"""Minimal test code for colour"""

import io

import skilleter_modules.colour as colour

def test_colour():
    """Very basic test"""

    for combo in (0, 1, 2):
        print()
        if combo == 0:
            print('Background colours')
        elif combo == 1:
            print('Foreground colours')
        else:
            print('Combinations')

        print()
        for y in range(0, 16):
            for x in range(0, 16):
                colour_index = x + y * 16

                if combo == 0:
                    colour.write(format('[B%d]%4d' % (colour_index, colour_index)), newline=False)
                elif combo == 1:
                    colour.write(format('[%d]%4d' % (colour_index, colour_index)), newline=False)
                else:
                    colour.write(format('[B%d]%4d[%d]/%4d ' % (colour_index, colour_index, 255 - colour_index, 255 - colour_index)), newline=False)

            colour.write('[NORMAL]')

    print()

    colour.write('Foreground: [RED]red [GREEN]green [BLACK]black [NORMAL]normal')
    colour.write('Background: [BRED]red [BGREEN]green [BBLACK]black [NORMAL]normal')

    colour.write('Foreground: [BBLUE:blue] [RED:red] normal')

    colour.write('Bright foreground: [RED_B]red [GREEN_B]green [BLACK_B]black [NORMAL]normal')
    colour.write('Bright background: [BRED_B]red [BGREEN_B]green [BBLACK_B]black [NORMAL]normal')

    colour.write('Foreground: [BBLUE:blue_B] [RED:red_B] normal')

    print()

    colour.write('[NORMAL:Normal text]')
    colour.write('[FAINT:Faint text]')
    colour.write('[ITALIC:Italic text]')
    colour.write('[UNDERSCORE:Underscored text]')
    colour.write('[BLINK:Blinking text]')
    colour.write('[REVERSE:Reverse text]')
    colour.write('[STRIKE:Strikethrough text]')


def test_write_empty_string_no_indent():
    buf = io.StringIO()
    colour.write('', indent=4, stream=buf)
    assert buf.getvalue() == '\n'


def test_write_with_indent_and_strip():
    buf = io.StringIO()
    colour.write('  text', indent=2, strip=True, stream=buf)
    assert buf.getvalue() == '  text\n'
