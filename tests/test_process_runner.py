"""Pruebas del ejecutor modular de procesos de la etapa 4."""

import subprocess
from types import SimpleNamespace

import pytest

from core.processes.runner import must, run_command, terminate_process_tree


def test_run_command_is_noninteractive_and_captures_output(monkeypatch):
    expected = SimpleNamespace(returncode=0, stdout="ok", stderr="")
    calls = {}

    def fake_run(cmd, **kwargs):
        calls["cmd"] = cmd
        calls.update(kwargs)
        return expected

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert run_command(["printf", "ok"]) is expected
    assert calls["capture_output"] is True
    assert calls["text"] is True
    assert calls["stdin"] is subprocess.DEVNULL


def test_must_returns_success_and_reports_failure_detail():
    success = SimpleNamespace(returncode=0, stdout="", stderr="")
    assert must(success, "ejecutar") is success

    failure = SimpleNamespace(returncode=2, stdout="", stderr="detalle")
    with pytest.raises(RuntimeError, match="detalle"):
        must(failure, "ejecutar")


def test_terminate_process_tree_escalates_after_timeout(monkeypatch):
    class FakeProcess:
        pid = 123
        def __init__(self):
            self.signals = []
            self.wait_calls = 0
        def send_signal(self, sig):
            self.signals.append(sig)
        def wait(self, timeout):
            self.wait_calls += 1
            if self.wait_calls == 1:
                raise subprocess.TimeoutExpired("fake", timeout)
            return 0

    import core.processes.runner as runner
    process = FakeProcess()
    monkeypatch.setattr(runner, "signal_process_group", lambda proc, sig: proc.send_signal(sig))
    terminate_process_tree(process, timeout=0.01)
    assert len(process.signals) == 2
