import socket
import threading
import time
import os
import re
import subprocess
from colorama import Fore, Style, init

init(autoreset=True)

print(Fore.CYAN + r"""
  /\    \         /\      /  \    \       /  \    \  _____   _____   ________
 /    \    \     /    \    \/     \ /     \ /   _____|
/      \    \   /      \    |  |  |  |  |  |   |__
|      |    |  |      |    |  |  |  |  |  |   __|
\______|____|   \______|____|__|__|  |__|  |_____|

             """ + Fore.MAGENTA + "advgorscan v2" + Style.RESET_ALL)

print(Fore.YELLOW + "\nSelect a scan option:")
print("1. Scan Website by Domain Name")
print("2. Scan Your Own Router")
print("3. Scan Custom Target IP")

choice = input(Fore.CYAN + "Which scan do you want to perform? (1/2/3): ").strip()

# Thread-safe print lock
print_lock = threading.Lock()

def get_own_ip():
    try:
        output = subprocess.check_output("ifconfig", shell=True).decode()
        match = re.search(r'inet (?:addr:)?(\d+\.\d+\.\d+\.\d+)', output)
        if match:
            return match.group(1)
    except Exception:
        pass
    return None

def scan_port(ip, port, verbose):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    try:
        result = s.connect_ex((ip, port))
        with print_lock:
            if result == 0:
                print(Fore.GREEN + f"[+] Port {port} is open!")
            elif verbose:
                print(Fore.RED + f"[-] Port {port} is closed")
    except:
        pass
    finally:
        s.close()

def valid_ip(ip):
    pattern = re.compile(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$")
    return pattern.match(ip)

def valid_domain(domain):
    pattern = re.compile(
        r"^(?:[a-zA-Z0-9-]{1,63}\.)+[a-zA-Z]{2,6}$"
    )
    return pattern.match(domain)

def start_scan(ip):
    try:
        start_port = int(input("Enter start port (1-65535): "))
        end_port = int(input("Enter end port (1-65535): "))
        if not (1 <= start_port <= 65535 and 1 <= end_port <= 65535):
            raise ValueError

        verbose_input = input("Enable verbose mode? (y/n): ").strip().lower()
        verbose = verbose_input == 'y'

        print(Fore.BLUE + f"\nScanning {ip} from port {start_port} to {end_port}...\n")
        threads = []

        # Select threading level
        print("Select threading level:")
        print("1. Level 1 (slow)")
        print("2. Level 2 (medium)")
        print("3. Level 3 (fast)")
        level = input("Choose (1/2/3): ").strip()
        delay = 0.09
        max_threads = 30 if level == '1' else 100 if level == '2' else 200

        sem = threading.Semaphore(max_threads)

        for port in range(start_port, end_port + 1):
            sem.acquire()

            t = threading.Thread(target=lambda p=port: [scan_port(ip, p, verbose), sem.release()])
            threads.append(t)
            t.start()
            time.sleep(delay)

        for t in threads:
            t.join()

    except ValueError:
        print(Fore.RED + "Invalid port range entered.")

# Handle choice
if choice == '1':
    domain = input("Enter domain name (e.g., google.com): ").strip()
    if not valid_domain(domain):
        print(Fore.RED + "Invalid domain name.")
    else:
        try:
            ip = socket.gethostbyname(domain)
            start_scan(ip)
        except socket.gaierror:
            print(Fore.RED + "Could not resolve domain. Please check the name.")

elif choice == '2':
    print("Scanning your own router...")
    own_ip = get_own_ip()
    if own_ip:
        print(Fore.GREEN + f"Detected IP: {own_ip}")
        start_scan(own_ip)
    else:
        print(Fore.RED + "Could not detect router IP. Try manual input instead.")

elif choice == '3':
    ip = input("Enter target IP: ").strip()
    if not valid_ip(ip):
        print(Fore.RED + "Invalid IP address.")
    else:
        start_scan(ip)

else:
    print(Fore.RED + "Invalid option.")
