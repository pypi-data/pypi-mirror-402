import os
import sys
import time
import subprocess

# --- AUTO-INSTALLER BOOTLOADER ---
def install_requirements():
    try:
        import pick, tqdm
    except ImportError:
        print("📦 First run: Installing professional UI packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pick", "tqdm", "--quiet"])
        print("✅ UI Packages Ready.\n")

install_requirements()
from pick import pick
from tqdm import tqdm

# --- CORE FUNCTIONS ---
def log(message):
    timestamp = time.strftime("%H:%M:%S")
    print(f"[\033[94m{timestamp}\033[0m] {message}")

def fake_loading_bar(desc, duration=1.5):
    for _ in tqdm(range(100), desc=desc, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}', leave=False):
        time.sleep(duration/100)

def get_status():
    try:
        check = subprocess.check_output("docker ps --filter name=my-distro --format '{{.Status}}'", shell=True).decode()
        if not check:
            return "\033[91mOffline\033[0m"
        stats = subprocess.check_output("docker stats my-distro --no-stream --format '{{.CPUPerc}} | {{.MemUsage}}'", shell=True).decode().strip()
        return f"\033[92mOnline\033[0m ({stats})"
    except:
        return "\033[91mError Checking Status\033[0m"

def main():
    while True:
        os.system('clear')
        status = get_status()
        
        # FIXED TITLE: Using a multi-line string to ensure spacing works
        title = (
            f"--- axonserver Local OS Machine ---\n\n"
            f"Status: {status}\n\n"
            f"(⬆/⬇ Arrows to move, Enter to select)"
        )
        
        options = [
            'Ubuntu Desktop (With Audio Support)', 
#            'Kali Linux (Advanced Tools)', 
#            'Debian Lite (Standard)',
            'Check Performance Stats',
            'Stop & Shutdown All',
            'Exit'
        ]
        
        option, index = pick(options, title, indicator='=>', default_index=0)

        if option == 'Exit':
            break
            
        if option == 'Stop & Shutdown All':
            log("Shutting down services...")
            os.system("docker stop my-distro > /dev/null 2>&1")
            log("Cleanup complete.")
            time.sleep(1)
            continue

        if option == 'Check Performance Stats':
            print("\n" + "="*40)
            print(f"Current Stats: {get_status()}")
            input("\nPress Enter to return to menu...")
            continue

        # --- UPDATED IMAGE MAPPING (With Audio Ports) ---
        # 0 = Webtop (Port 3000), 1 = Kali (Port 6901), 2 = Debian (Port 80)
        images = {
            0: {"img": "linuxserver/webtop:ubuntu-xfce", "port": 3000},
            1: {"img": "kasmweb/kali-linux-coder-x86_64:1.14.0", "port": 6901},
            2: {"img": "dorowu/ubuntu-desktop-lxde-vnc:latest", "port": 80}
        }
        
        selected = images[index]
        image_name = selected["img"]
        internal_port = selected["port"]

        print("\n" + "="*40)
        log(f"axonserver System Boot: Preparing {option}...")
        
        os.system("docker stop my-distro > /dev/null 2>&1")
        
        log(f"Pulling {image_name}...")
        os.system(f"docker pull {image_name} > /dev/null 2>&1")
        
        fake_loading_bar("Please wait...", duration=5)
        # Dynamic port mapping based on the image's needs
        os.system(f"docker run -d -p 8080:{internal_port} --name my-distro --rm {image_name}")
        
        fake_loading_bar("Configuring VNC Bridge...", duration=5)
        
        print("="*40)
        print(f"\n✅ {option.upper()} IS LIVE!")
        print("👉 Connect to port 8080 to enter VM")
        if internal_port == 3000:
            print("🔊 AUDIO: Use the pull-out menu on the left side of the screen")
        print("="*40)
        input("\nPress Enter to return to menu...")

if __name__ == "__main__":
    main()