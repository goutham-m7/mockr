import sys

import pytest

from mockr_coach.bank import Case
from mockr_coach.sandbox import Sandbox, SandboxUnavailable


def test_broken_runtime_is_not_blame_assigned_to_candidate(monkeypatch):
    monkeypatch.setattr(sys, "executable", "/nonexistent/mockr-python")
    with pytest.raises(SandboxUnavailable, match="startup"):
        Sandbox().run("def solve(): return 1", (Case([], 1),))
