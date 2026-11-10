"""Gemini GenerateContent text/vision adapter with isolated persistent credentials."""
import json,os
from types import SimpleNamespace
from urllib.request import Request,build_opener
from urllib.error import HTTPError,URLError
from .credentials import stored_key,store_key
from .openai_assistant import OpenAIEncoder,OpenAIRequestError,NoRedirect,image_data_url

MODELS={'Gemini 3.8 Flash · Recommended · Text + images':'gemini-3.8-flash',
        'Gemini 3.5 Flash-Lite · Budget · Text + images':'gemini-3.5-flash-lite',
        'Gemini 4 Argon · Higher cost · Text + images':'gemini-4-argon'}
DEFAULT_MODEL=next(iter(MODELS))
_session_key=''

def resolve_key(name='GEMINI_API_KEY'):
    return (_session_key or stored_key('gemini') or os.environ.get(name,'') or os.environ.get('GOOGLE_API_KEY','')).strip()

def key_status():
    saved=bool(stored_key('gemini'));environment=bool(os.environ.get('GEMINI_API_KEY','') or os.environ.get('GOOGLE_API_KEY',''))
    return dict(configured=bool(_session_key) or saved or environment,saved_configured=saved,session_configured=bool(_session_key),environment_configured=environment)

def set_persistent_key(key):
    global _session_key
    if not isinstance(key,str) or key and (not 20<=len(key)<=512 or any(c.isspace() for c in key)):raise ValueError('Enter a valid Gemini API key.')
    store_key('gemini',key);_session_key=key

class GeminiEncoder(OpenAIEncoder):
    def __init__(self,model=DEFAULT_MODEL,key_env='GEMINI_API_KEY',timeout=180):
        if model not in MODELS:raise ValueError('Choose a Gemini model from the dropdown.')
        if not resolve_key():raise ValueError('Add your Gemini API key in the Foundry key panel.')
        if not 10<=timeout<=600:raise ValueError('Gemini timeout must be 10–600 seconds.')
        self.model,self.key_env,self.timeout,self.calls=MODELS[model],key_env,timeout,[]
    def execute(self,prompt,system_prompt='',max_length=4096,thinking=False,image=None,**unused):
        if not 128<=max_length<=16384:raise ValueError('API token limit must be 128–16384.')
        parts=[{'text':prompt}]
        if image is not None:
            for reference in image if isinstance(image,(tuple,list)) else [image]:
                parts.append({'inlineData':{'mimeType':'image/png','data':image_data_url(reference).split(',',1)[1]}})
        payload={'systemInstruction':{'parts':[{'text':system_prompt}]},'contents':[{'role':'user','parts':parts}],
                 'generationConfig':{'maxOutputTokens':max_length,'thinkingConfig':{'thinkingLevel':'HIGH' if thinking else 'LOW'}}}
        key=resolve_key()
        if not key:raise OpenAIRequestError('The Gemini key was removed. Add it in the key panel.')
        request=Request('https://generativelanguage.googleapis.com/v1beta/models/'+self.model+':generateContent',data=json.dumps(payload).encode(),headers={'x-goog-api-key':key,'Content-Type':'application/json'})
        try:
            with build_opener(NoRedirect()).open(request,timeout=self.timeout) as response:raw=response.read(8*1024*1024+1)
            if len(raw)>8*1024*1024:raise OpenAIRequestError('Gemini response exceeded the supported size.')
            value=json.loads(raw)
        except HTTPError as e:
            raise OpenAIRequestError('Gemini HTTP '+str(e.code)+': '+{400:'Check model/request parameters.',401:'Invalid key.',403:'Key or project lacks access.',404:'Model unavailable.',429:'Rate limit or billing quota exceeded.'}.get(e.code,'Provider request failed.')+' No automatic retry was made.') from None
        except (URLError,TimeoutError):raise OpenAIRequestError('Gemini connection timed out. It may still be billable; no automatic retry was made.') from None
        except ValueError:raise OpenAIRequestError('Gemini returned an invalid response.') from None
        if not isinstance(value,dict):raise OpenAIRequestError('Gemini returned an invalid response object.')
        candidate=next(iter(value.get('candidates',[])),{})
        if not isinstance(candidate,dict):raise OpenAIRequestError('Gemini returned an invalid candidate.')
        if candidate.get('finishReason')!='STOP':raise OpenAIRequestError('Gemini returned no complete answer ('+str(candidate.get('finishReason',value.get('promptFeedback',{}).get('blockReason','no candidate')))+'). No automatic retry was made.')
        text='\n'.join(p['text'] for p in candidate.get('content',{}).get('parts',[]) if isinstance(p.get('text'),str) and not p.get('thought')).strip()
        if not text:raise OpenAIRequestError('Gemini returned no usable text.')
        usage=value.get('usageMetadata',{});call=dict(model=self.model,input_tokens=usage.get('promptTokenCount',0),output_tokens=usage.get('candidatesTokenCount',0),reasoning_tokens=usage.get('thoughtsTokenCount',0),status='completed')
        self.calls.append(call);return SimpleNamespace(args=[text],api_usage=call)
