# agentic_llm_workflow/open5gs_manager.py
import os
import subprocess
import sqlite3
import re
import json
import psutil
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging

load_dotenv()

class Open5GSMetricsCollector:
    """Real-time Open5GS metrics collection - better than Loki parsing!"""
    
    def __init__(self):
        self.project_root = Path(os.getenv('PROJECT_ROOT', os.getcwd()))
        self.db_path = self.project_root / "data" / "open5gs_metrics.db"
        self.log_path = Path(os.getenv('OPEN5GS_LOG_PATH', '/var/log/open5gs'))
        
        # Ensure directories exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        (self.project_root / "logs").mkdir(parents=True, exist_ok=True)
        
        self.setup_logging()
        self.setup_database()
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.project_root / "logs" / "metrics.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_database(self):
        """Initialize metrics database - compatible with original agent structure"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Original MAC_UE table for agent compatibility
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS MAC_UE (
                tstamp INTEGER PRIMARY KEY,
                pusch_snr REAL,
                dl_aggr_tbs INTEGER,
                ul_aggr_tbs INTEGER,
                dl_harq_round0 INTEGER,
                dl_harq_round1 INTEGER,
                dl_harq_round2 INTEGER,
                dl_harq_round3 INTEGER,
                p0_nominal INTEGER,
                dl_carrierBandwidth INTEGER,
                ul_carrierBandwidth INTEGER,
                att_tx INTEGER,
                att_rx INTEGER
            )
        """)
        
        # Real-time Open5GS metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS open5gs_metrics (
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                nrf_registered_nf_count INTEGER,
                amf_registered_ue_count INTEGER,
                smf_active_sessions INTEGER,
                upf_active_sessions INTEGER,
                upf_dl_packets INTEGER,
                upf_ul_packets INTEGER,
                upf_dl_bytes INTEGER,
                upf_ul_bytes INTEGER,
                cpu_usage_percent REAL,
                memory_usage_percent REAL,
                disk_usage_percent REAL
            )
        """)
        
        conn.commit()
        conn.close()
        self.logger.info(f"✅ Databases initialized at {self.db_path}")
    
    def get_open5gs_service_status(self):
        """Get status of all Open5GS services"""
        services = ['open5gs-nrfd', 'open5gs-amfd', 'open5gs-smfd', 'open5gs-upfd', 'open5gs-ausfd', 'open5gs-udrd', 'open5gs-pcfd', 'open5gs-nssfd']
        status = {}
        
        for service in services:
            try:
                result = subprocess.run(f"systemctl is-active {service}", shell=True, capture_output=True, text=True)
                status[service] = result.stdout.strip() == 'active'
            except:
                status[service] = False
        
        return status
    
    def parse_nrf_metrics(self):
        """Extract NRF metrics - registered network functions"""
        try:
            # Use Open5GS management interface if available, or parse logs
            result = subprocess.run("journalctl -u open5gs-nrfd --since '1 minute ago' --no-pager", 
                                  shell=True, capture_output=True, text=True)
            
            # Look for NF registration patterns
            nf_registrations = len(re.findall(r'NF registered', result.stdout))
            return nf_registrations
        except:
            return 0
    
    def parse_amf_metrics(self):
        """Extract AMF metrics - UE registrations and authentications"""
        try:
            result = subprocess.run("journalctl -u open5gs-amfd --since '1 minute ago' --no-pager", 
                                  shell=True, capture_output=True, text=True)
            
            # Count UE registrations
            ue_registrations = len(re.findall(r'UE registered', result.stdout))
            return ue_registrations
        except:
            return 0
    
    def parse_smf_upf_metrics(self):
        """Extract SMF/UPF session and traffic metrics"""
        try:
            # SMF sessions
            smf_result = subprocess.run("journalctl -u open5gs-smfd --since '1 minute ago' --no-pager", 
                                      shell=True, capture_output=True, text=True)
            active_sessions = len(re.findall(r'PDU session', smf_result.stdout))
            
            # UPF traffic (simplified - you can enhance this)
            upf_result = subprocess.run("journalctl -u open5gs-upfd --since '1 minute ago' --no-pager", 
                                      shell=True, capture_output=True, text=True)
            
            # Parse packet counts from logs (you'll need to adjust regex based on your logs)
            dl_packets = len(re.findall(r'DL.*packet', upf_result.stdout))
            ul_packets = len(re.findall(r'UL.*packet', upf_result.stdout))
            
            return {
                'active_sessions': active_sessions,
                'dl_packets': dl_packets,
                'ul_packets': ul_packets,
                'dl_bytes': dl_packets * 1500,  # Estimate
                'ul_bytes': ul_packets * 1500   # Estimate
            }
        except:
            return {'active_sessions': 0, 'dl_packets': 0, 'ul_packets': 0, 'dl_bytes': 0, 'ul_bytes': 0}
    
    def get_system_metrics(self):
        """Get system resource usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu_usage_percent': cpu_percent,
                'memory_usage_percent': memory.percent,
                'disk_usage_percent': disk.percent
            }
        except:
            return {'cpu_usage_percent': 0, 'memory_usage_percent': 0, 'disk_usage_percent': 0}
    
    def collect_all_metrics(self):
        """Collect comprehensive Open5GS metrics"""
        timestamp = datetime.now()
        
        # Get all metric components
        nrf_metrics = self.parse_nrf_metrics()
        amf_metrics = self.parse_amf_metrics()
        smf_upf_metrics = self.parse_smf_upf_metrics()
        system_metrics = self.get_system_metrics()
        
        # Combine into single metrics object
        metrics = {
            'timestamp': timestamp,
            'nrf_registered_nf_count': nrf_metrics,
            'amf_registered_ue_count': amf_metrics,
            'smf_active_sessions': smf_upf_metrics['active_sessions'],
            'upf_active_sessions': smf_upf_metrics['active_sessions'],  # Same as SMF for now
            'upf_dl_packets': smf_upf_metrics['dl_packets'],
            'upf_ul_packets': smf_upf_metrics['ul_packets'],
            'upf_dl_bytes': smf_upf_metrics['dl_bytes'],
            'upf_ul_bytes': smf_upf_metrics['ul_bytes'],
            **system_metrics
        }
        
        # Store in database
        self.store_metrics(metrics)
        
        # Also create MAC_UE entry for agent compatibility
        self.store_mac_ue_metrics(metrics)
        
        return metrics
    
    def store_metrics(self, metrics):
        """Store metrics in database"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        columns = ', '.join(metrics.keys())
        placeholders = ', '.join(['?' for _ in metrics])
        
        cursor.execute(f"""
            INSERT INTO open5gs_metrics ({columns}) 
            VALUES ({placeholders})
        """, list(metrics.values()))
        
        conn.commit()
        conn.close()
    
    def store_mac_ue_metrics(self, metrics):
        """Store in MAC_UE format for agent compatibility"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Map Open5GS metrics to MAC_UE format
        mac_ue_data = {
            'tstamp': int(metrics['timestamp'].timestamp() * 1000),
            'pusch_snr': 25.0 + (metrics['amf_registered_ue_count'] * 0.5),  # Simulated SNR
            'dl_aggr_tbs': metrics['upf_dl_bytes'],
            'ul_aggr_tbs': metrics['upf_ul_bytes'],
            'dl_harq_round0': metrics['upf_dl_packets'],
            'dl_harq_round1': 0,
            'dl_harq_round2': 0,
            'dl_harq_round3': 0,
            'p0_nominal': -90,  # Default values - agents can modify these
            'dl_carrierBandwidth': 51,
            'ul_carrierBandwidth': 51,
            'att_tx': 10,
            'att_rx': 10
        }
        
        columns = ', '.join(mac_ue_data.keys())
        placeholders = ', '.join(['?' for _ in mac_ue_data])
        
        cursor.execute(f"""
            INSERT OR REPLACE INTO MAC_UE ({columns}) 
            VALUES ({placeholders})
        """, list(mac_ue_data.values()))
        
        conn.commit()
        conn.close()
    
    def get_recent_metrics(self, minutes=5):
        """Get recent metrics for dashboard display"""
        conn = sqlite3.connect(str(self.db_path))
        
        # Get recent Open5GS metrics
        query = """
            SELECT * FROM open5gs_metrics 
            WHERE timestamp >= datetime('now', '-{} minutes')
            ORDER BY timestamp DESC
        """.format(minutes)
        
        import pandas as pd
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df