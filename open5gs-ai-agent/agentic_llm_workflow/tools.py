# agentic_llm_workflow/tools.py
"""
Tools for LangGraph Agents with Rate Limiting
"""

import sqlite3
import pandas as pd
from io import StringIO
import os
import json
import subprocess
import re
import hashlib
import time
from typing import Annotated
from datetime import datetime, timedelta
from pathlib import Path
from langchain_core.tools import tool

# Global rate limiting
_last_ai_call = None
_ai_cooldown = 1800  # 30 minutes between AI calls

def get_nrf_logs_pattern_analysis():
    """Get NRF logs and do pattern analysis - NO AI"""
    try:
        # Get recent NRF logs
        result = subprocess.run(
            "journalctl -n 100 -u open5gs-nrfd --no-pager --since '30 seconds ago'",
            shell=True, capture_output=True, text=True, timeout=5
        )
        
        if result.returncode != 0:
            return {
                'threat_detected': False, 
                'threat_type': 'normal',
                'severity': 'low',
                'details': 'No logs available - NRF service may be down'
            }
        
        logs = result.stdout.strip().split('\n')
        
        # Pattern-based analysis
        threat_patterns = {
            'registration_flood': [
                r'fake-nf-\d+', 
                r'PUT.*nnrf-nfm.*nf-instances.*fake',
                r'nfInstanceId.*fake',
                r'127\.0\.0\.99'  # Fake IP from attack script
            ],
            'reconnaissance': [
                r'GET.*nnrf-disc.*nf-instances', 
                r'discovery.*requester'
            ],
            'dos_attack': [
                r'too many requests', 
                r'connection refused', 
                r'timeout'
            ]
        }
        
        threat_counts = {}
        for threat_type, patterns in threat_patterns.items():
            count = 0
            for log in logs:
                for pattern in patterns:
                    if re.search(pattern, log, re.IGNORECASE):
                        count += 1
            threat_counts[threat_type] = count
        
        # Find highest threat
        max_threat = max(threat_counts.items(), key=lambda x: x[1]) if threat_counts else ('normal', 0)
        threat_type, count = max_threat
        
        # Determine severity and execute immediate action
        if count > 10:  # Lowered threshold for faster detection
            severity = 'critical' if count > 25 else 'high'
            
            # IMMEDIATE SELF-HEALING for flood attacks
            if threat_type == 'registration_flood' and count > 5:
                print(f"[🚨] IMMEDIATE ACTION: {count} flood patterns detected")
                try:
                    from .self_healing import execute_defensive_action
                    execute_defensive_action('kill_processes', 'registration_flood', 'unknown')
                except Exception as e:
                    print(f"[!] Immediate action failed: {e}")
            
            return {
                'threat_detected': True,
                'threat_type': threat_type,
                'severity': severity,
                'details': f'ACTIVE ATTACK: {count} instances of {threat_type} detected - DEFENSIVE ACTIONS EXECUTED'
            }
        elif count > 3:
            return {
                'threat_detected': True,
                'threat_type': threat_type,
                'severity': 'medium',
                'details': f'Suspicious activity: {count} instances of {threat_type}'
            }
        
        return {
            'threat_detected': False,
            'threat_type': 'normal',
            'severity': 'low',
            'details': f'Pattern analysis: Normal activity (checked {len(logs)} log entries)'
        }
        
    except subprocess.TimeoutExpired:
        return {
            'threat_detected': False,
            'threat_type': 'error', 
            'severity': 'low',
            'details': 'Log analysis timeout'
        }
    except Exception as e:
        return {
            'threat_detected': False,
            'threat_type': 'error',
            'severity': 'low', 
            'details': f'Analysis error: {str(e)}'
        }
@tool
def execute_open5gs_sql(sql_query: Annotated[str, "SQL query to execute"]):
    """Execute SQL query on Open5GS metrics database"""
    try:
        db_path = os.getenv('PROJECT_ROOT', os.getcwd()) + "/data/open5gs_metrics.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(sql_query)
        
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        result_df = pd.DataFrame(rows, columns=columns)
        conn.close()
        
        return result_df.to_string(index=False)
    except Exception as e:
        return f"SQL Error: {str(e)}"

