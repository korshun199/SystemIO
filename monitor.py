import curses
import subprocess
import time

# Для отображения цветов
COLORS = {
    "green": curses.COLOR_GREEN,
    "red": curses.COLOR_RED,
    "yellow": curses.COLOR_YELLOW,
    "blue": curses.COLOR_BLUE,
    "cyan": curses.COLOR_CYAN,
    "white": curses.COLOR_WHITE,
}

def safe_addstr(stdscr, y, x, text, attr=0):
    """Функция для безопасного добавления текста на экран."""
    if y < 0 or x < 0:
        return
    max_y, max_x = stdscr.getmaxyx()
    if y >= max_y:
        return
    clipped = text[: max(0, max_x - x - 1)]
    try:
        stdscr.addstr(y, x, clipped, attr)
    except curses.error:
        pass

def draw_syslog(stdscr):
    """Рисует последние строки из /var/log/syslog в реальном времени."""
    stdscr.clear()
    stdscr.addstr(0, 0, "Watching /var/log/syslog (Ctrl+C to quit)...", curses.A_BOLD | curses.color_pair(COLORS["cyan"]))

    try:
        log_file = subprocess.Popen(["tail", "-f", "/var/log/syslog"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        y = 2
        while True:
            output = log_file.stdout.readline()
            if output == b"" and log_file.poll() is not None:
                break
            if output:
                safe_addstr(stdscr, y, 2, output.decode("utf-8"), curses.color_pair(COLORS["white"]))
                y += 1
                if y > curses.LINES - 2:
                    y = 2
            stdscr.refresh()
            time.sleep(0.1)
    except Exception as e:
        safe_addstr(stdscr, 1, 0, f"Error: {e}", curses.color_pair(COLORS["red"]))
        stdscr.refresh()

def draw_netstat(stdscr):
    """Рисует вывод netstat (или ss) с цветами для сетевых соединений."""
    stdscr.clear()
    stdscr.addstr(0, 0, "Network connections (Ctrl+C to quit)...", curses.A_BOLD | curses.color_pair(COLORS["cyan"]))

    try:
        netstat_output = subprocess.check_output(["ss", "-tuln"], text=True)
        lines = netstat_output.splitlines()
        y = 2
        for line in lines:
            if line.startswith("State"):
                continue
            safe_addstr(stdscr, y, 2, line, curses.color_pair(COLORS["yellow"]))
            y += 1
            if y > curses.LINES - 2:
                y = 2
        stdscr.refresh()
    except Exception as e:
        safe_addstr(stdscr, 1, 0, f"Error: {e}", curses.color_pair(COLORS["red"]))
        stdscr.refresh()

def draw_process_tree(stdscr):
    """Рисует дерево процессов с цветами."""
    stdscr.clear()
    stdscr.addstr(0, 0, "Process Tree (Ctrl+C to quit)...", curses.A_BOLD | curses.color_pair(COLORS["cyan"]))

    try:
        # Команда ps для отображения дерева процессов
        process_tree_output = subprocess.check_output("ps axjf", shell=True, text=True)
        lines = process_tree_output.splitlines()
        y = 2
        for line in lines:
            if line.startswith("PID"):
                continue  # Пропускаем заголовок
            safe_addstr(stdscr, y, 2, line, curses.color_pair(COLORS["green"]))
            y += 1
            if y > curses.LINES - 2:
                y = 2
        stdscr.refresh()
    except Exception as e:
        safe_addstr(stdscr, 1, 0, f"Error: {e}", curses.color_pair(COLORS["red"]))
        stdscr.refresh()

def main(stdscr):
    """Главная функция для управления экранами и переключением."""
    curses.start_color()
    curses.init_pair(COLORS["green"], curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(COLORS["red"], curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(COLORS["yellow"], curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(COLORS["blue"], curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(COLORS["cyan"], curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(COLORS["white"], curses.COLOR_WHITE, curses.COLOR_BLACK)

    stdscr.clear()
    stdscr.refresh()

    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "Choose an option:", curses.A_BOLD | curses.color_pair(COLORS["cyan"]))
        stdscr.addstr(1, 0, "1 - View Syslog", curses.color_pair(COLORS["yellow"]))
        stdscr.addstr(2, 0, "2 - View Network Connections", curses.color_pair(COLORS["yellow"]))
        stdscr.addstr(3, 0, "3 - View Process Tree", curses.color_pair(COLORS["yellow"]))
        stdscr.addstr(4, 0, "Q - Quit", curses.color_pair(COLORS["red"]))
        stdscr.refresh()

        key = stdscr.getch()
        if key == ord('1'):
            draw_syslog(stdscr)
        elif key == ord('2'):
            draw_netstat(stdscr)
        elif key == ord('3'):
            draw_process_tree(stdscr)
        elif key == ord('q') or key == ord('Q'):
            break

if __name__ == "__main__":
    curses.wrapper(main)