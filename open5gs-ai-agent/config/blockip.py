import subprocess
import time
import re
from collections import defaultdict
from datetime import datetime, timedelta

# Configuration
THRESHOLD = 100              # Max allowed packets per IP in time window
WINDOW_SECONDS = 10          # Time window to check
BLOCKED_IPS = set()          # Track blocked IPs to avoid duplicates

def start_tcpdump():
    print("[*] Starting tcpdump to monitor port 7777 traffic...")
    # Run tcpdump command to capture only relevant packets
    return subprocess.Popen(
        ["sudo", "tcpdump", "-i", "any", "port", "7777", "-n"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True
    )

def extract_ip(line):
    match = re.search(r"IP (\d+\.\d+\.\d+\.\d+)\.\d+ > ", line)
    if match:
        return match.group(1)
    return None

def block_ip(ip):
    if ip in BLOCKED_IPS:
        return
    print(f"[⚠️] Blocking attacker IP: {ip}")
    subprocess.call(["sudo", "iptables", "-A", "INPUT", "-s", ip, "-p", "tcp", "--dport", "7777", "-j", "DROP"])
    BLOCKED_IPS.add(ip)

def monitor():
    proc = start_tcpdump()
    traffic_log = defaultdict(list)

    try:
        for line in proc.stdout:
            ip = extract_ip(line)
            if not ip:
                continue

            now = datetime.now()
            traffic_log[ip].append(now)

            # Remove old entries outside the window
            traffic_log[ip] = [t for t in traffic_log[ip] if (now - t).total_seconds() <= WINDOW_SECONDS]

            if len(traffic_log[ip]) > THRESHOLD:
                print(f"[🚨] Detected flood from {ip} ({len(traffic_log[ip])} packets in {WINDOW_SECONDS}s)")
                block_ip(ip)
                traffic_log[ip].clear()

    except KeyboardInterrupt:
        print("\n[+] Stopped monitoring.")
        proc.terminate()
    except Exception as e:
        print(f"[!] Error: {e}")
        proc.terminate()

if __name__ == "__main__":
    monitor()

