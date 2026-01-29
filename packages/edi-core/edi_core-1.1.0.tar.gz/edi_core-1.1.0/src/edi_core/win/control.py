import pyautogui


def write(text: str, interval: float = 0.1):
    pyautogui.write(text, interval)
