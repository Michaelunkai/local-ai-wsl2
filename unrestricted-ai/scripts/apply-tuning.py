"""Choose largest tested context within 10% of fastest measured decoding."""
import json, pathlib, time, urllib.request
root=pathlib.Path(__file__).resolve().parent.parent
def call(path,body):
    r=urllib.request.Request('http://127.0.0.1:11434'+path,data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(r,timeout=300) as response: return json.load(response)
results=json.loads((root/'logs/benchmark.json').read_text())['results']
tuning={'timestamp':time.time(),'selection':'Largest tested context with at least 90% of the best measured tokens/sec','models':{}}
for model in ('local-qwen:27b','local-dolphin:24b'):
    rows=[r for r in results if r['model']==model and 'error' not in r]
    best=max(r['tokens_per_second'] for r in rows)
    selected=max((r for r in rows if r['tokens_per_second']>=best*.9),key=lambda r:r['context'])
    params={'temperature':.7,'top_p':.9,'repeat_penalty':1.1,'num_thread':8}
    for alias,context in ((model+'-32k',32768),(model,selected['context'])):
        response=call('/api/create',{'model':alias,'from':model,'parameters':dict(params,num_ctx=context),'stream':False})
        assert response.get('status')=='success',response
        show=call('/api/show',{'model':alias})
        name=('qwen' if 'qwen' in model else 'dolphin')+('-32k' if alias.endswith('-32k') else '')+'.Modelfile'
        (root/'modelfiles'/name).write_text(show['modelfile'])
    tuning['models'][model]={'num_ctx':selected['context'],'num_thread':8,'num_gpu':'Ollama automatic VRAM fit','tokens_per_second':selected['tokens_per_second'],'measured_vram_bytes':selected['memory'][0]['size_vram'],'extended_alias':model+'-32k'}
(root/'tuning.json').write_text(json.dumps(tuning,indent=2))
print(json.dumps(tuning,indent=2))
