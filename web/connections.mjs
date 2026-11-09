const prefix = "DanbooruTagsTransformer";
const node = (name, slot) => ({ type: prefix + name, slot });
const preview = { type: "PreviewAny", slot: "source" };
const encode = { type: "CLIPTextEncode", slot: "text" };
const composers = (slot) => [node("ComposePromptV3", slot)];
const generators = (slot) => [node("Generate", slot), node("GenerateAdvanced", slot)];

export function connectionsFor(type, name, slotType, isOutput) {
    if (type===prefix+'Grimoire') {
        if (!isOutput && ['width','height'].includes(name)) return [node('Resolution',name)];
        if (!isOutput && name==='appearance') return [node('AppearanceOverrides',0)];
        if (!isOutput && name==='image') return [{type:'LoadImage',slot:0},node('ImageBatchUpload',0)];
        if (!isOutput && name==='clip') return [{type:'CLIPLoader',slot:0}];
        return isOutput ? [encode,preview] : [];
    }
    if (!isOutput && name === 'filters' && type?.startsWith(prefix)) return [node('TagFilters',0)];
    if (type === prefix+'TagFilters') {
        if (isOutput && name === 'filters') return [node('Generate','filters'),node('ArchmageBeta','filters')];
        return isOutput ? [preview] : [];
    }
    if (type === prefix + 'ArchmageBeta' && !isOutput && name === 'source_tags')
        return [node('Generate',0),node('Decode',0),node('DecodeBySplitedParts',4)];
    if ([prefix+'Generate',prefix+'Decode',prefix+'DecodeBySplitedParts'].includes(type) && isOutput && slotType === 'STRING')
        return [node('ArchmageBeta','source_tags'),node('DescribeImage','source_tags'),encode,preview];
    if (type === prefix + 'Resolution' && isOutput && ['width', 'height'].includes(name))
        return [node('ArchmageBeta',name), {type:'EmptyFlux2LatentImage',slot:name}, {type:'EmptySD3LatentImage',slot:name}];
    if (type === prefix + 'ArchmageBeta' && !isOutput && ['width', 'height'].includes(name))
        return [node('Resolution',name)];
    if (type === prefix + 'ArchmageBeta' && isOutput) {
        if (name === 'width' || name === 'height') return [{type:'EmptySD3LatentImage',slot:name},{type:'EmptyLatentImage',slot:name},preview];
        if (name === 'image') return [{type:'PreviewImage',slot:'images'}];
        if (name === 'description') return [node('TagComposer','idea'),encode,preview];
        if (name === 'prompt' || name === 'moss_json') return [encode,preview];
        return [preview];
    }
    if (type === prefix + 'TagComposer' && isOutput) return name === 'tags' || name === 'prompt' ? [encode,preview] : [preview];
    if (type === prefix + 'SceneComposer' && isOutput) return name === 'prompt' ? [encode,node('TagComposer','idea'),preview] : [preview];
    if (!type?.startsWith(prefix)) return [];
    if (!isOutput) {
        if ([prefix + 'ArchmageBeta',prefix + 'ImageToText'].includes(type) && name === "image") return [{type:"LoadImage",slot:0},node("ImageBatchUpload",0),node("ImageBatchSelector",0)];
        if (name === "appearance" && [prefix + "ImageToText", prefix + "DescribeImage",prefix+'TagComposer',prefix+'SceneComposer',prefix+'ArchmageBeta'].includes(type)) return [node("AppearanceOverrides", 0)];
        if (name === "image") return [{ type: "LoadImage", slot: 0 }];
        if (type === prefix + "DescribeImage" && name === "description") return [node("ImageToText", 0)];
        if (name === "model") return [node("LoaderV3", 0)];
        if (name === "tokenizer") return [node("LoaderV3", 1)];
        if (name === "setting") return [node("GenerationConfig", 0)];
        if (name === "token_ids") return [node("GenerateAdvanced", 0)];
        if (name === "clip") return [{ type: "CLIPLoader", slot: 0 }];
        if (type === prefix + "DescribeImage" && name === "source_tags") return [node("Generate", 0), node("Decode", 0), node("DecodeBySplitedParts", 4)];
        if (name === "prompt" && /Generate/.test(type)) return composers(0);
        const describeSlots = { general: 1, copyright: 2, character: 3 };
        if (name in describeSlots) return [node("DescribeImage", describeSlots[name])];
        return [];
    }
    if ([prefix + "ImageBatchSelector", prefix + "ImageBatchUpload"].includes(type)) {
        if (name === "image") return [node('ArchmageBeta','image'), node("ImageToText","image"), {type:"PreviewImage",slot:"images"}];
        if (name === "filename") return [node("ArchmageBeta","source_name"),node("ImageToText","source_name"),preview];
        return [preview];
    }
    if (slotType === "ATELIER_APPEARANCE") return [node('ArchmageBeta','appearance'),node('TagComposer','appearance'),node("ImageToText", "appearance"), node("DescribeImage", "appearance"),node('SceneComposer','appearance')];
    if (type === prefix + "AppearanceOverrides") return [preview];
    if (slotType === "DART_MODEL") return generators("model");
    if (slotType === "DART_TOKENIZER") return [
        ...generators("tokenizer"), node("Decode", "tokenizer"),
        node("DecodeBySplitedParts", "tokenizer"), node("BanTagsFromRegex", "tokenizer"),
    ];
    if (slotType === "DART SETTING") return generators("setting");
    if (slotType === "DART_TOKEN_IDS") return [
        node("Decode", "token_ids"), node("DecodeBySplitedParts", "token_ids"),
        node("RearrangedByAnimagine", "token_ids"), node("RemoveTagToken", "token_ids"),
    ];
    if (type === prefix + "DescribeImage") {
        if (name === "status" || name === "report") return [preview];
        if (name === "general_tags") return [...composers("general"), preview];
        if (name === "copyright" || name === "character") return [...composers(name), preview];
        if (name === "scene_json") return [preview];
        return [encode, preview];
    }
    if (type === prefix + "ImageToText") {
        if (name === "status" || name === "report") return [preview];
        if (name === "width" || name === "height") return [
            { type: "EmptySD3LatentImage", slot: name }, { type: "EmptyLatentImage", slot: name }, preview,
        ];
        if (name === "image") return [{ type: "PreviewImage", slot: "images" }];
        return [node("DescribeImage", "description"), encode, preview];
    }
    if (/ComposePrompt/.test(type)) return [...generators("prompt"), preview];
    if (/BanTagsFromRegex/.test(type)) return [...generators("ban_tags"), preview];
    if (slotType === "STRING") return [node("DescribeImage", "source_tags"), encode, preview];
    return [];
}

export function resolveSlot(slots, value) {
    const index = typeof value === "number" ? value : slots.findIndex(
        (slot) => slot === value || slot.name === (typeof value === "string" ? value : value?.name),
    );
    return { index, slot: slots[index] };
}
