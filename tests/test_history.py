import pytest

from mockr_coach.history import History


def record(id='one', score=2, topic='arrays', kind='dsa'):
    return dict(id=id, question_id='q', title='A question', kind=kind, topic=topic, provider='mock', transcript=[dict(stage='approach',answer='I used a map.')], execution=None, scorecard=dict(overall=score, criteria=[dict(id='approach',score=score,quote='I used a map.',feedback='Explain why.')]))


def test_sqlite_round_trip(tmp_path):
    path = tmp_path/'history.sqlite3'
    with History(path) as db: db.save(record())
    with History(path) as db:
        assert db.get('one')['transcript'][0]['answer'] == 'I used a map.'
        assert db.get('missing') is None
        assert db.summary()['count'] == 1


def test_progress_topics_and_trend():
    with History(':memory:') as db:
        for row in [record(),record('two',4),record('three',5,'graphs')]: db.save(row)
        summary = db.summary()
        assert summary['weak_topics'][0] == dict(topic='arrays',kind='dsa',mean=3.0,sessions=2)
        assert [r['score'] for r in summary['trend']] == [2,4,5]
        assert summary['count'] == 3
        with pytest.raises(ValueError,match='already'): db.save(record())


def test_empty_history():
    with History(':memory:') as db:
        assert db.summary() == dict(count=0,weak_topics=[],trend=[],sessions=[])
