"""Verify that both actual WebUI chat models use Windows tools to inspect F:."""
import json, pathlib, time, uuid, requests
s=requests.Session(); base='http://open-webui:8080'
r=s.post(base+'/api/v1/auths/signin',json={'email':'admin@localhost','password':'admin'},timeout=30);r.raise_for_status()
s.headers['Authorization']='Bearer '+r.json()['token']
report={'started':time.time(),'passed':False,'models':{}}
try:
    for model in ('local-dolphin:24b-32k','local-qwen:27b-32k'):
        prompt='List the immediate folders in F:\\ using list_windows_directory. Report the actual returned names. Do not give me code to run.'
        mid=str(uuid.uuid4());uid=str(uuid.uuid4());start=time.monotonic()
        body={'model':model,'messages':[{'role':'user','content':prompt}],'stream':True,'id':mid,'parent_id':None,'session_id':'host-capability-verifier','user_message':{'id':uid,'parentId':None,'role':'user','content':prompt,'timestamp':int(time.time())},'tool_ids':['server:windows'],'features':{},'params':{'temperature':0,'num_predict':256,'function_calling':'native' if 'qwen' in model else 'legacy'}}
        if 'qwen' in model:body['params']['think']=False
        r=s.post(base+'/api/chat/completions',json=body,timeout=900);r.raise_for_status();chat_id=r.json()['chat_id']
        while time.monotonic()-start<900:
            r=s.get(base+'/api/v1/chats/'+chat_id,timeout=30);r.raise_for_status()
            message=r.json()['chat']['history']['messages'].get(mid,{})
            if message.get('error'):raise RuntimeError(str(message['error']))
            if message.get('done'):break
            time.sleep(2)
        else:raise TimeoutError(model)
        text=message.get('content','');serialized=json.dumps(message)
        passed=all(x in text.casefold() for x in ('backup','study')) and 'list_windows_directory' in serialized
        report['models'][model]={'passed':passed,'chat_id':chat_id,'seconds':time.monotonic()-start,'answer':text,'message':message}
        print(model,passed,text[:200],flush=True)
        if not passed:raise AssertionError('Host tool result was not verified')
    report['passed']=True
finally:
    report['finished']=time.time()
    pathlib.Path('/state/host-chat-verification.json').write_text(json.dumps(report,indent=2))
