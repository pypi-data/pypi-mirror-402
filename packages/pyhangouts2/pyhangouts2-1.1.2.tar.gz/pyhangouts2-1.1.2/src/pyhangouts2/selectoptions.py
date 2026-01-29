"""
@brief Really bad code.
Select options using `ncurses`.
@author NexusSfan
@copyright GPL-3.0-or-later
"""

# SPDX-FileCopyrightText: 2025 NexusSfan <nexussfan@duck.com>
# SPDX-License-Identifier: GPL-3.0-or-later

import curses
import sys

options = []
realoptions = []


def update_options(upd: list):
    """
    @brief Update the list of options displayed.
    @param upd List of options to display
    """
    global options
    options = upd


def real_options(upd):
    """
    @brief Update the list of options actually returned.
    @param upd List of options actually returned
    """
    global realoptions
    realoptions = upd


def select(stdscr):
    """
    @brief Select a choice in a menu.
    @param stdscr `ncurses` `stdscr`, provided by `curses.wrapper`
    """
    # Clear screen
    stdscr.clear()

    # Define menu options
    current_row = 0

    while True:
        # Display the menu
        for idx, option in enumerate(options):
            # todo: if screen is too small, scroll
            if idx == current_row:
                stdscr.addstr(
                    idx, 0, option, curses.A_REVERSE
                )  # Highlight the current option
            else:
                stdscr.addstr(idx, 0, option)

        stdscr.refresh()

        # Get user input
        key = stdscr.getch()

        # Navigate the menu
        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(options) - 1:
            current_row += 1
        elif key == curses.KEY_ENTER or key in [10, 13]:  # Enter key
            break

    # Clear the screen before exiting
    stdscr.clear()
    stdscr.refresh()

    if realoptions[current_row] == "Exit":
        sys.exit()
    else:
        return realoptions[current_row]
