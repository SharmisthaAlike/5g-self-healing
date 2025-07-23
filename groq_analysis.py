#handles Groq's context length error
import time
import subprocess
from datetime import datetime
from collections import deque

from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate

# paste groq key
GROQ_API_KEY = "xxxx"


LOG_PATH = "/var/log/open5gs/nrf.log"


THRESHOLD = 200  # lines in window
WINDOW_SECONDS = 10
GROQ_LINE_LIMIT = 50
LINE_TRUNCATE_LEN = 200


client = ChatGroq(
    api_key=GROQ_API_KEY,
    model="llama3-8b-8192"
)


prompt = ChatPromptTemplate.from_messages([
    ("system",
     """You are a cybersecurity expert analyzing real-time NRF logs from a 5G core network.
Your job is to:
1. Identify abnormal behavior such as NF registration flooding, Denial of Service (DoS), or misconfiguration.
2. Determine the probable cause of any spike.
3. Recommend **specific** self-healing actions, such as:
   - killing attacker processes
   - restarting NRF
   - applying TCP rate limiting (e.g., iptables rules)
   - logging suspicious IPs or endpoints
   - blocking local abuse of curl or HTTP/2
4. Output your findings in a clear format:
   - Root Cause
   - Evidence from logs (summarized)
   - Recommended Fixes

Return full analysis based on logs provided.
"""
     ),
    ("human", "{logs}")
])

chain = prompt | client


def kill_nrf_flood():
    print("[⚠️] Attempting to kill suspected NRF flood processes...")
    subprocess.call(["pkill", "-f", "curl.*nnrf-nfm/v1/nf-instances/fake-nf"])
    print("[✓] Attack processes terminated.")


def restart_nrf():
    print("[↻] Restarting Open5GS NRF service...")
    subprocess.call(["sudo", "systemctl", "restart", "open5gs-nrfd"])
    print("[✓] NRF service restarted.")


def analyze_with_groq(log_lines, timestamp):
    print("[*] Sending logs to Groq for analysis...")

    #limiting the logs
    limited_lines = log_lines[-GROQ_LINE_LIMIT:]
    safe_logs = [line[:LINE_TRUNCATE_LEN] for line in limited_lines]
    logs_str = f"[{timestamp}] Last {len(safe_logs)} lines:\n" + "\n".join(safe_logs)

    try:
        result = chain.invoke({"logs": logs_str})
        print("\n[🔍] Groq Analysis:\n" + result.content.strip())

        if any(keyword in result.content.lower() for keyword in ["flood", "dos", "denial of service"]):
            kill_nrf_flood()
            restart_nrf()

    except Exception as e:
        print(f"[!] Groq error: {e}")


def monitor_log():
    print("[*] Monitoring NRF log for spikes...\n")
    recent_logs = deque()

    try:
        with open(LOG_PATH, "r") as f:
            f.seek(0, 2)  # Seek to end

            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.1)
                    continue

                now = datetime.now()
                recent_logs.append((now, line.strip()))

                
                while recent_logs and (now - recent_logs[0][0]).total_seconds() > WINDOW_SECONDS:
                    recent_logs.popleft()

                if len(recent_logs) > THRESHOLD:
                    print(f"[⚠️] Spike detected: {len(recent_logs)} lines at {now.strftime('%H:%M:%S')}")
                    analyze_with_groq([entry[1] for entry in recent_logs], now.strftime('%Y-%m-%d %H:%M:%S'))
                    recent_logs.clear()

    except KeyboardInterrupt:
        print("\n[+] Monitoring stopped by user.")
    except Exception as e:
        print(f"[!] Error during log monitoring: {e}")


if __name__ == "__main__":
    monitor_log()

