#! /usr/bin/env python3

################################################################################
""" Colour colour output

    Copyright (C) 2017-18 John Skilleter

    Licence: GPL v3 or later

    0-15 are the standard VGA colour codes
    16-21 are a few extras
    22-231 appear to be a sort of colour cube
    232-255 are 24 shades of grey
"""
################################################################################

import sys
import re

################################################################################
# Constants

_ANSI_NORMAL = '\x1b[0m'

_ANSI_BOLD = '\x1b[1m'
_ANSI_FAINT = '\x1b[2m'
_ANSI_ITALIC = '\x1b[3m'
_ANSI_UNDERSCORE = '\x1b[4m'
_ANSI_BLINK = '\x1b[5m'
_ANSI_REVERSE = '\x1b[7m'
_ANSI_STRIKE = '\x1b[9m'

_ANSI_BLACK = '\x1b[30m'
_ANSI_RED = '\x1b[31m'
_ANSI_GREEN = '\x1b[32m'
_ANSI_YELLOW = '\x1b[33m'
_ANSI_BLUE = '\x1b[34m'
_ANSI_MAGENTA = '\x1b[35m'
_ANSI_CYAN = '\x1b[36m'
_ANSI_WHITE = '\x1b[37m'

_ANSI_BLACK_B = '\x1b[1;30m'
_ANSI_RED_B = '\x1b[1;31m'
_ANSI_GREEN_B = '\x1b[1;32m'
_ANSI_YELLOW_B = '\x1b[1;33m'
_ANSI_BLUE_B = '\x1b[1;34m'
_ANSI_MAGENTA_B = '\x1b[1;35m'
_ANSI_CYAN_B = '\x1b[1;36m'
_ANSI_WHITE_B = '\x1b[1;37m'

_ANSI_BBLACK = '\x1b[40m'
_ANSI_BRED = '\x1b[41m'
_ANSI_BGREEN = '\x1b[42m'
_ANSI_BYELLOW = '\x1b[43m'
_ANSI_BBLUE = '\x1b[44m'
_ANSI_BMAGENTA = '\x1b[45m'
_ANSI_BCYAN = '\x1b[46m'
_ANSI_BWHITE = '\x1b[47m'

_ANSI_BBLACK_B = '\x1b[1;40m'
_ANSI_BRED_B = '\x1b[1;41m'
_ANSI_BGREEN_B = '\x1b[1;42m'
_ANSI_BYELLOW_B = '\x1b[1;43m'
_ANSI_BBLUE_B = '\x1b[1;44m'
_ANSI_BMAGENTA_B = '\x1b[1;45m'
_ANSI_BCYAN_B = '\x1b[1;46m'
_ANSI_BWHITE_B = '\x1b[1;47m'

_ANSI_CLEAREOL = '\x1b[K'

# Looking up tables for converting textual colour codes to ANSI codes

