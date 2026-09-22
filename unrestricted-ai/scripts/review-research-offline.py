"""Exercise only the extracted research function with fake search/crawl transports.

Does not import the application, start services, or make network requests.
"""
import ast
import json
from pathlib import Path
from types import SimpleNamespace

root = Path(__file__).resolve().parents[1]
tree = ast.parse((root / 'scripts/workspace_api.py').read_text(encoding='utf-8-sig'))
function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'research_web')
function.decorator_list = []


class Future:
    def __init__(self, fn, args):
        self.fn, self.args = fn, args

    def result(self):
        return self.fn(*self.args)


class Pool:
    def __init__(self, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def submit(self, fn, *args):
        return Future(fn, args)


def run(responses, queries, read_pages=3, reverse=False):
    reads = []

    def request(method, url, *, params, timeout):
        response = responses[params['q']]
        if isinstance(response, Exception):
            raise response
        return response

    def crawl(url):
        reads.append(url)
        return {'url': url, 'text': 'offline fixture'}

    scope = dict(ThreadPoolExecutor=Pool,
                 as_completed=lambda jobs: list(reversed(jobs)) if reverse else list(jobs),
                 request=request, crawl_page=crawl,
                 os=SimpleNamespace(environ={'SEARXNG_URL': 'offline://fixture'}))
    exec(compile(ast.Module(body=[function], type_ignores=[]), '<extracted-research>', 'exec'), scope)
    return scope['research_web'](queries, read_pages=read_pages), reads


def results(*urls):
    return {'results': [{'url': url, 'title': url} for url in urls]}


responses = {'alpha': results('https://a.test/1', 'https://a.test/2', 'https://c.test/1'),
             'beta': results('https://b.test/1', 'https://a.test/1')}
forward, reads = run(responses, ['alpha', 'beta'])
reverse, _ = run(responses, ['alpha', 'beta'], reverse=True)
assert forward == reverse, 'Network completion order changed research selection'
assert reads == ['https://a.test/1', 'https://b.test/1', 'https://c.test/1']
assert forward['sources'][0]['queries'] == ['alpha', 'beta']
single, reads = run({'alpha': responses['alpha']}, ['alpha'], read_pages=3)
assert len(reads) == 3 and len(set(reads)) == 3, 'Same-domain sources left budget unused'
partial, reads = run({'alpha': RuntimeError('offline timeout'), 'beta': responses['beta']}, ['alpha', 'beta'])
assert partial['sources'] and partial['failures'][0]['query'] == 'alpha'
empty, reads = run({'alpha': results()}, ['alpha'])
assert empty['sources'] == [] and reads == []
_, reads = run(responses, ['alpha', 'beta'], read_pages=0)
assert reads == [], 'Zero page budget still crawled'
report = {'mode': 'offline_extracted_function', 'passed': True,
          'checks': ['completion-order independence', 'query-balanced ordering',
                     'source query provenance', 'same-domain budget fallback',
                     'partial search failure', 'empty results', 'zero crawl budget'],
          'live_services_started': False, 'network_requests': 0}
(root / 'logs/research-offline-review.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report))
