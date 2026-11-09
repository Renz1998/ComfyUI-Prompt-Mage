import json
from .base import BaseNode
from ..dart.spell_scroll import active_scroll, prompt_from_scroll, LOCK


class PromptMageSpellScroll(BaseNode):
    CATEGORY='Prompt Mage/Assistants'
    DESCRIPTION='Reads only the prompt explicitly applied from Grimoire. No assistant model, API key or chat calls. Run repeatedly to generate images from the same snapshot. Choose the destination by this scroll ID in Grimoire.'
    FUNCTION='read'
    OUTPUT_NODE=False
    RETURN_TYPES=('STRING','STRING')
    RETURN_NAMES=('prompt','report')

    @classmethod
    def INPUT_TYPES(cls):
        return {'required':{'scroll_id':('STRING',{'default':'main-scroll','tooltip':'Independent saved prompt slot. Match the destination selected in Grimoire. Use a distinct ID for separate projects.'})},
                'optional':{'width':('INT',{'forceInput':True,'default':1024}), 'height':('INT',{'forceInput':True,'default':1024})}}

    @classmethod
    def IS_CHANGED(cls,**kwargs):return float('nan')

    def read(self,scroll_id='main-scroll',width=1024,height=1024):
        with LOCK:value=active_scroll(scroll_id)
        text=prompt_from_scroll(value,width,height)
        return text,json.dumps({k:v for k,v in value.items() if k!='text'},ensure_ascii=False,indent=2)
