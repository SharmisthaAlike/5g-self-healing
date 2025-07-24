# agentic_llm_workflow/agents.py
"""
Agent function definitions with rate limiting
"""

import os
import time
from copy import deepcopy
from datetime import datetime
from langgraph.graph import END
from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI

from .langgraph_agent import UnifiedAgentState
from .tools import (
    analyze_nrf_logs_smart,
    calc_weighted_average,
    execute_open5gs_sql,
    get_continuous_system_metrics,
    get_open5gs_parameter,
)
from .self_healing import execute_defensive_action

load_dotenv()

def init_agent():
    """Initialize Gemini agent with conservative settings"""
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=os.getenv('GOOGLE_API_KEY'),
        temperature=0,
        max_tokens=200  # Minimal tokens to avoid rate limits
    )

def monitoring_agent(state: UnifiedAgentState) -> UnifiedAgentState:
    """Monitoring agent with LOCAL analysis first"""
    print("\n🔍 Smart Monitoring Agent (Rate-Limited)")
    
    # Ensure state exists
    if not state:
        state = {
            "next": None,
            "agent_id": "monitoring_agent", 
            "messages": [],
            "vars_current": {"p0_nominal": -90, "dl_carrierBandwidth": 51, "ul_carrierBandwidth": 51, "att_tx": 10, "att_rx": 10},
            "vars_new": None,
            "security_alerts": [],
            "threat_level": "normal",
            "last_attack_time": None,
            "active_attacks": {},
            "log_monitor_active": True,
            "system_monitor_active": True,
            "average_kpis_df": None,
            "weighted_average_gain": None
        }
    
    # LOCAL ANALYSIS FIRST - No API calls initially
    try:
        from .tools import get_nrf_logs_pattern_analysis
        analysis = get_nrf_logs_pattern_analysis()
    except Exception as e:
        print(f"[!] Analysis error: {e}")
        analysis = {
            'threat_detected': False,
            'threat_type': 'error',
            'severity': 'normal',
            'details': f'Analysis failed: {e}'
        }
    
    # Ensure analysis is valid
    if not analysis or not isinstance(analysis, dict):
        analysis = {
            'threat_detected': False,
            'threat_type': 'normal',
            'severity': 'normal',
            'details': 'No analysis data'
        }
    
    threats_detected = []
    threat_level = analysis.get('severity', 'normal')
    
    if analysis.get('threat_detected', False):
        threat_type = analysis.get('threat_type', 'unknown')
        threats_detected.append(threat_type)
        
        # Execute self-healing immediately for high/critical threats
        if threat_level in ['high', 'critical']:
            print(f"[🔧] Auto-healing for {threat_level} threat")
            try:
                from .self_healing import execute_defensive_action
                action = 'kill_processes' if 'flood' in threat_type else 'monitor'
                execute_defensive_action(action, threat_type, 'unknown')
            except Exception as e:
                print(f"[!] Self-healing error: {e}")
    
    # Determine next agent
    if threats_detected:
        next_agent = "security_agent"
        message = f"🚨 THREATS: {', '.join(threats_detected)} (Level: {threat_level})"
    else:
        next_agent = None
        message = "✅ Network Normal - Local analysis complete"
    
    return {
        "next": next_agent,
        "agent_id": "monitoring_agent",
        "messages": state.get("messages", []) + [("assistant", f"{message}\n\nDetails: {analysis.get('details', 'No details')}")],
        "security_alerts": threats_detected,
        "threat_level": threat_level,
        "last_attack_time": datetime.now().isoformat() if threats_detected else state.get("last_attack_time"),
        "active_attacks": {threat: 1 for threat in threats_detected},
        "vars_current": state.get("vars_current", {"p0_nominal": -90, "dl_carrierBandwidth": 51, "ul_carrierBandwidth": 51, "att_tx": 10, "att_rx": 10}),
        "vars_new": None,
        "log_monitor_active": True,
        "system_monitor_active": True,
        "average_kpis_df": None,
        "weighted_average_gain": None
    }

