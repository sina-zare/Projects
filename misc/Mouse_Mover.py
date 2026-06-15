import pyautogui
import random
import time

def move_mouse_randomly():
    screen_width, screen_height = pyautogui.size()
    while True:
        random_x = random.randint(0, screen_width - 1)
        random_y = random.randint(0, screen_height - 1)
        pyautogui.moveTo(random_x, random_y)
        time.sleep(50)

if __name__ == "__main__":
    move_mouse_randomly()
