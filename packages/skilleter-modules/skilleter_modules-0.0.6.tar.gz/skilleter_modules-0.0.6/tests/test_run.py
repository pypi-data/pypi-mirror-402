import subprocess

import skilleter_modules.run as run


def test_process_echoes_and_captures_stdout(monkeypatch):
    real_popen = subprocess.Popen

    def fake_popen(command, bufsize=0, stdout=None, stderr=None, text=False, errors=None, encoding=None, **kwargs):
        assert stdout == subprocess.PIPE
        assert stderr == subprocess.PIPE
        proc = real_popen(['printf', 'hello\n'], stdout=stdout, stderr=stderr, text=True)
        return proc

    monkeypatch.setattr(subprocess, 'Popen', fake_popen)
    result = run._process(['printf', 'hello'])
    assert result['stdout'] == ['hello']


def test_process_raises_on_nonzero(monkeypatch):
    real_popen = subprocess.Popen

    def fake_popen(command, bufsize=0, stdout=None, stderr=None, text=False, errors=None, encoding=None, **kwargs):
        return real_popen(['python', '-c', 'import sys; sys.exit(3)'], stdout=stdout, stderr=stderr, text=True)

    monkeypatch.setattr(subprocess, 'Popen', fake_popen)
    try:
        run._process(['python', '-c', 'exit 3'])
    except run.RunError as exc:
        assert exc.status == 3
    else:
        assert False, 'expected RunError'
