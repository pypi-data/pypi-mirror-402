import skilleter_modules.tidy as tidy


def test_remove_times_does_not_match_stray_dot():
    text = 'Version 1. release'
    assert tidy.remove_times(text) == text


def test_remove_times_replaces_seconds():
    assert tidy.remove_times('took 12.5 seconds') == 'took {ELAPSED}'
