import time
import subprocess
import re
from datetime import datetime
from collections import deque, defaultdict
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate

# --- Config ---
THRESHOLD = 200
WINDOW_SECONDS = 10
GROQ_LINE_LIMIT = 50
LINE_TRUNCATE_LEN = 200
MAX_SPIKES_BEFORE_BLOCK = 3
GROQ_API_KEY = "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"
TCPDUMP_COMMAND = ["sudo", "tcpdump", "-l", "-n", "tcp port 7777"]

# --- Tracking ---
spike_counter = defaultdict(int)
blocked_ips = set()
packet_log = deque()

# --- Langchain/Groq Setup ---
client = ChatGroq(api_key=GROQ_API_KEY, model="llama3-8b-8192")
prompt = ChatPromptTemplate.from_messages([
    ("system", """
You are a cybersecurity expert analyzing TCP traffic logs to the 5G NRF service (port 7777).
Your job is to:
1. Detect attacks like NF flooding, DoS, and fake registration bursts.
2. Identify responsible IPs or behaviors.
3. Recommend only necessary self-healing actions:
   - Kill curl flooders
   - Restart NRF
   - Block IP (only if repeat offender)
   - Enable TCP rate limit
   - Log evidence

Respond in this format:
Root Cause:
Evidence Summary:
Recommended Fixes:
"""),
    ("human", "{logs}")
])
chain = prompt | client

# --- Healing Actions ---
def kill_nrf_flood():
    subprocess.call(["pkill", "-f", "curl.*nnrf-nfm/v1/nf-instances/fake-nf"])

def restart_nrf():
    subprocess.call(["sudo", "systemctl", "restart", "open5gs-nrfd"])

def block_ip(ip):
    if ip in blocked_ips:
        return
    print(f"[🚫] Blocking IP: {ip}")
    subprocess.call(["sudo", "iptables", "-A", "INPUT", "-s", ip, "-p", "tcp", "--dport", "7777", "-j", "DROP"])
    blocked_ips.add(ip)

# --- IP Parser from tcpdump line ---
def extract_ip(line):
    match = re.search(r"IP (\d+\.\d+\.\d+\.\d+)\.\d+ > ", line)
    return match.group(1) if match else None

# --- Groq Analysis ---
def analyze_with_groq(log_lines, timestamp):
    limited_lines = log_lines[-GROQ_LINE_LIMIT:]
    safe_logs = [line[:LINE_TRUNCATE_LEN] for line in limited_lines]
    logs_str = f"[{timestamp}] Last {len(safe_logs)} TCP packets:\n" + "\n".join(safe_logs)

    try:
        result = chain.invoke({"logs": logs_str})
        analysis = result.content.strip()
        print("\n[🔍] Groq Analysis:\n" + analysis)

        if any(word in analysis.lower() for word in ["flood", "dos", "denial"]):
            kill_nrf_flood()
            restart_nrf()

            ip_counts = defaultdict(int)
            for line in log_lines:
                ip = extract_ip(line)
                if ip:
                    ip_counts[ip] += 1

            for ip, count in ip_counts.items():
                spike_counter[ip] += 1
                print(f"[!] {ip} has spiked {spike_counter[ip]} time(s)")
                if spike_counter[ip] >= MAX_SPIKES_BEFORE_BLOCK:
                    block_ip(ip)
    except Exception as e:
        print(f"[!] Groq error: {e}")

# --- Main Monitor ---
def monitor_tcpdump():
    print("[*] Monitoring TCP traffic on port 7777 using tcpdump...\n")

    process = subprocess.Popen(
        TCPDUMP_COMMAND,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True
    )

    try:
        for line in process.stdout:
            now = datetime.now()
            line = line.strip()
            packet_log.append((now, line))

            while packet_log and (now - packet_log[0][0]).total_seconds() > WINDOW_SECONDS:
                packet_log.popleft()

            if len(packet_log) > THRESHOLD:
                ts = now.strftime('%Y-%m-%d %H:%M:%S')
                print(f"[⚠️] Spike detected: {len(packet_log)} packets at {ts}")
                recent_lines = [entry[1] for entry in packet_log]
                analyze_with_groq(recent_lines, ts)
                packet_log.clear()

    except KeyboardInterrupt:
        print("\n[+] Monitoring stopped.")
        process.terminate()
    except Exception as e:
        print(f"[!] Error: {e}")
        process.terminate()

if __name__ == "__main__":
    monitor_tcpdump()

