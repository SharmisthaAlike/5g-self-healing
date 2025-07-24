import time
import subprocess
import re
from datetime import datetime
from collections import deque, defaultdict

from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate

# Groq API Key
GROQ_API_KEY = "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"

# Paths and constants
LOG_PATH = "/var/log/open5gs/nrf.log"
THRESHOLD = 200
WINDOW_SECONDS = 10
GROQ_LINE_LIMIT = 50
LINE_TRUNCATE_LEN = 200
MAX_SPIKES_BEFORE_BLOCK = 3

# Track IP spike frequency and blocked IPs
spike_counter = defaultdict(int)
blocked_ips = set()

# Groq LLM setup
client = ChatGroq(api_key=GROQ_API_KEY, model="llama3-8b-8192")
prompt = ChatPromptTemplate.from_messages([
    ("system", """
You are a cybersecurity expert analyzing real-time NRF logs from a 5G core network.

Your job is to:
1. Detect attacks like NF registration flooding or misconfiguration.
2. Determine root cause of a spike.
3. Recommend precise self-healing actions (choose only what’s relevant):
   - kill attacker processes
   - restart NRF
   - apply TCP rate limiting (iptables)
   - block IP (only if same IP spikes > 2 times)
   - disable curl abuse
   - log IPs

Respond in this format:
Root Cause:
Evidence Summary:
Recommended Fixes:
    """),
    ("human", "{logs}")
])
chain = prompt | client

def kill_nrf_flood():
    print("[⚠️] Killing flood curl processes...")
    subprocess.call(["pkill", "-f", "curl.*nnrf-nfm/v1/nf-instances/fake-nf"])
    print("[✓] Flood processes terminated.")

def restart_nrf():
    print("[↻] Restarting Open5GS NRF service...")
    subprocess.call(["sudo", "systemctl", "restart", "open5gs-nrfd"])
    print("[✓] NRF restarted.")

def block_ip(ip):
    if ip in blocked_ips:
        return
    print(f"[🚫] Blocking IP: {ip}")
    subprocess.call(["sudo", "iptables", "-A", "INPUT", "-s", ip, "-p", "tcp", "--dport", "7777", "-j", "DROP"])
    blocked_ips.add(ip)
    print(f"[✓] {ip} blocked via iptables.")

def extract_ips_from_logs(log_lines):
    ip_pattern = r"(\d+\.\d+\.\d+\.\d+)"
    ip_hits = defaultdict(int)
    for line in log_lines:
        match = re.search(ip_pattern, line)
        if match:
            ip_hits[match.group(1)] += 1
    return ip_hits

def analyze_with_groq(log_lines, timestamp):
    print("[*] Sending logs to Groq for analysis...")
    limited_lines = log_lines[-GROQ_LINE_LIMIT:]
    safe_logs = [line[:LINE_TRUNCATE_LEN] for line in limited_lines]
    logs_str = f"[{timestamp}] Last {len(safe_logs)} lines:\n" + "\n".join(safe_logs)

    try:
        result = chain.invoke({"logs": logs_str})
        analysis = result.content.strip()
        print("\n[🔍] Groq Analysis:\n" + analysis)

        if any(keyword in analysis.lower() for keyword in ["flood", "dos", "denial of service"]):
            # Execute basic healing steps
            kill_nrf_flood()
            restart_nrf()

            # Extract and handle IPs
            ips = extract_ips_from_logs(log_lines)
            for ip, count in ips.items():
                spike_counter[ip] += 1
                print(f"[!] Spike count for {ip}: {spike_counter[ip]}")
                if spike_counter[ip] >= MAX_SPIKES_BEFORE_BLOCK:
                    block_ip(ip)

    except Exception as e:
        print(f"[!] Groq error: {e}")

def monitor_log():
    print("[*] Monitoring NRF logs...\n")
    recent_logs = deque()

    try:
        with open(LOG_PATH, "r") as f:
            f.seek(0, 2)

            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.1)
                    continue

                now = datetime.now()
                recent_logs.append((now, line.strip()))

                # Remove old entries
                while recent_logs and (now - recent_logs[0][0]).total_seconds() > WINDOW_SECONDS:
                    recent_logs.popleft()

                if len(recent_logs) > THRESHOLD:
                    ts = now.strftime('%Y-%m-%d %H:%M:%S')
                    print(f"[⚠️] Spike detected: {len(recent_logs)} lines at {ts}")
                    analyze_with_groq([entry[1] for entry in recent_logs], ts)
                    recent_logs.clear()

    except KeyboardInterrupt:
        print("\n[+] Monitoring stopped.")
    except Exception as e:
        print(f"[!] Error: {e}")

if __name__ == "__main__":
    monitor_log()


