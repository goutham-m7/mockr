import pytest

from mockr_coach.bank import Case, load_bank
from mockr_coach.sandbox import Sandbox


def test_correct_solution():
    result = Sandbox().run("def solve(x): return x + 1", (Case([2], 3), Case([-1], 0)))
    assert (result.passed, result.total, result.status) == (2, 2, "passed")


@pytest.mark.parametrize(
    "code,status",
    [
        ("def solve(x): return 0", "wrong-answer"),
        ("def solve(x): raise ValueError('private')", "runtime-error"),
        ("def solve(:", "runtime-error"),
        ("def solve(x):\n while True: pass", "timeout"),
        (
            "def solve(x):\n import socket\n socket.create_connection(('1.1.1.1',80),timeout=.1)\n return 3",
            "runtime-error",
        ),
        (
            "def solve(x):\n open('/tmp/mockr-escape','w').write('bad')\n return 3",
            "runtime-error",
        ),
        (
            "def solve(x):\n import subprocess\n subprocess.run(['/usr/bin/true'],check=True)\n return 3",
            "runtime-error",
        ),
    ],
)
def test_rejects_unsafe_or_incorrect_code(code, status):
    result = Sandbox(timeout=0.5).run(code, (Case([2], 3),))
    assert result.status == status
    assert result.passed == 0
    assert "private" not in str(result)


def test_host_secret_is_unreadable(tmp_path):
    secret = tmp_path / "secret.txt"
    secret.write_text("secret")
    result = Sandbox().run(
        f"def solve(x): return open({str(secret)!r}).read()", (Case([2], "secret"),)
    )
    assert result.status == "runtime-error"


def test_large_output_is_bounded():
    result = Sandbox().run("def solve(x): return 'a' * 1000000", (Case([2], "no"),))
    assert result.status == "runtime-error"


def test_source_limit():
    with pytest.raises(ValueError, match="64"):
        Sandbox().run("x" * 70000, (Case([], 0),))


@pytest.mark.parametrize(
    "question", [q for q in load_bank() if q.kind == "dsa"], ids=lambda q: q.id
)
def test_every_reference_passes_hidden_cases(question):
    result = Sandbox().run(question.reference, question.tests)
    assert result.status == "passed", (question.id, result)
    assert result.passed == len(question.tests)
