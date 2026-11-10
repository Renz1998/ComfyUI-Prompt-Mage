from test_regressions import plugin
import io
import json
import sys
import tempfile
import unittest
import zipfile
from types import SimpleNamespace
from unittest.mock import patch, Mock
from PIL import Image
from dart_plugin.py.dart.grimoire_attachments import save_attachment, load_attachment, parse_attachment_ids, attachment_image, MAX_TEXT
from dart_plugin.py.dart.grimoire import memory_path, read_memory


class AttachmentTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.modules=patch.dict(sys.modules,{'folder_paths':SimpleNamespace(get_user_directory=lambda:self.temp.name,get_filename_list=lambda name:[]),
            'comfy_execution.graph':SimpleNamespace(ExecutionBlocker=lambda value:value)})
        self.modules.start()

    def tearDown(self):
        self.modules.stop();self.temp.cleanup()

    def image(self,name='outfit.png'):
        stream=io.BytesIO();Image.new('RGB',(32,48),'green').save(stream,format='PNG')
        return save_attachment(name,stream.getvalue())

    def test_stored_references_are_server_owned_and_bounded(self):
        value=save_attachment('../notes.md',b'Green cloak and brown leather boots.')
        self.assertEqual(value['name'],'notes.md')
        self.assertNotIn('text',value)
        self.assertIn('Green cloak',load_attachment(value['id'])['text'])
        with self.assertRaises(ValueError):load_attachment('../notes.md')
        with self.assertRaises(ValueError):parse_attachment_ids('["../../secret"]')
        with self.assertRaises(ValueError):parse_attachment_ids(json.dumps(['a'*32]*7))
        with self.assertRaises(ValueError):save_attachment('program.exe',b'not executable')
        long=save_attachment('long.txt',b'x'*(MAX_TEXT+100));self.assertTrue(long['truncated'])
        self.assertEqual(len(load_attachment(long['id'])['text']),MAX_TEXT)

    def test_image_and_docx_references(self):
        value=self.image();self.assertTrue(value['preview'].startswith('data:image/png;base64,'))
        self.assertEqual(tuple(attachment_image(value['id']).shape),(1,48,32,3))
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w') as archive:
            archive.writestr('word/document.xml','<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>A blue coat.</w:t></w:r></w:p></w:body></w:document>')
        value=save_attachment('outfit.docx',stream.getvalue());self.assertEqual(load_attachment(value['id'])['text'],'A blue coat.')

    def test_pdf_text_and_scanned_page_feedback(self):
        from pypdf import PdfWriter
        from pypdf.generic import DictionaryObject,NameObject,DecodedStreamObject
        writer=PdfWriter();page=writer.add_blank_page(width=300,height=300)
        blank=io.BytesIO();writer.write(blank)
        with self.assertRaisesRegex(ValueError,'no readable text'):save_attachment('scan.pdf',blank.getvalue())
        font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
        page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):writer._add_object(font)})})
        content=DecodedStreamObject();content.set_data(b'BT /F1 12 Tf 20 200 Td (A red cloak.) Tj ET');page[NameObject('/Contents')]=writer._add_object(content)
        stream=io.BytesIO();writer.write(stream);value=save_attachment('notes.pdf',stream.getvalue());self.assertIn('red cloak',load_attachment(value['id'])['text'])

    def test_local_images_are_captioned_and_text_is_remembered(self):
        image=self.image();text=save_attachment('notes.txt',b'Keep the leather boots.')
        node=plugin.NODE_CLASS_MAPPINGS['DanbooruTagsTransformerGrimoire']()
        execute=Mock(return_value=SimpleNamespace(args=['A traveler in a green cloak.']))
        with patch('dart_plugin.py.nodes.grimoire.load_local_clip',return_value='encoder'),patch('dart_plugin.py.nodes.grimoire.caption_image',return_value='A green cloak.') as caption,patch('dart_plugin.py.nodes.grimoire.execute_generation',execute):
            node.chat('attach-chat',action='Send',message='Use these',attachments=json.dumps([image['id'],text['id']]))
        self.assertEqual(caption.call_count,1);self.assertEqual(execute.call_count,1)
        self.assertIn('leather boots',execute.call_args.kwargs['prompt'])
        turn=read_memory(memory_path('attach-chat'))['turns'][0]
        self.assertEqual(turn['message'],'Use these');self.assertEqual(len(turn['attachments']),2)
        self.assertNotIn('preview',str(turn['attachments']))

    def test_api_images_use_one_call_and_followup_reuses_recent_refs(self):
        from dart_plugin.py.dart.openai_assistant import OpenAIEncoder
        image=self.image();second=self.image('boots.png')
        node=plugin.NODE_CLASS_MAPPINGS['DanbooruTagsTransformerGrimoire']()
        execute=Mock(return_value=SimpleNamespace(args=['A clear outfit reference.']))
        with patch.object(OpenAIEncoder,'__init__',return_value=None),patch('dart_plugin.py.nodes.grimoire.execute_generation',execute),patch('dart_plugin.py.nodes.grimoire.caption_image',side_effect=AssertionError('No extra caption API call')):
            with patch.object(OpenAIEncoder,'calls',[],create=True):
                node.chat('api-attach',action='Send',message='Compare',assistant_backend='OpenAI API',attachments=json.dumps([image['id'],second['id']]))
                self.assertEqual(len(execute.call_args.kwargs['image']),2)
                node.chat('api-attach',action='Send',message='What about the boots?',assistant_backend='OpenAI API')
                self.assertEqual(len(execute.call_args.kwargs['image']),2)
        self.assertEqual(execute.call_count,2)

    def test_multiple_graph_inputs_are_sent_in_one_api_call(self):
        import torch
        from dart_plugin.py.dart.openai_assistant import OpenAIEncoder
        node=plugin.NODE_CLASS_MAPPINGS['DanbooruTagsTransformerGrimoire']()
        self.assertTrue(all('image_'+str(i) in node.INPUT_TYPES()['optional'] for i in range(2,7)))
        execute=Mock(return_value=SimpleNamespace(args=['The two outfit references.']))
        with patch.object(OpenAIEncoder,'__init__',return_value=None),patch.object(OpenAIEncoder,'calls',[],create=True),patch('dart_plugin.py.nodes.grimoire.execute_generation',execute),patch('dart_plugin.py.nodes.grimoire.caption_image',side_effect=AssertionError('No extra paid caption stage')):
            node.chat('multi-input',action='Send',message='Compare the outfits',assistant_backend='OpenAI API',image=torch.zeros(1,16,16,3),image_2=torch.ones(1,16,16,3))
        self.assertEqual(execute.call_count,1)
        self.assertEqual(len(execute.call_args.kwargs['image']),2)
