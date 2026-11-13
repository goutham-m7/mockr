"""Linux-specific kernel-isolation regressions; no Python-only write filters."""

import platform

import pytest

from mockr_coach.bank import Case
from mockr_coach.sandbox import Sandbox

pytestmark = pytest.mark.skipif(
    platform.system() != "Linux", reason="Requires Linux bubblewrap"
)


@pytest.mark.parametrize(
    "path",
    [
        "/tmp/mockr-escape",
        "/work/mockr-escape",
        "/mockr-escape",
        "/dev/mockr-escape",
        "/usr/mockr-escape",
    ],
)
def test_path_writes_are_denied(path):
    code = f"def solve():\n open({path!r}, 'w').write('bad')\n return 1"
    assert Sandbox().run(code, (Case([], 1),)).status == "runtime-error"


@pytest.mark.parametrize(
    "operation",
    [
        "os.mkdir('/tmp/mockr-directory')",
        "os.symlink('/work/worker.py', '/tmp/mockr-link')",
        "os.unlink('/work/worker.py')",
        "os.rename('/work/worker.py', '/tmp/mockr-worker')",
    ],
)
def test_filesystem_mutations_are_denied(operation):
    code = f"def solve():\n import os\n {operation}\n return 1"
    assert Sandbox().run(code, (Case([], 1),)).status == "runtime-error"


def test_devnull_remains_usable():
    code = "def solve():\n with open('/dev/null', 'w') as sink: sink.write('discarded')\n return 1"
    assert Sandbox().run(code, (Case([], 1),)).status == "passed"
