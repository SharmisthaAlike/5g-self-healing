# agentic_llm_workflow/monitoring.py
"""
Continuous System Monitoring
"""

import psutil
import sqlite3
import threading
import time
from collections import deque
from datetime import datetime
from pathlib import Path
import os
import pandas as pd

class ContinuousSystemMonitor:
    """Continuous CPU and memory monitoring for 5 minutes"""
    
    def __init__(self):
        self.monitoring = False
        self.monitor_thread = None
        self.data_points = deque(maxlen=300)  # 5 minutes at 1-second intervals
        self.db_path = Path(os.getenv('PROJECT_ROOT', os.getcwd())) / "data" / "open5gs_metrics.db"
        self.setup_database()
        print("[*] Continuous system monitor initialized")
    
    def setup_database(self):
        """Setup database for system metrics"""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    cpu_percent REAL,
                    memory_percent REAL,
                    memory_used_gb REAL,
                    memory_total_gb REAL,
                    disk_percent REAL
                )
            """)
            
            conn.commit()
            conn.close()
            print("[✅] System metrics database ready")
        except Exception as e:
            print(f"[!] Database setup error: {e}")
    
    def collect_system_metrics(self):
        """Collect current system metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            timestamp = datetime.now()
            metrics = {
                'timestamp': timestamp,
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_used_gb': memory.used / (1024**3),
                'memory_total_gb': memory.total / (1024**3),
                'disk_percent': disk.percent
            }
            
            self.data_points.append(metrics)
            self.store_metrics(metrics)
            return metrics
        except Exception as e:
            print(f"[!] Error collecting metrics: {e}")
            return None
    
    def store_metrics(self, metrics):
        """Store metrics in database"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO system_metrics 
                (timestamp, cpu_percent, memory_percent, memory_used_gb, memory_total_gb, disk_percent)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                metrics['timestamp'], metrics['cpu_percent'], metrics['memory_percent'],
                metrics['memory_used_gb'], metrics['memory_total_gb'], metrics['disk_percent']
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[!] Error storing metrics: {e}")
    
    def get_recent_metrics(self, minutes=5):
        """Get recent system metrics from database"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            query = f"""
                SELECT * FROM system_metrics 
                WHERE timestamp >= datetime('now', '-{minutes} minutes')
                ORDER BY timestamp DESC
                LIMIT 300
            """
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except Exception as e:
            print(f"[!] Error getting metrics: {e}")
            return pd.DataFrame()
    
    def continuous_monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                self.collect_system_metrics()
                time.sleep(1)
            except Exception as e:
                print(f"[!] Monitoring error: {e}")
                time.sleep(5)
    
    def start_monitoring(self):
        """Start continuous monitoring"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self.continuous_monitoring_loop)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            print("[✅] Continuous system monitoring started")
            return self.monitor_thread
        return self.monitor_thread
    
    def stop_monitoring(self):
        """Stop monitoring"""
        if self.monitoring:
            self.monitoring = False
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=2)
            print("[🛑] Continuous system monitoring stopped")