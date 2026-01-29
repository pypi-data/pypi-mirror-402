import subprocess
import time
import sys

def lock_and_sleep():
    try:
        # Locking GNOME screen
        subprocess.run([
            "dbus-send", "--type=method_call", "--dest=org.gnome.ScreenSaver", "/org/gnome/ScreenSaver", "org.gnome.ScreenSaver.Lock"
            ], check=True)

        time.sleep(1)

        # Sleep
        subprocess.run(["systemctl", "suspend"], check=True)
    
    except subprocess.CalledProcessError:
        print("Error: Please check if you use GNOME and can control systemctl")
        sys.exit(1)

if __name__ == "__main__":
    lock_and_sleep()
