"""Measure actual hardware/context performance; keep a resumable report."""
import json, pathlib, sys, time, urllib.request
ROOT=pathlib.Path(__file__).resolve().parent.parent
URL='http://127.0.0.1:11434'
def call(path,body=None):
    request=urllib.request.Request(URL+path,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=900) as response: return json.load(response)
report_path=ROOT/'logs/benchmark.json'
report=json.loads(report_path.read_text()) if '--extend' in sys.argv and report_path.exists() else {'timestamp':time.time(),'results':[]}
for model in ('local-qwen:27b','local-dolphin:24b'):
    for context in ((8192,) if '--extend' in sys.argv else (4096,16384,32768)):
        body={'model':model,'messages':[{'role':'user','content':'Write a Python function that computes the moving average of a list for a specified window size. Include validation and a short example.'}],'stream':False,'options':{'temperature':0,'num_ctx':context,'num_predict':96,'num_thread':8}}
        if 'qwen' in model: body['think']=False
        begin=time.monotonic()
        try:
            result=call('/api/chat',body)
            assert result['message']['content'].strip()
            row={'model':model,'context':context,'seconds':time.monotonic()-begin,'tokens_per_second':result['eval_count']/(result['eval_duration']/1e9),'prefill_tokens_per_second':result['prompt_eval_count']/(result['prompt_eval_duration']/1e9),'load_seconds':result['load_duration']/1e9,'memory':call('/api/ps')['models'],'answer':result['message']['content']}
        except Exception as error: row={'model':model,'context':context,'error':str(error)}
        report['results'].append(row)
        (ROOT/'logs/benchmark.json').write_text(json.dumps(report,indent=2))
        print(json.dumps({k:v for k,v in row.items() if k not in ('answer','memory')}),flush=True)