ANSI_REGEXES = \
    (
        (r'\[NORMAL:(.*?)\]', r'%s\1%s' % (_ANSI_NORMAL, _ANSI_NORMAL)),
        (r'\[BOLD:(.*?)\]', r'%s\1%s' % (_ANSI_BOLD, _ANSI_NORMAL)),
        (r'\[FAINT:(.*?)\]', r'%s\1%s' % (_ANSI_FAINT, _ANSI_NORMAL)),
        (r'\[ITALIC:(.*?)\]', r'%s\1%s' % (_ANSI_ITALIC, _ANSI_NORMAL)),
        (r'\[UNDERSCORE:(.*?)\]', r'%s\1%s' % (_ANSI_UNDERSCORE, _ANSI_NORMAL)),
        (r'\[BLINK:(.*?)\]', r'%s\1%s' % (_ANSI_BLINK, _ANSI_NORMAL)),
        (r'\[REVERSE:(.*?)\]', r'%s\1%s' % (_ANSI_REVERSE, _ANSI_NORMAL)),
        (r'\[STRIKE:(.*?)\]', r'%s\1%s' % (_ANSI_STRIKE, _ANSI_NORMAL)),

        (r'\[BLACK:(.*?)\]', r'%s\1%s' % (_ANSI_BLACK, _ANSI_NORMAL)),
        (r'\[RED:(.*?)\]', r'%s\1%s' % (_ANSI_RED, _ANSI_NORMAL)),
        (r'\[GREEN:(.*?)\]', r'%s\1%s' % (_ANSI_GREEN, _ANSI_NORMAL)),
        (r'\[YELLOW:(.*?)\]', r'%s\1%s' % (_ANSI_YELLOW, _ANSI_NORMAL)),
        (r'\[BLUE:(.*?)\]', r'%s\1%s' % (_ANSI_BLUE, _ANSI_NORMAL)),
        (r'\[MAGENTA:(.*?)\]', r'%s\1%s' % (_ANSI_MAGENTA, _ANSI_NORMAL)),
        (r'\[CYAN:(.*?)\]', r'%s\1%s' % (_ANSI_CYAN, _ANSI_NORMAL)),
        (r'\[WHITE:(.*?)\]', r'%s\1%s' % (_ANSI_WHITE, _ANSI_NORMAL)),

        (r'\[BLACK_B:(.*?)\]', r'%s\1%s' % (_ANSI_BLACK_B, _ANSI_NORMAL)),
        (r'\[RED_B:(.*?)\]', r'%s\1%s' % (_ANSI_RED_B, _ANSI_NORMAL)),
        (r'\[GREEN_B:(.*?)\]', r'%s\1%s' % (_ANSI_GREEN_B, _ANSI_NORMAL)),
        (r'\[YELLOW_B:(.*?)\]', r'%s\1%s' % (_ANSI_YELLOW_B, _ANSI_NORMAL)),
        (r'\[BLUE_B:(.*?)\]', r'%s\1%s' % (_ANSI_BLUE_B, _ANSI_NORMAL)),
        (r'\[MAGENTA_B:(.*?)\]', r'%s\1%s' % (_ANSI_MAGENTA_B, _ANSI_NORMAL)),
        (r'\[CYAN_B:(.*?)\]', r'%s\1%s' % (_ANSI_CYAN_B, _ANSI_NORMAL)),
        (r'\[WHITE_B:(.*?)\]', r'%s\1%s' % (_ANSI_WHITE_B, _ANSI_NORMAL)),

        (r'\[BBLACK:(.*?)\]', r'%s\1%s' % (_ANSI_BBLACK, _ANSI_NORMAL)),
        (r'\[BRED:(.*?)\]', r'%s\1%s' % (_ANSI_BRED, _ANSI_NORMAL)),
        (r'\[BGREEN:(.*?)\]', r'%s\1%s' % (_ANSI_BGREEN, _ANSI_NORMAL)),
        (r'\[BYELLOW:(.*?)\]', r'%s\1%s' % (_ANSI_BYELLOW, _ANSI_NORMAL)),
        (r'\[BBLUE:(.*?)\]', r'%s\1%s' % (_ANSI_BBLUE, _ANSI_NORMAL)),
        (r'\[BMAGENTA:(.*?)\]', r'%s\1%s' % (_ANSI_BMAGENTA, _ANSI_NORMAL)),
        (r'\[BCYAN:(.*?)\]', r'%s\1%s' % (_ANSI_BCYAN, _ANSI_NORMAL)),
        (r'\[BWHITE:(.*?)\]', r'%s\1%s' % (_ANSI_BWHITE, _ANSI_NORMAL)),

        (r'\[BBLACK_B:(.*?)\]', r'%s\1%s' % (_ANSI_BBLACK_B, _ANSI_NORMAL)),
        (r'\[BRED_B:(.*?)\]', r'%s\1%s' % (_ANSI_BRED_B, _ANSI_NORMAL)),
        (r'\[BGREEN_B:(.*?)\]', r'%s\1%s' % (_ANSI_BGREEN_B, _ANSI_NORMAL)),
        (r'\[BYELLOW_B:(.*?)\]', r'%s\1%s' % (_ANSI_BYELLOW_B, _ANSI_NORMAL)),
        (r'\[BBLUE_B:(.*?)\]', r'%s\1%s' % (_ANSI_BBLUE_B, _ANSI_NORMAL)),
        (r'\[BMAGENTA_B:(.*?)\]', r'%s\1%s' % (_ANSI_BMAGENTA_B, _ANSI_NORMAL)),
        (r'\[BCYAN_B:(.*?)\]', r'%s\1%s' % (_ANSI_BCYAN_B, _ANSI_NORMAL)),
        (r'\[BWHITE_B:(.*?)\]', r'%s\1%s' % (_ANSI_BWHITE_B, _ANSI_NORMAL)),
    )

