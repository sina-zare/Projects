# import itertools
# import sys
# import time
# import threading
#
# done = False
#
# def spinner():
#     for c in itertools.cycle(['|', '/', '--', '\\']):
#         if done:
#             break
#         sys.stdout.write(f'\rConnecting... {c}')
#         sys.stdout.flush()
#         time.sleep(0.1)
#     sys.stdout.write('\rConnected!     \n')
#
# t = threading.Thread(target=spinner)
# t.start()
#
# # Simulate unknown duration task
# time.sleep(7)
# done = True
#
# t.join()

from tqdm import tqdm
import time, threading

progress = 0
running = True

def fake_progress():
    global progress
    for i in tqdm(range(90), desc="Connecting...", ncols=75):
        if not running:
            break
        time.sleep(0.1)  # pseudo progress
        progress = i

thread = threading.Thread(target=fake_progress)
thread.start()

# Simulate the real operation
time.sleep(10)
running = False
thread.join()

# Complete to 100%
print("✅ Connection established!")
