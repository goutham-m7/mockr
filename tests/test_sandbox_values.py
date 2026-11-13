from mockr_coach.bank import Case
from mockr_coach.sandbox import Sandbox


def test_boolean_is_not_an_integer_answer():
    result = Sandbox().run("def solve(): return True", (Case([], 1),))
    assert result.status == "wrong-answer"


def test_nested_boolean_does_not_match_integer():
    result = Sandbox().run("def solve(): return {'x':[True]}", (Case([], {"x": [1]}),))
    assert result.status == "wrong-answer"


def test_json_objects_ignore_key_order():
    result = Sandbox().run(
        "def solve(): return {'b':2,'a':1}", (Case([], {"a": 1, "b": 2}),)
    )
    assert result.status == "passed"
