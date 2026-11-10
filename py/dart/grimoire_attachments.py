"""Server-owned reference attachments. Uploaded files are never executed."""
import base64
import io
import json
import re
import uuid
import zipfile
from pathlib import Path
from xml.etree import ElementTree

MAX_BYTES = 16 * 1024 * 1024
MAX_FILES = 6
MAX_TEXT = 24000
TEXT_TYPES = {'.txt', '.md', '.markdown', '.json', '.csv', '.tsv', '.yaml', '.yml', '.toml',
              '.log', '.py', '.js', '.ts', '.html', '.css', '.xml', '.ini', '.sql', '.rst'}
IMAGE_TYPES = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp', '.tif', '.tiff'}


def attachment_root():
    import folder_paths
    root = Path(folder_paths.get_user_directory()) / 'prompt_mage' / 'grimoire_attachments'
    root.mkdir(parents=True, exist_ok=True)
    return root


def attachment_path(identifier):
    if not isinstance(identifier, str) or not re.fullmatch(r'[a-f0-9]{32}', identifier):
        raise ValueError('Invalid attachment ID. Attach the file again.')
    return attachment_root() / (identifier + '.json')


def load_attachment(identifier):
    path = attachment_path(identifier)
    if not path.is_file() or path.stat().st_size > 2 * 1024 * 1024:
        raise ValueError('Attachment is unavailable on this server. Attach the file again.')
    return json.loads(path.read_text(encoding='utf-8'))


def public_attachment(value):
    return {k: value[k] for k in ('id', 'name', 'kind', 'size', 'truncated', 'preview', 'excerpt') if k in value}


def parse_attachment_ids(raw):
    try:
        identifiers = json.loads(raw or '[]')
    except (TypeError, ValueError):
        raise ValueError('Invalid attachments list. Attach the files again.') from None
    if not isinstance(identifiers, list) or len(identifiers) > MAX_FILES:
        raise ValueError('Attach up to six files per message.')
    for identifier in identifiers:
        if not isinstance(identifier, str) or not re.fullmatch(r'[a-f0-9]{32}', identifier):
            raise ValueError('Invalid attachment ID.')
    return list(dict.fromkeys(identifiers))


def document_text(raw, extension):
    if extension == '.pdf':
        try:
            from pypdf import PdfReader
        except ImportError:
            raise ValueError('PDF support needs pypdf. Install Prompt Mage requirements and restart ComfyUI.') from None
        reader = PdfReader(io.BytesIO(raw))
        if reader.is_encrypted:
            raise ValueError('Use an unencrypted PDF, or attach its text instead.')
        chunks = []
        for page in reader.pages[:16]:
            chunks.append(page.extract_text() or '')
            if sum(map(len, chunks)) > MAX_TEXT:
                break
        text = '\n\n'.join(chunks)
        if not text.strip():
            raise ValueError('This PDF has no readable text. For scanned pages or diagrams, attach page images instead.')
        return text, len(reader.pages) > len(chunks)
    if extension == '.docx':
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            if sum(info.file_size for info in archive.infolist()) > 8 * 1024 * 1024:
                raise ValueError('DOCX expanded content exceeds 8 MB.')
            tree = ElementTree.fromstring(archive.read('word/document.xml'))
        ns = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
        return '\n'.join(''.join(t.text or '' for t in p.iter(ns+'t')) for p in tree.iter(ns+'p')), False
    if b'\0' in raw[:4096] and not raw.startswith((b'\xff\xfe', b'\xfe\xff')):
        raise ValueError('This looks like a binary file. Attach a supported text file or image.')
    try:
        encoding = 'utf-16' if raw.startswith((b'\xff\xfe', b'\xfe\xff')) else 'utf-8-sig'
        return raw.decode(encoding), False
    except UnicodeError:
        raise ValueError('Text attachments must use UTF-8 or UTF-16 encoding.') from None


def save_attachment(filename, raw):
    if not raw or len(raw) > MAX_BYTES:
        raise ValueError('Choose a nonempty file under 16 MB.')
    name = Path(str(filename).replace('\\', '/')).name[:180]
    extension = Path(name).suffix.lower()
    if extension not in TEXT_TYPES | IMAGE_TYPES | {'.pdf', '.docx'}:
        raise ValueError('Supported: images, text/code, Markdown, JSON, CSV, text-based PDF and DOCX.')
    identifier = uuid.uuid4().hex
    value = dict(id=identifier, name=name, size=len(raw), truncated=False)
    if extension in IMAGE_TYPES:
        from PIL import Image, ImageOps
        with Image.open(io.BytesIO(raw)) as opened:
            if opened.width * opened.height > 24_000_000:
                raise ValueError('Image exceeds 24 megapixels. Resize it before attaching.')
            image = ImageOps.exif_transpose(opened).convert('RGB')
            image.thumbnail((1536, 1536), Image.Resampling.LANCZOS)
            image.save(attachment_root() / (identifier + '.png'), format='PNG')
            image.thumbnail((192, 192), Image.Resampling.LANCZOS)
            stream = io.BytesIO(); image.save(stream, format='PNG')
        value.update(kind='image', preview='data:image/png;base64,' + base64.b64encode(stream.getvalue()).decode())
    else:
        text, truncated = document_text(raw, extension)
        if not text.strip():
            raise ValueError('This file contains no readable text.')
        value.update(kind='text', text=text[:MAX_TEXT], excerpt=text[:600], truncated=truncated or len(text) > MAX_TEXT)
    path = attachment_path(identifier)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')
    temporary.replace(path)
    return public_attachment(value)


def attachment_image(identifier):
    value = load_attachment(identifier)
    if value['kind'] != 'image':
        raise ValueError('Attachment is not an image.')
    import numpy as np
    import torch
    from PIL import Image
    with Image.open(attachment_root() / (identifier + '.png')) as image:
        return torch.from_numpy(np.array(image.convert('RGB')).astype('float32') / 255).unsqueeze(0)
