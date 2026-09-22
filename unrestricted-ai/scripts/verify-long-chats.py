"""Exercise consecutive saved-chat turns, compaction, recall and tools in WebUI."""
import argparse, json, time, uuid, pathlib
import requests

BASE='http://open-webui:8080'
parser=argparse.ArgumentParser()
parser.add_argument('--model',choices=['local-dolphin:24b-32k','local-qwen:27b-32k'])
args=parser.parse_args()
s=requests.Session()
r=s.post(BASE+'/api/v1/auths/signin',json={'email':'admin@localhost','password':'admin'}); r.raise_for_status()
s.headers['Authorization']='Bearer '+r.json()['token']
report={'timestamp':time.time(),'models':{},'passed':False}

def call(method,path,body=None):
    r=s.request(method,BASE+path,json=body,timeout=900 if method=='POST' else 30); r.raise_for_status(); return r.json()

try:
    for model in ([args.model] if args.model else ('local-dolphin:24b-32k','local-qwen:27b-32k')):
        results={'turns':[]}; report['models'][model]=results
        chat_id=None; parent=None; messages=[]
        turns=[
            ('Remember this project fact for this conversation: our sentinel is COPPER-HERON-8621 and our preferred language is Python. Acknowledge briefly.',''),
            ('What is 17 multiplied by 23? Reply with the integer.','391'),
            ('What is our project sentinel?','COPPER-HERON-8621'),
            ('What programming language did I say we prefer?','Python'),
            ('Add the project decision: the output filename is project-result.txt. Repeat that filename.','project-result.txt'),
            ('What was the sentinel from my first message?','COPPER-HERON-8621'),
            ('What was the filename we chose?','project-result.txt'),
            ('Use execute_python to calculate 12 squared. Tell me its output.','144'),
            ('Restate our preferred programming language and sentinel.','COPPER-HERON-8621'),
            ('Use read_project_file to read workspace/retrieval-check.md. Tell me the verification phrase in that file.','SILVER-ORCHID-742'),
            ('After reading that file, what was our original project sentinel?','COPPER-HERON-8621'),
            ('Say which published model variant you are and who made it.','Huihui' if 'qwen' in model else 'Cognitive'),
        ]
        for index,(prompt,expected) in enumerate(turns):
            mid=str(uuid.uuid4()); uid=str(uuid.uuid4()); started=time.monotonic()
            messages.append({'role':'user','content':prompt})
            body={'model':model,'messages':messages,'stream':True,'id':mid,'parent_id':parent,
                  'session_id':'local-long-chat-verifier','user_message':{'id':uid,'parentId':parent,'role':'user','content':prompt,'timestamp':int(time.time())},
                  'tool_ids':['server:workspace'],'features':{'code_interpreter':True},
                  'params':{'temperature':0,'num_predict':192,'function_calling':'native' if 'qwen' in model else 'legacy',
                            'compact_token_threshold':600 if index>=4 else 18000}}
            if 'qwen' in model: body['params']['think']=False
            if chat_id: body['chat_id']=chat_id
            response=call('POST','/api/chat/completions',body)
            chat_id=response.get('chat_id',chat_id); results['chat_id']=chat_id
            deadline=time.monotonic()+900
            while time.monotonic()<deadline:
                chat=call('GET','/api/v1/chats/'+chat_id)
                message=chat['chat']['history']['messages'].get(mid,{})
                if message.get('error'): raise RuntimeError(str(message['error']))
                if message.get('done'): break
                time.sleep(2)
            else: raise TimeoutError('Saved chat turn did not finish')
            answer=message.get('content','')
            assert answer.strip(),f'{model} turn {index+1}: blank response'
            assert expected.casefold() in answer.casefold(),f'{model} turn {index+1}: expected {expected}: {answer}'
            if index==7: assert 'execute_python' in json.dumps(message),'Python tool was not actually used'
            summaries=[m['contextSummary'] for m in chat['chat']['history']['messages'].values() if m.get('contextSummary')]
            results['turns'].append({'number':index+1,'seconds':round(time.monotonic()-started,2),'answer':answer,'summary_checkpoints':len(summaries),'passed':True})
            results['compaction_test_threshold']=600
            messages.append({'role':'assistant','content':answer}); parent=mid
            print('PASS',model,'turn',index+1,'summaries',len(summaries),flush=True)
            pathlib.Path('/state/long-chat-verification.json').write_text(json.dumps(report,indent=2))
        assert summaries,'No persisted context-summary checkpoint was created'
        assert any('COPPER-HERON-8621' in summary for summary in summaries),'Compaction lost the sentinel'
        results['passed']=True
    report['passed']=True
except Exception as error:
    report['error']=str(error)
    raise
finally:
    report['completed_at']=time.time()
    pathlib.Path('/state/long-chat-verification.json').write_text(json.dumps(report,indent=2))
