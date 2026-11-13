"""OS isolation, per-case resource limits and a parent-enforced wall timeout."""

import json
import os
import platform
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from .bank import Case


@dataclass(frozen=True)
class RunResult:
    passed: int
    total: int
    status: str
    elapsed_ms: float


class SandboxUnavailable(RuntimeError):
    pass


class Sandbox:
    def __init__(self, timeout: float = 2.0):
        if not 0 < timeout <= 10:
            raise ValueError("Timeout must be between 0 and 10 seconds")
        self.timeout = timeout

    def _command(self, directory: Path) -> list[str]:
        executable = Path(sys.executable).resolve()
        runtime = executable.parent.parent
        worker = directory / "worker.py"
        if platform.system() == "Darwin" and Path("/usr/bin/sandbox-exec").exists():
            # Default deny: only the interpreter, system libraries and worker are readable.
            def literal(path):
                return json.dumps(str(path))

            reads = [
                runtime,
                Path("/System/Library"),
                Path("/usr/lib"),
                Path("/usr/share/locale"),
            ]
            # dyld reads the root directory itself; this does not grant child-file access.
            profile = '(version 1)(deny default)(allow sysctl-read)(allow file-read* (literal "/"))'
            profile += "(allow process-exec (literal " + literal(executable) + "))"
            profile += (
                "(allow file-read* "
                + " ".join("(subpath " + literal(p) + ")" for p in reads)
                + " (literal "
                + literal(worker)
                + ') (literal "/dev/null"))'
            )
            profile += '(allow file-write* (literal "/dev/null"))'
            return [
                "/usr/bin/sandbox-exec",
                "-p",
                profile,
                str(executable),
                "-I",
                "-S",
                str(worker),
            ]
        if platform.system() == "Linux" and shutil.which("bwrap"):
            command = [
                "bwrap",
                "--unshare-all",
                "--die-with-parent",
                "--new-session",
                "--cap-drop",
                "ALL",
            ]
            paths = {Path("/usr"), Path("/lib"), Path("/lib64"), runtime}
            # A uv-managed interpreter may live outside /usr.
            for path in sorted(paths):
                if path.exists():
                    command += ["--ro-bind", str(path), str(path)]
            command += [
                "--proc",
                "/proc",
                "--dev",
                "/dev",
                "--tmpfs",
                "/tmp",
                "--ro-bind",
                str(directory),
                "/work",
                "--chdir",
                "/work",
            ]
            return command + [str(executable), "-I", "-S", "/work/worker.py"]
        raise SandboxUnavailable(
            "Code execution requires macOS sandbox-exec or Linux bubblewrap; refusing unsandboxed execution"
        )

    def run(self, code: str, cases: tuple[Case, ...]) -> RunResult:
        if not code.strip() or len(code.encode()) > 65536:
            raise ValueError("Code must be nonempty and at most 64 KiB")
        if not cases:
            raise ValueError("At least one hidden case is required")
        start = time.monotonic()
        passed = 0
        statuses = []
        with tempfile.TemporaryDirectory(prefix="mockr-") as temp:
            directory = Path(temp).resolve()
            (directory / "worker.py").write_text(
                Path(__file__).with_name("worker.py").read_text()
            )
            command = self._command(directory)
            # Distinguish host isolation failures from incorrect candidate code.
            try:
                ready = subprocess.run(
                    command[:-1] + ["-c", "import json,resource; print('mockr-ready')"],
                    capture_output=True,
                    timeout=2,
                    check=False,
                    cwd=directory,
                    env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"},
                )
            except (OSError, subprocess.TimeoutExpired) as exc:
                raise SandboxUnavailable(
                    "Sandbox startup failed; check the Python runtime and OS isolation permissions"
                ) from exc
            if ready.returncode or ready.stdout.strip() != b"mockr-ready":
                raise SandboxUnavailable(
                    "Sandbox startup failed; check the Python runtime and OS isolation permissions"
                )
            for case in cases:
                with tempfile.TemporaryFile() as output:
                    process = subprocess.Popen(
                        command,
                        stdin=subprocess.PIPE,
                        stdout=output,
                        stderr=subprocess.DEVNULL,
                        cwd=directory,
                        env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"},
                        start_new_session=True,
                    )
                    try:
                        process.communicate(
                            json.dumps({"code": code, "args": case.args}).encode(),
                            timeout=self.timeout,
                        )
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.communicate()
                        statuses.append("timeout")
                        continue
                    output.seek(0)
                    try:
                        data = json.loads(output.read(16385))
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        data = {}
                    if (
                        process.returncode
                        or not isinstance(data, dict)
                        or set(data) != {"result"}
                    ):
                        statuses.append("runtime-error")
                    elif data["result"] == case.expected:
                        passed += 1
                    else:
                        statuses.append("wrong-answer")
        status = next(
            (s for s in ("timeout", "runtime-error", "wrong-answer") if s in statuses),
            "passed",
        )
        return RunResult(
            passed, len(cases), status, round((time.monotonic() - start) * 1000, 1)
        )
