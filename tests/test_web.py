import http.client
import json
import threading

import pytest

from mockr_coach.bank import load_bank
from mockr_coach.providers import MockProvider
from mockr_coach.web import create_server


@pytest.fixture
def app(tmp_path):
    server = create_server(tmp_path/'history.sqlite3',load_bank(),MockProvider(),'mock',0)
    thread = threading.Thread(target=server.serve_forever,daemon=True); thread.start()
    def request(method,path,payload=None,headers=None):
        connection=http.client.HTTPConnection('127.0.0.1',server.server_port)
        base={'Origin':f'http://127.0.0.1:{server.server_port}','Content-Type':'application/json','X-Mockr-Token':server.token}
        base.update(headers or {})
        connection.request(method,path,json.dumps(payload) if payload is not None else None,base)
        response=connection.getresponse(); raw=response.read(); connection.close()
        return response.status,raw,response.headers
    yield request
    server.shutdown(); server.server_close(); thread.join()


def test_page_and_private_bank(app):
    status,raw,headers=app('GET','/')
    assert status == 200 and b'mockr' in raw
    assert "default-src 'self'" in headers['Content-Security-Policy']
    status,raw,_=app('GET','/api/config')
    data=json.loads(raw)
    assert len(data['questions']) == 30
    assert all('tests' not in q and 'reference' not in q for q in data['questions'])
    assert data['provider'] == 'mock'


def test_browser_round_and_history(app):
    status,raw,_=app('POST','/api/start',dict(question_id='behavioural-unclear-goal'))
    assert status == 200
    state=json.loads(raw)
    for _ in range(5):
        status,raw,_=app('POST','/api/answer',dict(id=state['id'],answer='I clarified requirements by interviewing two volunteers and measured completion from a baseline.'))
        assert status == 200
        state=json.loads(raw)
    assert state['done'] and len(state['scorecard']['criteria']) == 5
    _,raw,_=app('GET','/api/history')
    assert json.loads(raw)['count'] == 1
    _,raw,_=app('GET','/api/session?id='+state['id'])
    assert len(json.loads(raw)['transcript']) == 5


@pytest.mark.parametrize('headers', [dict(Origin='https://evil.example'),{'X-Mockr-Token':'wrong'},dict(Host='evil.example')])
def test_cross_origin_and_rebinding_denied(app,headers):
    assert app('POST','/api/start',dict(question_id='design-job-board'),headers)[0] == 403


def test_bad_requests_and_paths(app):
    assert app('POST','/api/start',{})[0] == 400
    assert app('POST','/api/answer',dict(id='missing',answer='x'))[0] == 404
    assert app('GET','/api/session?id=missing')[0] == 404
    assert app('GET','/../../pyproject.toml')[0] == 404
    assert app('POST','/api/start',dict(question_id='x'*200000))[0] == 413
    assert app('GET','/api/history')[0] == 200
