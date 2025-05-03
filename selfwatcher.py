import threading
import time
from datetime import datetime, timezone
import string
import os
import glob
import Xlib
from Xlib import X
from pathlib import Path

user_id = os.getuid()
xauth_files = glob.glob(f"/run/user/{user_id}/xauth_*")
assert len(xauth_files) > 0, "Error: could not find XAUTHORITY file"
if xauth_files:
    os.environ["XAUTHORITY"] = xauth_files[0]
    os.environ["DISPLAY"] = ":0"

from pynput import keyboard, mouse  # noqa: E402
from pynput.keyboard import Key  # noqa: E402
from pynput.mouse import Controller as MouseController  # noqa: E402

mouse_controller = MouseController()
display = Xlib.display.Display()
screen = display.screen()

home_dir = Path.home()
log_base_dir = home_dir / ".local" / "selfwatcher"
assert log_base_dir.exists(), "Log dir missing: {log_base_dir}"

IDLE_TIMEOUT_SEC = 5 * 60
POLL_INTERVAL_SEC = 2
PRINT_INTERVAL_SEC = 59
LINE_SEP = ";"
LINE_TIME_FMT = "%Y-%m-%d %H:%M:%S"
UNKNOWN = "_unknown"
IDLE = "_idle"

KEYS_ARR = [
    ("ALPHABETS", "k-az"),
    ("NUMBERS", "k-09"),
    ("SPECHARS", "k-spl"),
    ("ALT", "k-alt"),
    ("SHIFT", "k-sft"),
    ("CTRL", "k-ctl"),
    ("DELETE", "k-del"),
    ("CMD", "k-cmd"),
    ("ARROWS", "k-arr"),
    ("ENTER", "k-etr"),
    ("SPACE", "k-spc"),
    ("TAB", "k-tab"),
    ("ESC", "k-esc"),
    ("NAV", "k-nav"),
    ("FUNC", "k-fun"),
    ("OTHERS", "k-oth"),
    ("LCLICK", "m-lc"),
    ("RCLICK", "m-rc"),
    ("MCLICK", "m-mc"),
    ("SCROLL", "m-srl"),
]
KEYS_INDICES = {k:i for i, (k,_) in enumerate(KEYS_ARR)}

INIT_COUNTS = [0 for _ in KEYS_ARR]
G_key_counts_now = INIT_COUNTS.copy()
G_key_counts_next = INIT_COUNTS.copy()

G_data_now = []
G_data_next = []

G_last_input_time = time.time()
G_last_mouse_position = mouse_controller.position

lock = threading.Lock()
lock2 = threading.Lock()


def _get_current_window_id():
    atom = display.get_atom("_NET_ACTIVE_WINDOW")
    window_prop = screen.root.get_full_property(atom, X.AnyPropertyType)

    if window_prop is None:
        return None

    # window_prop may contain more than one value, but it seems that it's always the first we want.
    # The second has in my attempts always been 0 or rubbish.
    window_id = window_prop.value[0]
    return window_id if window_id != 0 else None


def _get_window(window_id: int):
    return display.create_resource_object("window", window_id)


def get_window_name(window):
    """After some annoying debugging I resorted to pretty much copying selfspy.
    Source: https://github.com/gurgeh/selfspy/blob/8a34597f81000b3a1be12f8cde092a40604e49cf/selfspy/sniff_x.py#L165"""
    try:
        NET_WM_NAME = display.intern_atom("_NET_WM_NAME")
        UTF8_STRING = display.intern_atom("UTF8_STRING")
        d = window.get_full_property(NET_WM_NAME, UTF8_STRING)
    except Xlib.error.XError:
        # I strongly suspect window.get_wm_name() will also fail and we should return "unknown" right away.
        # But I don't know, so I pass the thing on, for now.
        d = None
    if d is None or d.format != 8:
        try:
            # Fallback.
            r = window.get_wm_name()
            if isinstance(r, str):
                return r
            else:
                return r.decode("latin1")  # WM_NAME with type=STRING.
        except Xlib.error.BadWindow:
            # logger.warning(
            #     f"Unable to get window property WM_NAME, got a {type(e).__name__} exception from Xlib"
            # )
            return UNKNOWN
    else:
        # Fixing utf8 issue on Ubuntu (https://github.com/gurgeh/selfspy/issues/133)
        # Thanks to https://github.com/gurgeh/selfspy/issues/133#issuecomment-142943681
        try:
            return d.value.decode("utf8")
        except UnicodeError:
            if isinstance(d.value, bytes):
                return d.value.decode("utf8", "ignore")
            else:
                return d.value.encode("utf8").decode("utf8", "ignore")


