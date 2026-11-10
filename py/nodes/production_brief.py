from .grimoire import PromptMageGrimoire
from ..dart.production_brief import compile_brief
from ..dart.foundry_ai import encoder_for
from ..dart.openai_assistant import execute_generation
from ..dart.text_output import final_text

class PromptMageGrimoireBrief(PromptMageGrimoire):
    OUTPUT_NODE=True;DEPRECATED=True;CATEGORY='Prompt Mage/Internal';FUNCTION='publish_brief'
    def publish_brief(self,conversation_id,clip=None,appearance=None,image=None,**settings):
        config={k:settings[k] for k in ('assistant_backend','local_model','openai_model','deepseek_model','thinking','max_tokens') if k in settings}
        encoder=None
        def generate(system,prompt):
            nonlocal encoder
            if encoder is None:encoder=encoder_for(config,clip)
            from ..dart.memory import offload_after
            with offload_after(encoder,bool(settings.get('unload_after_generation',False)),release_on_error=False):
                result=execute_generation(encoder,prompt=prompt,system_prompt=system,max_length=min(8192,int(config.get('max_tokens',4096))),thinking=False,sampling_mode={'sampling_mode':'off'},mtp='off')
            return final_text(result,thinking=False)
        images=[v for v in (image,*[settings.get('image_'+str(i)) for i in range(2,7)]) if v is not None]
        brief=compile_brief(conversation_id,generate,appearance,images,settings)
        from comfy_execution.graph import ExecutionBlocker
        return {'ui':{'production_brief':[brief]},'result':tuple(ExecutionBlocker(None) for _ in range(4))+({'conversation_id':conversation_id,'id':brief['id']},)}
