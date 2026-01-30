import skilleter_modules.path as path


def test_is_subdirectory_strict_descendant():
    assert path.is_subdirectory('/root', '/root/child') is True


def test_is_subdirectory_same_path_is_false():
    assert path.is_subdirectory('/root', '/root') is False


def test_is_subdirectory_unrelated_is_false():
    assert path.is_subdirectory('/root/one', '/root/two') is False


def test_trimpath_home_to_tilde(monkeypatch):
    monkeypatch.setenv('HOME', '/home/user')
    assert path.trimpath('/home/user/projects', 80).startswith('~/')


def test_trimpath_truncates_middle():
    trimmed = path.trimpath('/a/b/c/d/e/f/g/h/i', 10)
    assert '...' in trimmed
