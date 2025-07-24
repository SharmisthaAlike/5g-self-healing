import time
import subprocess
from datetime import datetime
from collections import deque

from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate

# Paste your Groq API key here
GROQ_API_KEY = "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"  # Replace with your actual key

# Path to the NRF log
LOG_PATH = "/var/log/open5gs/nrf.log"

# Spike detection config
THRESHOLD = 100       # Number of log lines in the window to consider as spike
WINDOW_SECONDS = 10   # Time window in seconds

# Initialize Groq LLM
client = ChatGroq(
    api_key=GROQ_API_KEY,
    model="llama3-70b-8192"
)

# Set up prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", "You're a cybersecurity assistant analyzing NRF logs from a 5G core. Identify any abnormal behavior such as flooding, DoS, or misconfiguration."),
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


def analyze_with_groq(log_lines):
    print("[*] Sending logs to Groq for analysis...")
    logs = "\n".join(log_lines)
    try:
        result = chain.invoke({"logs": logs})
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
            f.seek(0, 2)  # Move to end of file

            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.1)
                    continue

                now = datetime.now()
                recent_logs.append((now, line.strip()))

                # Remove old lines outside the time window
                while recent_logs and (now - recent_logs[0][0]).total_seconds() > WINDOW_SECONDS:
                    recent_logs.popleft()

                if len(recent_logs) > THRESHOLD:
                    print(f"[⚠️] Spike detected: {len(recent_logs)} lines at {now.strftime('%H:%M:%S')}")
                    analyze_with_groq([entry[1] for entry in list(recent_logs)[-500:]])
                    recent_logs.clear()

    except KeyboardInterrupt:
        print("\n[+] Monitoring stopped.")
    except Exception as e:
        print(f"[!] Error reading log: {e}")


if __name__ == "__main__":
    monitor_log()