ANSI_CODES = \
    (
        ('[NORMAL]', _ANSI_NORMAL),
        ('[BOLD]', _ANSI_BOLD),
        ('[FAINT]', _ANSI_FAINT),
        ('[ITALIC]', _ANSI_ITALIC),
        ('[UNDERSCORE]', _ANSI_UNDERSCORE),
        ('[BLINK]', _ANSI_BLINK),
        ('[REVERSE]', _ANSI_REVERSE),
        ('[STRIKE]', _ANSI_STRIKE),

        ('[BLACK]', _ANSI_BLACK),
        ('[RED]', _ANSI_RED),
        ('[GREEN]', _ANSI_GREEN),
        ('[YELLOW]', _ANSI_YELLOW),
        ('[BLUE]', _ANSI_BLUE),
        ('[MAGENTA]', _ANSI_MAGENTA),
        ('[CYAN]', _ANSI_CYAN),
        ('[WHITE]', _ANSI_WHITE),

        ('[BLACK_B]', _ANSI_BLACK_B),
        ('[RED_B]', _ANSI_RED_B),
        ('[GREEN_B]', _ANSI_GREEN_B),
        ('[YELLOW_B]', _ANSI_YELLOW_B),
        ('[BLUE_B]', _ANSI_BLUE_B),
        ('[MAGENTA_B]', _ANSI_MAGENTA_B),
        ('[CYAN_B]', _ANSI_CYAN_B),
        ('[WHITE_B]', _ANSI_WHITE_B),

        ('[BBLACK]', _ANSI_BBLACK),
        ('[BRED]', _ANSI_BRED),
        ('[BGREEN]', _ANSI_BGREEN),
        ('[BYELLOW]', _ANSI_BYELLOW),
        ('[BBLUE]', _ANSI_BBLUE),
        ('[BMAGENTA]', _ANSI_BMAGENTA),
        ('[BCYAN]', _ANSI_BCYAN),
        ('[BWHITE]', _ANSI_BWHITE),

        ('[BBLACK_B]', _ANSI_BBLACK_B),
        ('[BRED_B]', _ANSI_BRED_B),
        ('[BGREEN_B]', _ANSI_BGREEN_B),
        ('[BYELLOW_B]', _ANSI_BYELLOW_B),
        ('[BBLUE_B]', _ANSI_BBLUE_B),
        ('[BMAGENTA_B]', _ANSI_BMAGENTA_B),
        ('[BCYAN_B]', _ANSI_BCYAN_B),
        ('[BWHITE_B]', _ANSI_BWHITE_B),
    )

# Regex to match an ANSI control sequence

RE_ANSI = re.compile(r'\x1b\[([0-9][0-9;]*)*m')

################################################################################

def format(txt):
    """ Convert textual colour codes in a string to ANSI codes.
        Codes can be specified as either [COLOUR], where all following text
        is output in the specified colour or [COLOR:text] where only 'text' is
        output in the colour, with subsequent text output in the default colours """

    # Replace [COLOUR:text] with COLOURtextNORMAL using regexes

    if re.search(r'\[.*:.*\]', txt):
        for regex in ANSI_REGEXES:
            txt = re.sub(regex[0], regex[1], txt)

    # Replace [COLOUR] with COLOUR

    if re.search(r'\[.*\]', txt):
        for code in ANSI_CODES:
            txt = txt.replace(code[0], code[1])

    # Now replace [N(N)(N)] with 256 colour colour code.

    while True:
        p = re.match(r'.*\[([0-9]{1,3})\].*', txt)
        if p is None:
            break

        value = int(p.group(1))
        txt = txt.replace('[%s]' % p.group(1), '\x1b[38;5;%dm' % value)

    while True:
        p = re.match(r'.*\[B([0-9]{1,3})\].*', txt)
        if p is None:
            break

        value = int(p.group(1))
        txt = txt.replace('[B%s]' % p.group(1), '\x1b[48;5;%dm' % value)

    return txt

################################################################################

def write(txt=None, newline=True, stream=sys.stdout, indent=0, strip=False, cleareol=False, cr=False):
    """ Write to the specified stream (defaulting to stdout), converting colour codes to ANSI
        txt can be None, a string or a list of strings."""

    if txt:
        if isinstance(txt, str):
            txt = txt.split('\n')

        for n, line in enumerate(txt):
            line = format(line)

            if strip:
                line = line.strip()

            if indent:
                stream.write(' ' * indent)

            stream.write(line)

            if cleareol:
                stream.write(_ANSI_CLEAREOL)

            if newline or n < len(txt) - 1:
                stream.write('\n')
            elif cr:
                stream.write('\r')

    else:
        if cleareol:
            stream.write(_ANSI_CLEAREOL)

        if newline:
            stream.write('\n')
        elif cr:
            stream.write('\r')

################################################################################

def error(txt, newline=True, stream=sys.stderr, status=1, prefix=False):
    """ Write an error message to the specified stream (defaulting to
        stderr) and exit with the specified status code (defaulting to 1)
        Prefix the output with 'ERROR:' in red if prefix==True """

    if prefix:
        write('[RED:ERROR]: ', newline=False, stream=stream, )

    write(txt, newline, stream)

    sys.exit(status)

################################################################################

def warning(txt, newline=True, stream=sys.stderr, prefix=False):
    """ Write a warning message to the specified stream (defaulting to
        stderr). Prefix the output with 'WARNING:' in red if prefix==True """

    if prefix:
        write('[RED:WARNING]: ', newline=False, stream=stream, )

    write(txt, newline, stream)