def get_window_class(window) -> str:
    cls = None

    try:
        cls = window.get_wm_class()
    except Xlib.error.BadWindow:
        pass

    if not cls:
        try:
            window = window.query_tree().parent
        except Xlib.error.BadWindow:
            # logger.warning(
            #     "Unable to get window query_tree().parent, got a BadWindow exception."
            # )
            return UNKNOWN
        except Xlib.error.XError:
            return UNKNOWN
        if window:
            return get_window_class(window)
        else:
            return UNKNOWN

    cls = cls[1]
    return cls


def get_current_window():
    """
    Returns the current window, or None if no window is active.
    """
    try:
        window_id = _get_current_window_id()
        if window_id is None:
            return None
        else:
            return _get_window(window_id)
    except Xlib.error.ConnectionClosedError:
        return None


def get_active_window_title():
    window = get_current_window()
    if window is None:
        name, cls = UNKNOWN, UNKNOWN
    else:
        cls = get_window_class(window)
        name = get_window_name(window)

    cls = cls.replace(LINE_SEP, "_")
    name = name.replace(LINE_SEP, "_")

    return f"{cls}{LINE_SEP}{name}"


def classify_key(key):
    if isinstance(key, keyboard.KeyCode):
        char = key.char
        # print(f"key: {char}")
        if char is None:
            return KEYS_INDICES["OTHERS"]
        if char.isalpha():
            return KEYS_INDICES["ALPHABETS"]
        if char.isdigit():
            return KEYS_INDICES["NUMBERS"]
        elif char in string.punctuation:
            return KEYS_INDICES["SPECHARS"]
        else:
            return KEYS_INDICES["OTHERS"]
    elif isinstance(key, Key):
        # print(f"kkey: {key}")
        if key in [Key.alt, Key.alt_l, Key.alt_r, Key.alt_gr]:
            return KEYS_INDICES["ALT"]
        elif key in [Key.shift, Key.shift_l, Key.shift_r]:
            return KEYS_INDICES["SHIFT"]
        elif key in [Key.ctrl, Key.ctrl_l, Key.ctrl_r]:
            return KEYS_INDICES["CTRL"]
        elif key in [Key.backspace, Key.delete]:
            return KEYS_INDICES["DELETE"]
        elif key in [Key.cmd, Key.cmd_l, Key.cmd_r]:
            return KEYS_INDICES["CMD"]
        elif key in [Key.down, Key.left, Key.right, Key.up]:
            return KEYS_INDICES["ARROWS"]
        elif key == Key.enter:
            return KEYS_INDICES["ENTER"]
        elif key == Key.space:
            return KEYS_INDICES["SPACE"]
        elif key == Key.tab:
            return KEYS_INDICES["TAB"]
        elif key == Key.esc:
            return KEYS_INDICES["ESC"]
        elif key in [
            Key.home,
            Key.end,
            Key.page_down,
            Key.page_up,
            Key.insert,
            Key.caps_lock,
        ]:
            return KEYS_INDICES["NAV"]
        elif key in [
            Key.f1,
            Key.f2,
            Key.f3,
            Key.f4,
            Key.f5,
            Key.f6,
            Key.f7,
            Key.f8,
            Key.f9,
            Key.f10,
            Key.f11,
            Key.f12,
            Key.f13,
            Key.f14,
            Key.f15,
            Key.f16,
            Key.f17,
            Key.f18,
            Key.f19,
            Key.f20,
        ]:
            return KEYS_INDICES["FUNC"]
        return KEYS_INDICES["OTHERS"]
    else:
        # print(f"okey: {key}")
        return KEYS_INDICES["OTHERS"]


