"""Verify real saved-chat tool use with all configured default capability groups."""
import argparse
import json
import pathlib
import time
import uuid
import requests

parser=argparse.ArgumentParser()
parser.add_argument('--model',required=True,choices=['local-dolphin:24b-32k','local-qwen:27b-32k'])
parser.add_argument('--artifact-only',action='store_true')
parser.add_argument('--browser-only',action='store_true')
args=parser.parse_args()
base='http://open-webui:8080'
s=requests.Session()
def call(method,path,body=None):
    response=s.request(method,base+path,json=body,timeout=60)
    response.raise_for_status()
    return response.json()
s.headers['Authorization']='Bearer '+call('POST','/api/v1/auths/signin',{'email':'admin@localhost','password':'admin'})['token']
model=call('GET','/api/v1/models/model?id='+args.model)
groups=model['meta']['toolIds']
assert {'server:workspace','server:windows','server:browser','server:research'}<=set(groups)
report={'started':time.time(),'model':args.model,'groups':groups,'passed':False,'turns':[]}
messages=[]; chat_id=None; parent=None
try:
    steps=[
        ('Use run_windows_powershell to evaluate 19 * 23 on Windows. Report the actual returned result briefly.','437','run_windows_powershell'),
        ('Use read_windows_file to read F:\\backup\\UnrestrictedAi\\workspace\\direct-tool-live-check.txt. Repeat the exact marker in the file.','DIRECT-TOOLS-VERIFIED-5842','read_windows_file'),
    ]
    if args.artifact_only:
        steps=[('Use get_workspace_artifact for document-capability-check/check.pdf and give me its exact download_url.','http://localhost:8001/files/download?path=document-capability-check','get_workspace_artifact')]
    if args.browser_only:
        steps=[('Read the current page in my connected browser using call_browser_tool with tool browser_snapshot, arguments {}, existing_tabs true. Report its heading and source URL from the actual result. Do not use web search or navigate elsewhere.','Example Domains','call_browser_tool')]
    for prompt,expected,tool in steps:
        mid=str(uuid.uuid4()); start=time.monotonic()
        messages.append({'role':'user','content':prompt})
        body={'model':args.model,'messages':messages,'stream':True,'id':mid,'parent_id':parent,
              'session_id':'default-capability-verifier','tool_ids':groups,'features':{},
              'user_message':{'id':str(uuid.uuid4()),'parentId':parent,'role':'user','content':prompt,'timestamp':int(time.time())},
              'params':{'temperature':0,'num_predict':256,'function_calling':'native' if 'qwen' in args.model else 'legacy'}}
        if 'qwen' in args.model:body['params']['think']=False
        if chat_id:body['chat_id']=chat_id
        chat_id=call('POST','/api/chat/completions',body).get('chat_id',chat_id)
        report['chat_id']=chat_id
        while time.monotonic()-start<900:
            message=call('GET','/api/v1/chats/'+chat_id)['chat']['history']['messages'].get(mid,{})
            if message.get('error'):raise RuntimeError(str(message['error']))
            if message.get('done'):break
            time.sleep(2)
        else:raise TimeoutError('Default capability chat timed out')
        answer=message.get('content','')
        assert expected in answer and tool in json.dumps(message),(tool,answer)
        report['turns'].append({'tool':tool,'seconds':time.monotonic()-start,'answer':answer,'message':message})
        messages.append({'role':'assistant','content':answer}); parent=mid
        print('PASS',args.model,tool,flush=True)
    report['passed']=True
except Exception as error:
    report['error']=str(error)
    raise
finally:
    report['finished']=time.time()
    path=pathlib.Path('/state')/('default-capabilities-'+('qwen' if 'qwen' in args.model else 'dolphin')+('-artifact' if args.artifact_only else '-browser' if args.browser_only else '')+'.json')
    path.write_text(json.dumps(report,indent=2))
