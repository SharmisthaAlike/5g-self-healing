# agentic_llm_workflow/self_healing.py
"""
Self-Healing Actions with Integrated blockip.py and nrf_defense.py functionality
"""

import subprocess
import time
import re
from collections import defaultdict
from datetime import datetime

class IntegratedSelfHealing:
    """Integrated self-healing combining blockip.py and nrf_defense.py"""
    
    def __init__(self):
        self.THRESHOLD = 100
        self.WINDOW_SECONDS = 10
        self.BLOCKED_IPS = set()
        print("[*] Self-healing system initialized")
    
    def kill_nrf_flood_processes(self):
        """Kill flood processes - fixed patterns"""
        print("[⚠️] Killing NRF flood processes...")
        try:
            # Kill by curl command targeting NRF
            subprocess.call(["pkill", "-f", "curl.*nnrf-nfm"])
            subprocess.call(["pkill", "-f", "curl.*7777"])
            subprocess.call(["pkill", "-f", "nf-instances"])
            subprocess.call(["pkill", "-f", "curl.*nnrf-nfm/v1/nf-instances/fake-nf"])
            # Kill by script name if running
            subprocess.call(["pkill", "-f", "flood"])
            print("[✓] Attack processes terminated")
        except Exception as e:
            print(f"[!] Error: {e}")
    
    def restart_nrf_service(self):
        """Restart NRF service (from nrf_defense.py)"""
        print("[↻] Restarting Open5GS NRF service...")
        try:
            subprocess.call(["sudo", "systemctl", "restart", "open5gs-nrfd"])
            time.sleep(3)
            print("[✓] NRF service restarted")
        except Exception as e:
            print(f"[!] Error restarting NRF: {e}")
    
    def block_ip(self, ip):
        """Block IP using iptables (from blockip.py)"""
        if ip in self.BLOCKED_IPS or ip == 'unknown':
            return
        
        print(f"[⚠️] Blocking IP: {ip}")
        try:
            subprocess.call([
                "sudo", "iptables", "-A", "INPUT", "-s", ip, 
                "-p", "tcp", "--dport", "7777", "-j", "DROP"
            ])
            self.BLOCKED_IPS.add(ip)
            print(f"[✓] IP {ip} blocked")
        except Exception as e:
            print(f"[!] Error blocking IP: {e}")
    
    def apply_rate_limiting(self):
        """Apply rate limiting for port 7777"""
        print("[🛡️] Applying rate limiting...")
        try:
            subprocess.call([
                "sudo", "iptables", "-A", "INPUT", "-p", "tcp", 
                "--dport", "7777", "-m", "connlimit", "--connlimit-above", "10", 
                "-j", "REJECT", "--reject-with", "tcp-reset"
            ])
            print("[✓] Rate limiting applied")
        except Exception as e:
            print(f"[!] Error applying rate limiting: {e}")
    
    def execute_defensive_action(self, action, threat_type, source_ip='unknown'):
        """Execute defensive actions based on threat analysis"""
        print(f"[🔧] Executing: {action} for {threat_type}")
        
        if action == 'kill_processes' or 'flood' in threat_type:
            self.kill_nrf_flood_processes()
            
        if action == 'restart_service' or threat_type == 'dos_attack':
            self.restart_nrf_service()
            
        if action == 'block_ip' and source_ip != 'unknown':
            self.block_ip(source_ip)
            
        if action == 'full_defense' or threat_type == 'critical':
            self.kill_nrf_flood_processes()
            time.sleep(2)
            self.restart_nrf_service()
            self.apply_rate_limiting()
            
        print(f"[✅] Defensive action {action} completed")

# Global instance for use across modules
self_healing_system = IntegratedSelfHealing()

def execute_defensive_action(action, threat_type, source_ip='unknown'):
    """Global function for defensive actions"""
    return self_healing_system.execute_defensive_action(action, threat_type, source_ip)