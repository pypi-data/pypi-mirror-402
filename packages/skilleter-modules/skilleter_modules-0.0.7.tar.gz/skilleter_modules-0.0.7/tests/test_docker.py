import types

import pytest

import skilleter_modules.docker as docker


class DummyResult(types.SimpleNamespace):
    pass


def test_instances_parses_lines(monkeypatch):
    def fake_run(cmd, capture_output, check, text):
        assert cmd[:2] == ['docker', 'ps']
        return DummyResult(stdout='id1\nid2\n')

    monkeypatch.setattr('subprocess.run', fake_run)
    assert docker.instances() == ['id1', 'id2']


def test_stop_force_passes_flag(monkeypatch):
    seen = {}

    def fake_run(cmd, check, capture_output):
        seen['cmd'] = cmd
        return DummyResult()

    monkeypatch.setattr('subprocess.run', fake_run)
    docker.stop('abc', force=True)
    assert seen['cmd'] == ['docker', 'stop', '--force', 'abc']
