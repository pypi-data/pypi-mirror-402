import os

import skilleter_modules.files as files


def test_format_size_suffix_and_sign():
    assert files.format_size(-1024, always_suffix=True).startswith('-')
    assert files.format_size(1024, always_suffix=True).endswith(' KiB')


def test_backup_no_file_no_raise(tmp_path):
    missing = tmp_path / 'missing.txt'
    # Should no-op when file is absent
    files.backup(str(missing))
    assert not list(tmp_path.iterdir())


def test_backup_creates_copy(tmp_path):
    src = tmp_path / 'file.txt'
    src.write_text('data', encoding='utf-8')
    files.backup(str(src))
    assert (tmp_path / 'file.bak').read_text(encoding='utf-8') == 'data'
