import psutil
import winsound
import time


def check_battery(threshold=20, check_interval=30):
    while True:
        battery = psutil.sensors_battery()
        if battery:
            percent = battery.percent
            plugged = battery.power_plugged
            print(f"Battery: {percent}% {'(Charging)' if plugged else '(Discharging)'}")

            if percent < threshold and not plugged:
                print("Battery is low! Beeping...")
                winsound.Beep(500, 1000)  # 1000 Hz for 1 second
                winsound.Beep(500, 1000)
        else:
            print("Battery information not available.")

        time.sleep(check_interval)

check_battery()
