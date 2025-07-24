# agentic_llm_workflow/security.py
"""
Real-time Log Monitoring and Security Analysis
"""

import subprocess
import re
import os
from pathlib import Path
from collections import deque
import threading
import time
from datetime import datetime

class RealTimeLogMonitor:
    """Real-time NRF log monitoring with Gemini CLI analysis"""
    
    def __init__(self):
        self.log_path = "/var/log/open5gs/nrf.log"
        self.threshold = 100  # Log lines threshold for spike detection
        self.window_seconds = 10  # Time window in seconds
        self.recent_logs = deque()
        self.monitoring = False
        self.monitor_thread = None
        self.project_root = Path(os.getenv('PROJECT_ROOT', os.getcwd()))
        
        # Attack detection patterns
        self.attack_patterns = {
            'reconnaissance': [
                r'GET.*nnrf-disc.*nf-instances',
                r'discovery.*requester.*target',
                r'NF.*discovery.*request'
            ],
            'registration_flood': [
                r'PUT.*nnrf-nfm.*nf-instances',
                r'fake-nf-\d+',
                r'nfInstanceId.*fake',
                r'registration.*flood'
            ],
            'dos_attack': [
                r'too many requests',
                r'connection refused',
                r'timeout.*exceeded'
            ]
        }
        
        print(f"[*] Log Monitor initialized - watching {self.log_path}")
    
    def call_gemini_cli(self, prompt_text):
        """Call Gemini CLI using subprocess"""
        try:
            gemini_command = ['npx', '@google/gemini-cli', prompt_text]
            result = subprocess.run(gemini_command, capture_output=True, text=True, check=True, timeout=30)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"[!] Error running Gemini CLI: {e}")
            print(f"[!] Stderr: {e.stderr}")
            return f"Gemini CLI Error: {e.stderr}"
        except subprocess.TimeoutExpired:
            print("[!] Gemini CLI timeout - analysis took too long")
            return "Gemini CLI timeout - analysis took too long"
        except Exception as e:
            print(f"[!] Unexpected Gemini CLI error: {str(e)}")
            return f"Unexpected error: {str(e)}"
    
    def analyze_logs_with_gemini(self, log_lines):
        """Analyze logs using Gemini CLI"""
        print("[*] Sending logs to Gemini CLI for cybersecurity analysis...")
        
        logs_text = "\n".join(log_lines)
        prompt = f"""
        You are a cybersecurity expert analyzing Open5GS NRF logs from a 5G core network.
        Identify any abnormal behavior such as flooding, DoS, reconnaissance, or misconfiguration.
        
        Log data to analyze:
        {logs_text}
        
        Look specifically for:
        1. NRF registration flooding attacks (fake-nf patterns, excessive PUT requests)
        2. Reconnaissance patterns (excessive GET discovery requests)
        3. DoS or DDoS indicators (connection timeouts, too many requests)
        4. Fake NF registrations (suspicious nfInstanceId patterns)
        5. Unusual traffic patterns or spikes
        
        Respond in this exact format:
        THREAT_DETECTED: [yes/no]
        THREAT_TYPE: [reconnaissance/flood/fake_nf/dos/normal]
        SEVERITY: [low/medium/high/critical]
        RECOMMENDED_ACTION: [monitor/block_ip/restart_service/kill_processes]
        SOURCE_IP: [detected IP or unknown]
        DETAILS: [Brief explanation of findings]
        
        Be precise and focus on actionable security insights.
        """
        
        try:
            analysis = self.call_gemini_cli(prompt)
            return self.parse_gemini_analysis(analysis)
        except Exception as e:
            print(f"[!] Gemini analysis error: {e}")
            return {
                'threat_detected': False,
                'threat_type': 'error',
                'severity': 'low',
                'action': 'monitor',
                'source_ip': 'unknown',
                'details': f'Analysis error: {e}'
            }
    
    def parse_gemini_analysis(self, analysis_text):
        """Parse structured Gemini CLI analysis response"""
        result = {
            'threat_detected': False,
            'threat_type': 'normal',
            'severity': 'low',
            'action': 'monitor',
            'source_ip': 'unknown',
            'details': analysis_text
        }
        
        try:
            if 'THREAT_DETECTED: yes' in analysis_text.upper():
                result['threat_detected'] = True
            
            for threat_type in ['reconnaissance', 'flood', 'fake_nf', 'dos']:
                if f'THREAT_TYPE: {threat_type}' in analysis_text.lower():
                    result['threat_type'] = threat_type
                    break
            
            for severity in ['critical', 'high', 'medium', 'low']:
                if f'SEVERITY: {severity}' in analysis_text.lower():
                    result['severity'] = severity
                    break
            
            for action in ['kill_processes', 'restart_service', 'block_ip', 'monitor']:
                if f'RECOMMENDED_ACTION: {action}' in analysis_text.lower():
                    result['action'] = action
                    break
            
            ip_match = re.search(r'SOURCE_IP: (\d+\.\d+\.\d+\.\d+)', analysis_text)
            if ip_match:
                result['source_ip'] = ip_match.group(1)
            
            details_match = re.search(r'DETAILS: (.+)', analysis_text, re.IGNORECASE)
            if details_match:
                result['details'] = details_match.group(1).strip()
                
        except Exception as e:
            print(f"[!] Error parsing analysis: {e}")
        
        return result

    def monitor_log_realtime(self):
        """Real-time log monitoring with optimized analysis"""
        print(f"[*] Starting real-time monitoring of {self.log_path}")
        
        try:
            with open(self.log_path, "r") as f:
                f.seek(0, 2)
                
                while self.monitoring:
                    line = f.readline()
                    if not line:
                        time.sleep(0.1)
                        continue
                    
                    now = datetime.now()
                    self.recent_logs.append((now, line.strip()))
                    
                    while self.recent_logs and (now - self.recent_logs[0][0]).total_seconds() > self.window_seconds:
                        self.recent_logs.popleft()
                    
                    if len(self.recent_logs) > self.threshold:
                        print(f"[⚠️] Log spike detected: {len(self.recent_logs)} lines at {now.strftime('%H:%M:%S')}")
                        
                        log_lines = [entry[1] for entry in list(self.recent_logs)[-500:]]
                        analysis = self.analyze_logs_with_gemini(log_lines)
                        
                        if analysis['threat_detected']:
                            print(f"[🚨] THREAT DETECTED: {analysis['threat_type']} - {analysis['severity']}")
                            print(f"[🔍] Details: {analysis['details']}")
                            
                            if analysis['severity'] in ['high', 'critical']:
                                from self_healing import execute_defensive_action
                                execute_defensive_action(
                                    analysis['action'],
                                    analysis['threat_type'],
                                    analysis['source_ip']
                                )
                                
                                if analysis['threat_type'] == 'reconnaissance':
                                    from self_healing import kill_reconnaissance_processes
                                    kill_reconnaissance_processes()
                    
                    self.recent_logs.clear()
                        
        except FileNotFoundError:
            print(f"[!] Log file not found: {self.log_path}")
        except Exception as e:
            print(f"[!] Monitoring error: {e}")

    def start_monitoring(self):
        """Start background monitoring thread"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self.monitor_log_realtime)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            print("[✅] Real-time log monitoring started")
            return self.monitor_thread
        else:
            print("[*] Monitoring already active")
            return self.monitor_thread

    def stop_monitoring(self):
        """Stop monitoring"""
        if self.monitoring:
            self.monitoring = False
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=2)
            print("[🛑] Real-time log monitoring stopped")
