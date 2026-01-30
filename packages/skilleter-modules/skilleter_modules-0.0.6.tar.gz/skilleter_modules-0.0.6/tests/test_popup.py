from types import SimpleNamespace

import skilleter_modules.popup as popup


class FakePanel:
    def __init__(self):
        self.update_calls = 0
        self.new_calls = []

    def new_panel(self, window):
        self.new_calls.append(window)
        return SimpleNamespace(top=lambda: None)

    def update_panels(self):
        self.update_calls += 1


class FakeWindow:
    def __init__(self):
        self.add_calls = []
        self.bkgd_calls = []

    def bkgd(self, ch, colour):
        self.bkgd_calls.append((ch, colour))

    def addstr(self, y_pos, x_pos, line, colour):
        self.add_calls.append((y_pos, x_pos, line, colour))


class FakeScreen:
    def __init__(self, keys):
        self.keys = list(keys)
        self.getch_calls = 0
        self.refresh_calls = 0

    def getmaxyx(self):
        return (24, 80)

    def refresh(self):
        self.refresh_calls += 1

    def getch(self):
        self.getch_calls += 1
        return self.keys.pop(0)


def test_waitkey_occurs_on_exit(monkeypatch):
    fake_panel = FakePanel()

    fake_curses = SimpleNamespace(
        KEY_RESIZE=999,
        panel=fake_panel,
    )

    fake_curses.color_pair = lambda colour: f'colour-{colour}'
    fake_curses.newwin = lambda h, w, y, x: FakeWindow()

    monkeypatch.setattr(popup, 'curses', fake_curses)

    keys = [fake_curses.KEY_RESIZE, ord('a')]
    screen = FakeScreen(keys)

    with popup.PopUp(screen, 'hello', 3, waitkey=True):
        enter_updates = fake_panel.update_calls
        assert screen.getch_calls == 0

    assert fake_panel.update_calls == enter_updates + 1
    assert screen.getch_calls == 2
    assert screen.refresh_calls >= 1
