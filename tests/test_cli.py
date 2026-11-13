import json
import subprocess
import sys

from mockr_coach.cli import main


def test_offline_demo_and_persistence(tmp_path,capsys):
    path=tmp_path/'demo.sqlite3'
    assert main(['demo','--db',str(path)]) == 0
    output=capsys.readouterr().out
    assert '5/5 hidden tests' in output
    assert 'OFFLINE MOCK' in output
    assert 'DSA' in output and 'SYSTEM DESIGN' in output and 'BEHAVIOURAL' in output
    assert 'Evidence:' in output
    assert main(['history','--db',str(path)]) == 0
    assert json.loads(capsys.readouterr().out)['count'] == 3


def test_calibration_no_labels(capsys):
    assert main(['calibrate']) == 0
    assert 'no human labels yet: fill calibration/human_labels.csv' in capsys.readouterr().out


def test_list_questions(capsys):
    assert main(['questions']) == 0
    assert len(capsys.readouterr().out.splitlines()) == 30


def test_text_default_and_multiline_code(monkeypatch,tmp_path,capsys):
    answers=iter(['I scan with a map.', 'def solve(weights, target):', ' seen = {}', ' for j,w in enumerate(weights):', '  if target-w in seen: return [seen[target-w],j]', '  seen.setdefault(w,j)', ' return []', ':end', 'Expected O(n) time and O(n) space.'])
    monkeypatch.setattr('builtins.input',lambda *args:next(answers))
    assert main(['--question','dsa-parcel-pair','--db',str(tmp_path/'text.sqlite3')]) == 0
    assert '5/5 hidden tests' in capsys.readouterr().out


def test_provider_configuration_error(capsys,monkeypatch):
    monkeypatch.delenv('MOCKR_API_KEY',raising=False)
    assert main(['interview','--provider','openai']) == 1
    assert 'API key' in capsys.readouterr().err


def test_missing_question_error(capsys):
    assert main(['interview','--question','missing']) == 1
    assert 'Unknown question' in capsys.readouterr().err


def test_module_help():
    result=subprocess.run([sys.executable,'-m','mockr_coach','--help'],capture_output=True,text=True)
    assert result.returncode == 0
    assert 'calibrate' in result.stdout
