import psutil
import time
import winsound  # For beeping on Windows

def check_battery_level():
    """
    Checks the battery level and beeps if it's below 20%.
    """
    battery = psutil.sensors_battery()

    if battery is None:
        print("Battery information not available.")
        return

    percent = battery.percent

    if percent < 20:
        print(f"Battery level is low: {percent}%")
        # Beep using winsound (Windows only)
        winsound.Beep(2500, 1000)  # Frequency (Hz), Duration (ms)
        # You can adjust the frequency and duration as needed

def main():
    """
    Main function to continuously check the battery level.
    """
    try:
        while True:
            check_battery_level()
            time.sleep(60)  # Check every 60 seconds (adjust as needed)
    except KeyboardInterrupt:
        print("Script stopped.")

if __name__ == "__main__":
    main()