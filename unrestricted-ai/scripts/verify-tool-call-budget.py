import json
import argparse
import os
import time
import uuid

import requests


BASE = os.environ.get('WEBUI_URL', 'http://open-webui:8080')


def wait_message(session, chat_id, message_id):
    deadline = time.monotonic() + 900
    while time.monotonic() < deadline:
        chat = session.get(f'{BASE}/api/v1/chats/{chat_id}', timeout=30)
        chat.raise_for_status()
        message = chat.json()['chat']['history']['messages'].get(message_id, {})
        if message.get('error') or message.get('done'):
            return message
        time.sleep(2)
    raise TimeoutError(f'timed out waiting for {message_id}')


def main(model):
    session = requests.Session()
    token = session.post(
        f'{BASE}/api/v1/auths/signin',
        json={'email': 'admin@localhost', 'password': 'admin'},
        timeout=30,
    ).json()['token']
    session.headers['Authorization'] = f'Bearer {token}'

    chat_id = None
    # About 24K simple tokens, plus the Open WebUI system/tool envelope, leaves
    # a long-chat continuation with almost no generation room in a 32K preset.
    retained = ('project-record alpha beta gamma delta epsilon zeta eta theta '
                'iota kappa lambda mu nu xi omicron pi rho sigma tau upsilon phi chi psi omega\n') * 864
    first_user = (
        'Treat the following as retained project data. Do not call a tool for this '
        'turn. Acknowledge with exactly READY after reading it.\n\n' + retained
    )
    first_mid = str(uuid.uuid4())
    first_uid = str(uuid.uuid4())
    first_body = {
        'model': model,
        'messages': [{'role': 'user', 'content': first_user}],
        'stream': True,
        'id': first_mid,
        'parent_id': None,
        'session_id': 'tool-call-budget-regression',
        'user_message': {'id': first_uid, 'parentId': None, 'role': 'user', 'content': first_user, 'timestamp': int(time.time())},
        'tool_ids': ['server:workspace'],
        'features': {'code_interpreter': True},
        'params': {'temperature': 0, 'num_predict': 64, 'function_calling': 'native' if 'qwen' in model else 'legacy', 'think': False, 'compact_token_threshold': 18000},
    }
    response = session.post(f'{BASE}/api/chat/completions', json=first_body, timeout=900)
    response.raise_for_status()
    chat_id = response.json()['chat_id']
    try:
        first = wait_message(session, chat_id, first_mid)
        if first.get('error'):
            raise RuntimeError(f'first turn failed: {first["error"]}')

        second_mid = str(uuid.uuid4())
        second_uid = str(uuid.uuid4())
        second_prompt = 'Use execute_python to calculate 12 squared. Tell me its output.'
        second_body = {
            'model': model,
            'messages': [
                {'role': 'user', 'content': first_user},
                {'role': 'assistant', 'content': first.get('content', '')},
                {'role': 'user', 'content': second_prompt},
            ],
            'stream': True,
            'id': second_mid,
            'parent_id': first_mid,
            'chat_id': chat_id,
            'session_id': 'tool-call-budget-regression',
            'user_message': {'id': second_uid, 'parentId': first_mid, 'role': 'user', 'content': second_prompt, 'timestamp': int(time.time())},
            'tool_ids': ['server:workspace'],
            'features': {'code_interpreter': True},
            'params': {'temperature': 0, 'num_predict': 768, 'function_calling': 'native' if 'qwen' in model else 'legacy', 'think': False, 'compact_token_threshold': 18000},
        }
        response = session.post(f'{BASE}/api/chat/completions', json=second_body, timeout=900)
        response.raise_for_status()
        second = wait_message(session, chat_id, second_mid)
        history = session.get(f'{BASE}/api/v1/chats/{chat_id}', timeout=30).json()['chat']['history']['messages']
        summary_count = sum(1 for message in history.values() if message.get('contextSummary'))
        print(json.dumps({
            'chat_id': chat_id,
            'first_usage': first.get('usage'),
            'second_usage': second.get('usage'),
            'second_error': second.get('error'),
            'second_content': second.get('content', ''),
            'second_output': second.get('output'),
            'context_summary_count': summary_count,
        }, ensure_ascii=False, indent=2))
        if second.get('error'):
            raise SystemExit(1)
        if '144' not in (second.get('content') or ''):
            raise SystemExit('second turn did not return 144')
        if not summary_count:
            raise SystemExit('oversized three-message branch was not compacted')
    finally:
        try:
            session.delete(f'{BASE}/api/v1/chats/{chat_id}', timeout=30)
        except requests.RequestException:
            pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Verify safe compaction before a long-chat tool call.')
    parser.add_argument('--model', choices=['local-qwen:27b-32k', 'local-dolphin:24b-32k'], default='local-qwen:27b-32k')
    main(parser.parse_args().model)