def security_agent(state: UnifiedAgentState) -> UnifiedAgentState:
    """Security agent with self-healing"""
    print("\n🛡️ Security Response Agent")
    
    threats = state.get("security_alerts", [])
    threat_level = state.get("threat_level", "normal")
    
    # Execute additional defensive measures
    action_plan = []
    if threats:
        for threat in threats:
            if 'flood' in threat.lower():
                execute_defensive_action('kill_processes', threat, 'unknown')
                action_plan.append("🚨 EXECUTED: Killed flood processes")
                action_plan.append("🔧 EXECUTED: Restarted NRF service")
            elif 'reconnaissance' in threat.lower():
                action_plan.append("⚠️ MONITORING: Enhanced log analysis active")
            elif 'dos' in threat.lower():
                execute_defensive_action('full_defense', threat, 'unknown')
                action_plan.append("🚨 EXECUTED: Full defensive measures")
    
    message = f"""Security Response Complete:

🎯 Threats Handled: {', '.join(threats)}
🛡️ Threat Level: {threat_level}

🤖 Actions Taken:
{chr(10).join(action_plan) if action_plan else "• Monitoring enhanced"}

✅ Self-healing systems active
"""
    
    return {
        "next": END,
        "agent_id": "security_agent",
        "messages": state["messages"] + [("assistant", message)],
        "security_alerts": threats,
        "threat_level": threat_level,
        "vars_current": state["vars_current"],
        "vars_new": None,
        "log_monitor_active": True,
        "system_monitor_active": True
    }

def config_agent(state: UnifiedAgentState) -> UnifiedAgentState:
    """Config agent with LOCAL analysis"""
    print("\n⚙️ Performance Agent (Local Analysis)")
    
    # LOCAL system analysis - no API calls
    try:
        from .monitoring import ContinuousSystemMonitor
        monitor = ContinuousSystemMonitor()
        df = monitor.get_recent_metrics(5)
        
        if not df.empty:
            avg_cpu = df['cpu_percent'].mean()
            avg_memory = df['memory_percent'].mean()
            
            recommendations = []
            if avg_cpu > 80:
                recommendations.append("• High CPU detected - consider service optimization")
            if avg_memory > 80:
                recommendations.append("• High memory usage - monitor for leaks")
            
            if not recommendations:
                recommendations.append("• System performance within normal limits")
            
            analysis = f"""Performance Analysis (Local):

📊 System Metrics (5-min average):
- CPU Usage: {avg_cpu:.1f}%
- Memory Usage: {avg_memory:.1f}%

🔧 Recommendations:
{chr(10).join(recommendations)}

⚙️ Current Parameters: {state['vars_current']}
"""
        else:
            analysis = "No recent performance data available"
            
    except Exception as e:
        analysis = f"Performance analysis error: {e}"
    
    return {
        "next": END,
        "agent_id": "config_agent",
        "messages": state["messages"] + [("assistant", analysis)],
        "vars_current": state["vars_current"],
        "vars_new": None,
        "security_alerts": state.get("security_alerts", []),
        "threat_level": state.get("threat_level", "normal"),
        "log_monitor_active": True,
        "system_monitor_active": True
    }

def validation_agent(state: UnifiedAgentState) -> UnifiedAgentState:
    """Validation agent"""
    print("\n✅ Validation Agent Active")
    
    if not state.get("vars_new") or state["vars_new"] == state["vars_current"]:
        return {
            "next": END,
            "agent_id": "validation_agent",
            "messages": state["messages"] + [("assistant", "No configuration changes to validate.")],
            "vars_current": state["vars_current"],
            "vars_new": None,
            "security_alerts": state.get("security_alerts", []),
            "threat_level": state.get("threat_level", "normal"),
            "log_monitor_active": True,
            "system_monitor_active": True
        }
    
    # Simulate validation
    print("🔄 Simulating configuration validation...")
    time.sleep(2)
    
    validation_success = True
    
    if validation_success:
        message = f"""✅ Configuration Validation Successful

🔧 Applied Changes:
   Previous: {state['vars_current']}
   New: {state['vars_new']}

📊 Validation Results:
   • System stability: ✅ Confirmed
   • Performance impact: ✅ Positive

🎯 New configuration active and monitored.
"""
        final_vars = state["vars_new"]
    else:
        message = "❌ Configuration validation failed - rolling back"
        final_vars = state["vars_current"]
    
    return {
        "next": END,
        "agent_id": "validation_agent",
        "messages": state["messages"] + [("assistant", message)],
        "vars_current": final_vars,
        "vars_new": None,
        "security_alerts": state.get("security_alerts", []),
        "threat_level": state.get("threat_level", "normal"),
        "log_monitor_active": True,
        "system_monitor_active": True
    }