def update_last_input():
    global G_last_input_time
    with lock:
        G_last_input_time = time.time()


def on_key_press(key):
    global G_key_counts_now
    update_last_input()
    index = classify_key(key)
    with lock:
        G_key_counts_now[index] += 1


def on_scroll(x, y, dx, dy):
    global G_key_counts_now
    update_last_input()
    with lock:
        G_key_counts_now[KEYS_INDICES["SCROLL"]] += 1


def on_click(x, y, button, pressed):
    global G_key_counts_now
    if pressed:
        update_last_input()
        with lock:
            if button == mouse.Button.left:
                G_key_counts_now[KEYS_INDICES["LCLICK"]] += 1
            elif button == mouse.Button.right:
                G_key_counts_now[KEYS_INDICES["RCLICK"]] += 1
            elif button == mouse.Button.middle:
                G_key_counts_now[KEYS_INDICES["MCLICK"]] += 1


def report_loop():
    global G_last_mouse_position, G_last_input_time, G_data_now, G_key_counts_now, G_key_counts_next

    while True:
        time.sleep(POLL_INTERVAL_SEC)

        current_mouse_position = mouse_controller.position
        if current_mouse_position != G_last_mouse_position:
            with lock:
                G_last_input_time = time.time()
            G_last_mouse_position = current_mouse_position
        with lock:
            is_idle = (time.time() - G_last_input_time) > IDLE_TIMEOUT_SEC

        idle_str = ""
        if is_idle:
            idle_str = IDLE

        title = get_active_window_title()
        window_title = f"{idle_str}{LINE_SEP}{title}"

        with lock:
            counts = G_key_counts_now
            G_key_counts_now = G_key_counts_next

        with lock2:
            if (
                len(G_data_now) == 0 or
                G_data_now[-1][1] != window_title or
                (G_data_now[-1][0][0] - G_data_now[-1][0][1]).total_seconds() > PRINT_INTERVAL_SEC
            ):
                G_data_now.append(([datetime.now(timezone.utc), datetime.now(timezone.utc)], window_title, INIT_COUNTS.copy()))

            G_data_now[-1][0][0] = datetime.now(timezone.utc)
            res = G_data_now[-1][2]
            for i in KEYS_INDICES.values():
                res[i] += counts[i]
                counts[i] = 0 #reset

        G_key_counts_next = counts


def print_loop():
    global G_data_now, G_data_next

    writeToFile([f"_started: {datetime.now(timezone.utc).strftime(LINE_TIME_FMT)}"])

    while True:
        time.sleep(PRINT_INTERVAL_SEC)

        with lock2:
            windows = G_data_now
            G_data_now = G_data_next

        lines = []
        for metadata, window, counts in windows:
            time_end = metadata[0].strftime(LINE_TIME_FMT)
            time_begin = metadata[1].strftime(LINE_TIME_FMT)
            stats = LINE_SEP.join([f"{kname}:{counts[KEYS_INDICES[key]]}" for key,kname in KEYS_ARR])
            lines.append(LINE_SEP.join([time_end, time_begin, window, stats]))
        writeToFile(lines)

        windows.clear()
        G_data_next = windows

def writeToFile(lines):
    now = datetime.now(timezone.utc)
    year = now.strftime("%Y")
    month = now.strftime("%m")
    day = now.strftime("%d")

    log_dir = log_base_dir / year / month
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"window-{year}.{month}.{day}-p{POLL_INTERVAL_SEC}.i{IDLE_TIMEOUT_SEC}.txt"
    with open(log_file, "a") as f:
        for line in lines:
            f.write(f"{line}\n")
            # print(l)

reporter_thread = threading.Thread(target=report_loop, daemon=True)
reporter_thread.start()

printer_thread = threading.Thread(target=print_loop, daemon=True)
printer_thread.start()

with (
    keyboard.Listener(on_press=on_key_press) as key_listener,
    mouse.Listener(on_click=on_click) as mouse_listener,
    mouse.Listener(on_scroll=on_scroll) as scroll_listener,
):
    key_listener.join()
    mouse_listener.join()
    scroll_listener.join()
