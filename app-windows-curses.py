import curses
import time

def run(stdscr):
	curses.curs_set(0)
	curses.init_pair(
		1,
		curses.COLOR_RED,
		curses.COLOR_YELLOW,)

	h, w = stdscr.getmaxyx()

	text = "Hello"
	x = w//2 - len(text)//2
	y = h//2

	stdscr.addstr(0, 0, text)
	stdscr.refresh()

	time.sleep(3)

if __name__ == "__main__":
	print("Hello")
	curses.wrapper(run)
