import json
from .base import BaseNode
from ..dart import foundry as store
from ..dart import foundry_ai as ai
from ..dart.style_presets import STYLE_OPTIONS


def ui(value,result):
    return {'ui':{'foundry':[store.public(value)]},'result':result}


class PromptMageFoundry(BaseNode):
    CATEGORY='Prompt Mage/Experimental'
    DESCRIPTION='Approve a plan once; Foundry renders, reviews against an adjustable passing score (recommended 80), retries and advances automatically on the server. Local Qwen, DeepSeek, OpenAI or Gemini. Style presets, appearance and outfit/image references. Separate records; never changes Grimoire or Spell Scroll. Use panel buttons, not global Run.'
    FUNCTION='read';OUTPUT_NODE=False
    RETURN_TYPES=('STRING','INT','INT','INT','STRING','STRING','STRING','STRING')
    RETURN_NAMES=('prompt','width','height','seed','run_id','attempt_id','filename_prefix','report')

    @classmethod
    def INPUT_TYPES(cls):
        return {'required':{
            'run_id':('STRING',{'default':'','tooltip':'Managed by the Foundry panel. Persistent run records live on this ComfyUI server.'}),
            'conversation_id':('STRING',{'default':'','tooltip':'Optional saved Grimoire chat. Its saved provider/model/style settings and recent project context are copied into the run. API keys remain server-side.'}),
            'template_id':('STRING',{'default':'single'}),
            'brief':('STRING',{'default':store.BUILTINS['single']['brief'],'multiline':True}),
            'shared_rules':('STRING',{'default':store.BUILTINS['single']['shared_rules'],'multiline':True}),
            'review_rules':('STRING',{'default':store.BUILTINS['single']['review_rules'],'multiline':True}),
            'shot_count':('INT',{'default':1,'min':1,'max':24}),
            'max_attempts':('INT',{'default':3,'min':1,'max':10}),
            'max_renders':('INT',{'default':3,'min':1,'max':100}),
            'max_calls':('INT',{'default':8,'min':1,'max':100}),
            'attempt_id':('STRING',{'default':'','tooltip':'Managed by Render and review; prevents cached/duplicate attempts.'}),
        },'optional':{
            'assistant_profile':(list(store.ASSISTANTS),{'default':store.ASSISTANTS[0],'tooltip':'Select Local Qwen, DeepSeek Flash, OpenAI or Gemini explicitly. Each API provider has its own saved key. API charges apply; high-cost choices are labelled.'}),
            'width':('INT',{'forceInput':True,'default':1024}),
            'height':('INT',{'forceInput':True,'default':1024}),
            'clip':('CLIP',{'tooltip':'Shared native assistant encoder for Local Qwen. API runs skip this dependency.'}),
            'appearance':('ATELIER_APPEARANCE',{'tooltip':'Copied into a new plan. Enable selected replacements before previewing; approved runs freeze this recipe.'}),
            'image':('IMAGE',{'tooltip':'Optional single planning connection (first image of a batch). Use the numbered drag-and-drop gallery for multiple references, up to 12 total.'}),
            'style_preset':(STYLE_OPTIONS,{'default':'Photo · Bright lifestyle'}),
            'style_notes':('STRING',{'default':'','multiline':True}),
            'run_mode':(['Automatic','Manual'],{'default':'Automatic'}),
            'review_tolerance':(['Relaxed','Balanced','Strict'],{'default':'Balanced'}),
            'reference_instructions':('STRING',{'default':'Borrow only the requested outfit or objects. Keep character identity from Appearance Overrides.','multiline':True}),
            'attachments':('STRING',{'default':'[]'}),
            'reference_roles':('STRING',{'default':'{}'}),
            'physical_tolerance':(['Relaxed','Balanced','Strict'],{'default':'Balanced','tooltip':'Independent of prompt-match tolerance. Balanced checks physically coherent anatomy, support, garments and integration; Strict rejects smaller ambiguities. Major defects always block.'}),
            'passing_score':('INT',{'default':80,'min':50,'max':100,'tooltip':'Recommended 80/100 overall: 40% prompt match, 25% usability, 35% physical inspection. First passing image advances immediately. Major defects and missing must-haves still block.'}),
            'failure_policy':(['Skip frame and continue','Pause for review'],{'default':'Skip frame and continue','tooltip':'Automatic mode: if no try passes, record the missing frame and continue, or pause for your review. Rejected images never enter the accepted folder.'}),
            'production_brief':('MAGE_PRODUCTION_BRIEF',{'lazy':True,'tooltip':'Connect Grimoire.production_brief. Send a brief explicitly in Grimoire to fill this new plan. Chatting and rendering never refresh it automatically.'}),
            'brief_id':('STRING',{'default':'','tooltip':'Managed by explicit Grimoire brief import. Approved plans freeze the imported snapshot.'}),
            'output_folder':('STRING',{'default':'','tooltip':'Optional collection folder name inside ComfyUI output/PromptMage-Foundry. Empty uses the AI project title. Accepted images are collected in its accepted subfolder.'}),
        }}

    def check_lazy_status(self,**kwargs):return []

    @classmethod
    def IS_CHANGED(cls,**kwargs):return float('nan')

    def read(self,run_id='',attempt_id='',width=1024,height=1024,clip=None,**kwargs):
        # A normal ComfyUI Run must not create a paid request or reuse a stale attempt.
        # The panel reserves explicit attempts; idle workflow execution stops downstream.
        notice='Start Foundry with Preview plan, then Approve & start sequence. ComfyUI Run does not create a plan.'
        with store.LOCK:
            if run_id and attempt_id:
                try:
                    value=store.read(run_id)
                    attempt=store.attempt_for(value,attempt_id)
                except ValueError:
                    notice='This workflow references a run or attempt unavailable on this server. Open a saved run or choose New plan, then Preview plan.'
                else:
                    if value['status']=='rendering' and attempt['status']=='reserved':notice=None
                    else:notice='No fresh render attempt is reserved. Use the Foundry panel to approve, resume or render the next frame; ComfyUI Run does not start another attempt.'
            elif run_id:
                notice='Use the Foundry panel to approve the previewed plan or open a saved run. ComfyUI Run does not reserve a render attempt.'
        if notice:
            from comfy_execution.graph import ExecutionBlocker
            return {'ui':{'foundry_notice':[notice]},'result':tuple(ExecutionBlocker(None) for _ in self.RETURN_TYPES)}
        prompt,seed=ai.compose(run_id,attempt_id,width,height,clip)
        with store.LOCK:value=store.read(run_id)
        prefix=store.output_prefix(value,attempt_id)
        return prompt,width,height,seed,run_id,attempt_id,prefix,json.dumps(store.public(value),ensure_ascii=False)


