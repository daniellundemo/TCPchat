import curses


class Windows:

    def __init__(self, whole_screen):
        # whole screen
        self.main_window = whole_screen.subwin(0, 0)
        self.w_height, self.w_width = self.main_window.getmaxyx()

        # header window
        self.header = curses.newwin(1, 40, 0, 1)

        # channel window
        self.channel_window = curses.newwin(self.w_height - 3, self.w_width - 15, 1, 0)

        # users window
        self.users_window = curses.newwin(0, 15, 1, self.w_width - 15)

        # input text window
        self.text_window = curses.newwin(3, self.w_width - 15, self.w_height - 2, 0)

        # draw all windows
        self.header.addstr(0, 1, 'chat client by teQ')
        self.header.refresh()
        self.refresh_channel_window()
        self.refresh_users_window()
        self.refresh_text_window()

    def refresh_channel_window(self):
        self.channel_window.clear()
        self.channel_window.border()
        self.channel_window.refresh()

    def refresh_users_window(self):
        self.users_window.clear()
        self.users_window.border()
        self.users_window.refresh()

    def refresh_text_window(self):
        h, w = self.text_window.getmaxyx()
        self.text_window.clear()
        self.text_window.border()
        self.text_window.addstr(h - 2, w - w + 2, '> ')
        self.text_window.refresh()
