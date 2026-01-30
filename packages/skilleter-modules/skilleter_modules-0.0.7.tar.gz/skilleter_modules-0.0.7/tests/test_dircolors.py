import io
import stat

import skilleter_modules.dircolors as dircolors


def test_load_from_dircolors_does_not_close_stream():
    data = io.StringIO('DIR 01;34\n')
    dc = dircolors.Dircolors(load=False)
    assert dc.load_from_dircolors(data, strict=True) is True
    assert data.closed is False
    assert dc.loaded is True


def test_format_mode_directory_and_extension(tmp_path):
    dc = dircolors.Dircolors(load=False)
    # Load minimal rules: directories blue (01;34), *.txt red (31)
    rules = 'DIR 01;34\n*.txt 31\n'
    assert dc.load_from_dircolors(io.StringIO(rules), strict=True)

    # Directory formatting: should wrap with escape codes
    formatted_dir = dc.format_mode('name', (stat.S_IFDIR | stat.S_IRUSR))
    assert '\x1b[' in formatted_dir and formatted_dir.endswith('\x1b[0m')

    # Extension formatting: .txt uses red foreground
    formatted_file = dc.format_mode('file.txt', 0)
    assert '\x1b[' in formatted_file and formatted_file.endswith('\x1b[0m')