class PromptMageFoundryPlan(PromptMageFoundry):
    OUTPUT_NODE=True;DEPRECATED=True;CATEGORY='Prompt Mage/Internal';FUNCTION='prepare'

    @classmethod
    def INPUT_TYPES(cls):
        inputs=super().INPUT_TYPES();inputs['hidden']={'extra_pnginfo':'EXTRA_PNGINFO','unique_id':'UNIQUE_ID'};return inputs

    def prepare(self,run_id,conversation_id='',template_id='single',brief='',shared_rules='',review_rules='',shot_count=1,
                max_attempts=3,max_renders=3,max_calls=8,width=1024,height=1024,clip=None,appearance=None,assistant_profile=store.ASSISTANTS[0],style_preset='Photo · Bright lifestyle',style_notes='',run_mode='Automatic',review_tolerance='Balanced',reference_instructions='',attachments='[]',reference_roles='{}',output_folder='',physical_tolerance='Balanced',passing_score=80,failure_policy='Skip frame and continue',brief_id='',**kwargs):
        from ..dart.foundry_runner import assert_can_plan
        assert_can_plan((kwargs.get('extra_pnginfo') or {}).get('workflow'),kwargs.get('unique_id'))
        imported=None
        if brief_id:
            from ..dart.production_brief import read
            imported=read(brief_id)
            if appearance is None:appearance=imported.get('appearance')
        with store.LOCK:value=store.create(run_id,conversation_id,template_id,brief,shared_rules,review_rules,shot_count,width,height,max_attempts,max_renders,max_calls,appearance,assistant_profile,style_preset,style_notes,review_tolerance,run_mode,output_folder,physical_tolerance,passing_score,failure_policy)
        if imported:
            value['production_brief_source']={k:imported[k] for k in ('id','conversation_id','title','created')};store.write(value)
        images=[(name,kwargs[name]) for name in ('image',*[f'image_{i}' for i in range(2,7)]) if kwargs.get(name) is not None]
        value=ai.plan(value,clip,images,attachments,reference_instructions,reference_roles)
        from comfy_execution.graph import ExecutionBlocker
        return ui(value,tuple(ExecutionBlocker(None) for _ in self.RETURN_TYPES))


class PromptMageFoundryReviewSaved(PromptMageFoundry):
    OUTPUT_NODE=True;DEPRECATED=True;CATEGORY='Prompt Mage/Internal';FUNCTION='review_saved'

    def review_saved(self,run_id,attempt_id,clip=None,**kwargs):
        value=ai.review(run_id,attempt_id,clip=clip)
        from comfy_execution.graph import ExecutionBlocker
        return ui(value,tuple(ExecutionBlocker(None) for _ in self.RETURN_TYPES))


class PromptMageFoundryReviewOutput(BaseNode):
    CATEGORY='Prompt Mage/Experimental';FUNCTION='inspect';OUTPUT_NODE=True
    DESCRIPTION='Archives and reviews the final actual image using the frozen assistant/style and tolerance. In Automatic mode the server controller accepts suitable frames, retries or advances. This node itself never waits on a nested queue.'
    RETURN_TYPES=('IMAGE','STRING');RETURN_NAMES=('image','review')

    @classmethod
    def INPUT_TYPES(cls):
        return {'required':{'image':('IMAGE',),'run_id':('STRING',{'forceInput':True}),'attempt_id':('STRING',{'forceInput':True})},
                'optional':{'clip':('CLIP',{'tooltip':'The same native generation-capable encoder used by Foundry for Local Qwen.'})}}

    @classmethod
    def IS_CHANGED(cls,**kwargs):return float('nan')

    def inspect(self,image,run_id,attempt_id,clip=None):
        value=ai.review(run_id,attempt_id,image,clip)
        attempt=store.attempt_for(value,attempt_id)
        return ui(value,(image,json.dumps(attempt.get('review'),ensure_ascii=False,indent=2)))