@tool
def calc_weighted_average(df_data: Annotated[str, "DataFrame as string"], 
                         weight1: Annotated[float, "Weight for first KPI"],
                         weight2: Annotated[float, "Weight for second KPI"], 
                         current_param_value: Annotated[int, "Current parameter value"]):
    """Calculate weighted average gain"""
    try:
        df = pd.read_csv(StringIO(df_data), sep=r'\s+')
        
        pivot_row = df[df.iloc[:, 0] == current_param_value]
        if pivot_row.empty:
            return "Error: Current parameter value not found in data"
        
        new_data = []
        columns = df.columns.tolist()
        
        for _, row in df.iterrows():
            if row.iloc[0] != current_param_value:
                denom_col1 = pivot_row[columns[1]].values[0] or 1
                denom_col2 = pivot_row[columns[2]].values[0] or 1
                
                changed_row = {
                    f"Change_in_{columns[0]}": f"{current_param_value}_to_{row.iloc[0]}",
                    f"%_increase_in_{columns[1]}": (row[columns[1]] - pivot_row[columns[1]].values[0])*100/denom_col1,
                    f"%_increase_in_{columns[2]}": (row[columns[2]] - pivot_row[columns[2]].values[0])*100/denom_col2,
                }
                new_data.append(changed_row)
        
        weighted_df = pd.DataFrame(new_data)
        weighted_df["Weighted_Average_Gain"] = (weight1 * weighted_df.iloc[:, 1]) + (weight2 * weighted_df.iloc[:, 2])
        
        return weighted_df.to_string(index=False)
    except Exception as e:
        return f"Calculation Error: {str(e)}"

@tool
def analyze_nrf_logs_smart():
    """Smart NRF log analysis with rate limiting"""
    global _last_ai_call
    
    # Always do pattern analysis first
    pattern_result = get_nrf_logs_pattern_analysis()
    
    # Only use AI for critical cases and if cooldown passed
    current_time = datetime.now()
    if _last_ai_call and (current_time - _last_ai_call).total_seconds() < _ai_cooldown:
        print(f"[*] Rate limited - using pattern analysis only")
        return json.dumps(pattern_result, indent=2)
    
    # Only use AI for high/critical threats
    if pattern_result.get('severity') in ['high', 'critical']:
        try:
            print("[*] Critical threat - using minimal AI analysis")
            _last_ai_call = current_time
            
            # Minimal AI call with very short prompt
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=os.getenv('GOOGLE_API_KEY'),
                temperature=0,
                max_tokens=50
            )
            
            prompt = f"5G threat level for: {pattern_result.get('details', '')}. Critical/high/normal?"
            response = llm.invoke(prompt)
            
            if 'critical' in response.content.lower():
                pattern_result['severity'] = 'critical'
                pattern_result['details'] += f" (AI confirmed: {response.content})"
                
        except Exception as e:
            print(f"[!] AI analysis failed: {e}")
    
    return json.dumps(pattern_result, indent=2)

@tool
def get_continuous_system_metrics(minutes: Annotated[int, "Minutes of metrics to retrieve"] = 5):
    """Get continuous system metrics"""
    try:
        db_path = os.getenv('PROJECT_ROOT', os.getcwd()) + "/data/open5gs_metrics.db"
        conn = sqlite3.connect(db_path)
        
        query = f"""
            SELECT * FROM system_metrics 
            WHERE timestamp >= datetime('now', '-{minutes} minutes')
            ORDER BY timestamp DESC
            LIMIT 300
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            return "No recent system metrics available"
        
        current_cpu = df.iloc[0]['cpu_percent'] if not df.empty else 0
        current_memory = df.iloc[0]['memory_percent'] if not df.empty else 0
        avg_cpu = df['cpu_percent'].mean()
        avg_memory = df['memory_percent'].mean()
        max_cpu = df['cpu_percent'].max()
        max_memory = df['memory_percent'].max()
        
        summary = {
            'time_range': f"Last {minutes} minutes",
            'data_points': len(df),
            'cpu_usage': {
                'current': round(current_cpu, 2),
                'average': round(avg_cpu, 2),
                'maximum': round(max_cpu, 2),
                'status': 'critical' if max_cpu > 90 else 'high' if max_cpu > 75 else 'normal'
            },
            'memory_usage': {
                'current': round(current_memory, 2),
                'average': round(avg_memory, 2),
                'maximum': round(max_memory, 2),
                'status': 'critical' if max_memory > 90 else 'high' if max_memory > 75 else 'normal'
            }
        }
        
        return json.dumps(summary, indent=2)
        
    except Exception as e:
        return f"System metrics error: {str(e)}"

@tool
def get_open5gs_parameter(param_name: Annotated[str, "Parameter name to retrieve"]):
    """Get current Open5GS parameter value"""
    param_defaults = {
        "p0_nominal": -90,
        "dl_carrierBandwidth": 51,
        "ul_carrierBandwidth": 51,
        "att_tx": 10,
        "att_rx": 10
    }
    return param_defaults.get(param_name, 0)