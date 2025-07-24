# telco_planner_ui.py
"""
Complete 5G Network AI Dashboard with Chatbot
Integrates with Fixed UnifiedNetworkAgent System
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import time
import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Import the fixed unified agent
from agentic_llm_workflow import UnifiedNetworkAgent

# ==================== PAGE CONFIGURATION ====================

st.set_page_config(
    page_title="🧠 5G AI Network Manager",
    page_icon="📡", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==================== COMPREHENSIVE CSS STYLING ====================

st.markdown("""
<style>
/* Main theme colors */
:root {
    --primary-blue: #4285f4;
    --primary-green: #0f9d58;
    --primary-orange: #ff9800;
    --primary-red: #f44336;
    --primary-purple: #9c27b0;
    --bg-light: #f8f9fa;
    --bg-card: #ffffff;
    --text-dark: #1a1a1a;
    --text-light: #666666;
    --border-light: #e8eaed;
    --shadow-light: rgba(0,0,0,0.08);
    --shadow-hover: rgba(0,0,0,0.12);
}

/* Global styling */
.main > div {
    padding-top: 2rem;
}

/* Header styling */
.main-header {
    text-align: center;
    padding: 2rem 0 3rem 0;
    background: linear-gradient(135deg, var(--bg-light) 0%, #ffffff 100%);
    border-radius: 15px;
    margin-bottom: 2rem;
    box-shadow: 0 4px 20px var(--shadow-light);
}

.main-header h1 {
    color: var(--text-dark);
    margin-bottom: 0.5rem;
    font-size: 3rem;
    font-weight: 700;
}

.main-header p {
    font-size: 1.3rem;
    color: var(--text-light);
    margin: 0;
    font-weight: 400;
}

/* Status Cards */
.status-card {
    padding: 1.8rem;
    border-radius: 15px;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 20px var(--shadow-light);
    border: 1px solid var(--border-light);
    background: var(--bg-card);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}

.status-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, var(--primary-blue), var(--primary-green));
}

.status-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 30px var(--shadow-hover);
}

.status-card h3 {
    margin: 0 0 1rem 0;
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--text-dark);
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.status-card .metric {
    font-size: 2.5rem;
    font-weight: 800;
    margin: 0;
    line-height: 1;
    font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
}

.status-card .subtext {
    font-size: 0.9rem;
    color: var(--text-light);
    margin-top: 0.5rem;
    font-weight: 500;
}

/* Threat level specific colors */
.threat-normal .metric { color: var(--primary-green); }
.threat-normal::before { background: var(--primary-green); }

.threat-medium .metric { color: var(--primary-orange); }
.threat-medium::before { background: var(--primary-orange); }

.threat-high .metric { color: var(--primary-red); }
.threat-high::before { background: var(--primary-red); }

.threat-critical .metric { color: var(--primary-purple); }
.threat-critical::before { background: var(--primary-purple); }

/* CPU/Memory status colors */
.cpu-normal .metric { color: var(--primary-green); }
.cpu-normal::before { background: var(--primary-green); }

.cpu-warning .metric { color: var(--primary-orange); }
.cpu-warning::before { background: var(--primary-orange); }

.cpu-critical .metric { color: var(--primary-red); }
.cpu-critical::before { background: var(--primary-red); }

/* Main Action Buttons */
.action-button-container {
    display: flex;
    gap: 1rem;
    margin: 2rem 0;
    align-items: center;
}

/* Security scan button */
.stButton > button[key="security"] {
    background: linear-gradient(135deg, #e53e3e 0%, #c53030 100%);
    color: white;
    border: none;
    padding: 1rem 2rem;
    border-radius: 12px;
    font-weight: 600;
    font-size: 1.1rem;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(229, 62, 62, 0.3);
    width: 100%;
    height: 60px;
    position: relative;
    overflow: hidden;
}

.stButton > button[key="security"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(229, 62, 62, 0.4);
    background: linear-gradient(135deg, #c53030 0%, #e53e3e 100%);
}

.stButton > button[key="security"]:active {
    transform: translateY(0);
}

/* Performance report button */
.stButton > button[key="performance"] {
    background: linear-gradient(135deg, var(--primary-green) 0%, #2e7d32 100%);
    color: white;
    border: none;
    padding: 1rem 2rem;
    border-radius: 12px;
    font-weight: 600;
    font-size: 1.1rem;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(15, 157, 88, 0.3);
    width: 100%;
    height: 60px;
}

.stButton > button[key="performance"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(15, 157, 88, 0.4);
    background: linear-gradient(135deg, #2e7d32 0%, var(--primary-green) 100%);
}

/* Refresh button */
.stButton > button[key="refresh"] {
    background: linear-gradient(135deg, var(--primary-blue) 0%, #1565c0 100%);
    color: white;
    border: none;
    padding: 1rem 2rem;
    border-radius: 12px;
    font-weight: 600;
    font-size: 1.1rem;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(66, 133, 244, 0.3);
    width: 100%;
    height: 60px;
}

.stButton > button[key="refresh"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(66, 133, 244, 0.4);
    background: linear-gradient(135deg, #1565c0 0%, var(--primary-blue) 100%);
}

/* Alert Cards */
.alert-card {
    background: linear-gradient(135deg, #fff5f5 0%, #fed7d7 100%);
    border: 2px solid #fc8181;
    border-radius: 15px;
    padding: 1.5rem;
    margin: 1rem 0;
    box-shadow: 0 4px 20px rgba(244, 67, 54, 0.15);
    position: relative;
    overflow: hidden;
}

.alert-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, #fc8181, #f56565);
}

.alert-card h4 {
    color: var(--primary-red);
    margin: 0 0 1rem 0;
    font-weight: 700;
    font-size: 1.2rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.alert-card p {
    margin: 0.5rem 0;
    color: #742a2a;
    font-weight: 500;
}

/* Chart containers */
.chart-container {
    background: var(--bg-card);
    border-radius: 15px;
    padding: 1.5rem;
    box-shadow: 0 4px 20px var(--shadow-light);
    border: 1px solid var(--border-light);
    margin-bottom: 1.5rem;
    transition: all 0.3s ease;
}

.chart-container:hover {
    box-shadow: 0 8px 30px var(--shadow-hover);
}

/* Service status cards */
.service-card {
    background: var(--bg-card);
    border-radius: 12px;
    padding: 1.2rem;
    margin: 0.5rem 0;
    border: 1px solid var(--border-light);
    text-align: center;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}

.service-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px var(--shadow-hover);
}

.service-active {
    border-left: 4px solid var(--primary-green);
    background: linear-gradient(135deg, #f0fff4 0%, #c6f6d5 100%);
}

.service-active::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: var(--primary-green);
}

.service-inactive {
    border-left: 4px solid var(--primary-red);
    background: linear-gradient(135deg, #fff5f5 0%, #fed7d7 100%);
}

.service-inactive::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: var(--primary-red);
}

.service-card .service-name {
    font-weight: 700;
    font-size: 1.1rem;
    margin-bottom: 0.5rem;
    color: var(--text-dark);
}

.service-card .service-status {
    font-size: 0.9rem;
    font-weight: 500;
    color: var(--text-light);
}

/* Chatbot Styles */
.chatbot-container {
    position: fixed;
    bottom: 20px;
    right: 20px;
    width: 380px;
    background: var(--bg-card);
    border-radius: 20px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
    z-index: 1000;
    border: 1px solid var(--border-light);
    display: none;
    backdrop-filter: blur(10px);
}

.chatbot-header {
    background: linear-gradient(135deg, var(--primary-blue) 0%, #1565c0 100%);
    color: white;
    padding: 1.2rem 1.5rem;
    border-radius: 20px 20px 0 0;
    font-weight: 600;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 1.1rem;
}

.chatbot-messages {
    height: 350px;
    overflow-y: auto;
    padding: 1.5rem;
    background: #fafafa;
}

.chatbot-input {
    padding: 1.5rem;
    border-top: 1px solid var(--border-light);
    border-radius: 0 0 20px 20px;
    background: var(--bg-card);
}

.chat-message {
    margin-bottom: 1rem;
    padding: 0.8rem 1rem;
    border-radius: 12px;
    max-width: 85%;
    word-wrap: break-word;
}

.user-message {
    background: linear-gradient(135deg, var(--primary-blue) 0%, #1565c0 100%);
    color: white;
    margin-left: auto;
    text-align: right;
}

.bot-message {
    background: white;
    color: var(--text-dark);
    border: 1px solid var(--border-light);
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.chatbot-toggle {
    position: fixed;
    bottom: 25px;
    right: 25px;
    width: 65px;
    height: 65px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--primary-blue) 0%, #1565c0 100%);
    color: white;
    border: none;
    font-size: 28px;
    cursor: pointer;
    box-shadow: 0 6px 25px rgba(66, 133, 244, 0.4);
    z-index: 999;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    display: flex;
    align-items: center;
    justify-content: center;
}

.chatbot-toggle:hover {
    transform: scale(1.1);
    box-shadow: 0 8px 30px rgba(66, 133, 244, 0.5);
}

.chatbot-toggle:active {
    transform: scale(0.95);
}

/* Section headers */
.section-header {
    font-size: 1.8rem;
    font-weight: 700;
    color: var(--text-dark);
    margin: 2rem 0 1rem 0;
    padding-bottom: 0.5rem;
    border-bottom: 3px solid var(--primary-blue);
    display: inline-block;
}

/* Expander styling */
.streamlit-expanderHeader {
    background-color: var(--bg-light);
    border-radius: 10px;
    padding: 1rem;
    border: 1px solid var(--border-light);
}

/* Hide Streamlit elements */
.stDeployButton { display: none; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }

/* Custom scrollbar */
::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb {
    background: var(--primary-blue);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: #1565c0;
}

/* Responsive design */
@media (max-width: 768px) {
    .chatbot-container {
        width: 90vw;
        right: 5vw;
    }
    
    .main-header h1 {
        font-size: 2rem;
    }
    
    .main-header p {
        font-size: 1rem;
    }
    
    .status-card {
        padding: 1rem;
    }
    
    .status-card .metric {
        font-size: 2rem;
    }
}

/* Loading animations */
@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.5; }
    100% { opacity: 1; }
}

.loading {
    animation: pulse 2s infinite;
}

/* Success/Error message styling */
.stSuccess {
    background-color: #d4edda;
    border-color: #c3e6cb;
    color: #155724;
}

.stError {
    background-color: #f8d7da;
    border-color: #f5c6cb;
    color: #721c24;
}

.stInfo {
    background-color: #d1ecf1;
    border-color: #bee5eb;
    color: #0c5460;
}
</style>
""", unsafe_allow_html=True)

# ==================== SESSION STATE MANAGEMENT ====================

if 'agent_system' not in st.session_state:
    try:
        with st.spinner("🚀 Initializing Enhanced AI Network Agent..."):
            st.session_state.agent_system = UnifiedNetworkAgent()
            st.session_state.system_initialized = True
            st.success("✅ AI Network Agent Successfully Initialized!")
    except Exception as e:
        st.session_state.system_initialized = False
        st.session_state.init_error = str(e)
        st.error(f"❌ Initialization Failed: {e}")

if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = [
        {
            "role": "assistant", 
            "content": "👋 Hello! I'm your AI network security assistant. I can help you with:\n\n🛡️ **Security Analysis** - Detect threats and attacks\n📊 **Performance Reports** - System optimization\n🔍 **Network Monitoring** - Real-time insights\n\nWhat would you like me to analyze today?"
        }
    ]

if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False

if 'last_scan_time' not in st.session_state:
    st.session_state.last_scan_time = None

# ==================== HELPER FUNCTIONS ====================

def get_open5gs_services():
    """Get Open5GS service status with enhanced error handling"""
    services = {
        'NRF': 'open5gs-nrfd',
        'AMF': 'open5gs-amfd', 
        'SMF': 'open5gs-smfd',
        'UPF': 'open5gs-upfd',
        'AUSF': 'open5gs-ausfd',
        'UDR': 'open5gs-udrd',
        'PCF': 'open5gs-pcfd',
        'NSSF': 'open5gs-nssfd'
    }
    
    status = {}
    for name, service in services.items():
        try:
            result = subprocess.run(
                f"systemctl is-active {service}", 
                shell=True, capture_output=True, text=True, timeout=5
            )
            status[name] = result.stdout.strip() == 'active'
        except Exception:
            status[name] = False
    
    return status

def get_threat_level_class(threat_level):
    """Get CSS class for threat level with enhanced mapping"""
    classes = {
        'normal': 'threat-normal',
        'low': 'threat-normal',
        'medium': 'threat-medium', 
        'high': 'threat-high',
        'critical': 'threat-critical'
    }
    return classes.get(threat_level.lower(), 'threat-normal')

def get_cpu_class(cpu_percent):
    """Get CSS class for CPU usage"""
    if cpu_percent > 85:
        return 'cpu-critical'
    elif cpu_percent > 70:
        return 'cpu-warning'
    else:
        return 'cpu-normal'

def get_memory_class(memory_percent):
    """Get CSS class for memory usage"""
    if memory_percent > 85:
        return 'cpu-critical'
    elif memory_percent > 70:
        return 'cpu-warning'
    else:
        return 'cpu-normal'

def format_timestamp(timestamp):
    """Format timestamp for display"""
    if timestamp:
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.strftime('%H:%M:%S')
        except:
            return 'Unknown'
    return 'None'

def get_system_health_score(cpu, memory, threat_level):
    """Calculate overall system health score"""
    cpu_score = max(0, 100 - cpu)
    memory_score = max(0, 100 - memory)
    
    threat_scores = {
        'normal': 100,
        'low': 80,
        'medium': 60,
        'high': 30,
        'critical': 0
    }
    
    threat_score = threat_scores.get(threat_level.lower(), 50)
    
    overall_score = (cpu_score * 0.3 + memory_score * 0.3 + threat_score * 0.4)
    return round(overall_score, 1)

# ==================== MAIN DASHBOARD FUNCTION ====================

def render_main_dashboard():
    """Render the main dashboard content"""
    
    # Header Section
    st.markdown("""
    <div class="main-header">
        <h1>🧠 AI-Powered 5G Network Manager</h1>
        <p>Advanced Security Detection • Performance Optimization • Self-Healing Technology</p>
    </div>
    """, unsafe_allow_html=True)
    
    # System initialization check
    if not st.session_state.system_initialized:
        st.error(f"⚠️ **System Initialization Error**")
        st.error(f"Details: {st.session_state.get('init_error', 'Unknown error occurred')}")
        st.info("💡 **Troubleshooting Steps:**")
        st.write("1. Check your GOOGLE_API_KEY in .env file")
        st.write("2. Ensure Open5GS services are running")
        st.write("3. Verify database permissions in /data directory")
        st.write("4. Restart the application")
        return
    
    # ==================== MAIN ACTION CONTROLS ====================
    
    st.markdown("### 🎛️ Control Center")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        security_scan = st.button(
            "🛡️ Security Scan", 
            key="security", 
            use_container_width=True,
            help="Run comprehensive security analysis with threat detection"
        )
        
        if security_scan:
            with st.spinner("🔍 Running advanced security analysis..."):
                progress_bar = st.progress(0)
                
                # Simulate progress for better UX
                for i in range(100):
                    time.sleep(0.01)
                    progress_bar.progress(i + 1)
                
                try:
                    result = st.session_state.agent_system.run_security_scan()
                    st.session_state.last_scan_time = datetime.now()
                    
                    progress_bar.empty()
                    st.success("✅ Security scan completed successfully!")
                    
                    # Display detailed results
                    if result.get('messages'):
                        latest_message = result['messages'][-1][1]
                        st.info(f"🛡️ **Security Analysis Report:**\n\n{latest_message}")
                    
                    # Show any detected threats
                    if result.get('security_alerts'):
                        st.warning(f"⚠️ **Threats Detected:** {', '.join(result['security_alerts'])}")
                    
                    st.rerun()
                    
                except Exception as e:
                    progress_bar.empty()
                    st.error(f"❌ Security scan failed: {str(e)}")
    
    with col2:
        performance_report = st.button(
            "📊 Performance Report", 
            key="performance", 
            use_container_width=True,
            help="Generate comprehensive performance analysis and optimization recommendations"
        )
        
        if performance_report:
            with st.spinner("📈 Analyzing system performance..."):
                progress_bar = st.progress(0)
                
                for i in range(100):
                    time.sleep(0.01)
                    progress_bar.progress(i + 1)
                
                try:
                    result = st.session_state.agent_system.run_performance_report()
                    
                    progress_bar.empty()
                    st.success("✅ Performance analysis completed!")
                    
                    if result.get('messages'):
                        latest_message = result['messages'][-1][1]
                        st.info(f"📊 **Performance Report:**\n\n{latest_message}")
                    
                    st.rerun()
                    
                except Exception as e:
                    progress_bar.empty()
                    st.error(f"❌ Performance analysis failed: {str(e)}")
    
    with col3:
        col3a, col3b = st.columns([1, 1])
        
        with col3a:
            if st.button("🔄 Refresh", key="refresh", use_container_width=True):
                st.rerun()
        
        with col3b:
            auto_refresh = st.checkbox(
                "Auto-refresh", 
                value=st.session_state.auto_refresh,
                help="Automatically refresh dashboard every 30 seconds"
            )
            st.session_state.auto_refresh = auto_refresh
    
    # Last scan info
    if st.session_state.last_scan_time:
        time_since_scan = (datetime.now() - st.session_state.last_scan_time).total_seconds()
        st.caption(f"🕒 Last security scan: {int(time_since_scan)}s ago")
    
    st.divider()
    
    # ==================== SYSTEM STATUS OVERVIEW ====================
    
    try:
        current_status = st.session_state.agent_system.get_current_status()
        continuous_metrics = st.session_state.agent_system.get_continuous_metrics()
    except Exception as e:
        st.error(f"❌ Error retrieving system status: {e}")
        return
    
    st.markdown('<h2 class="section-header">📊 Network Status Overview</h2>', unsafe_allow_html=True)
    
    # Main status metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        threat_level = current_status.get('security_status', {}).get('threat_level', 'normal')
        threat_class = get_threat_level_class(threat_level)
        st.markdown(f"""
        <div class="status-card {threat_class}">
            <h3>🛡️ Security Status</h3>
            <p class="metric">{threat_level.title()}</p>
            <p class="subtext">Threat Level</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        alerts = len(current_status.get('security_status', {}).get('active_alerts', []))
        alert_class = 'threat-high' if alerts > 0 else 'threat-normal'
        st.markdown(f"""
        <div class="status-card {alert_class}">
            <h3>🚨 Active Threats</h3>
            <p class="metric">{alerts}</p>
            <p class="subtext">Security Alerts</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        system_metrics = continuous_metrics.get('system_metrics', [])
        cpu = system_metrics[0]['cpu_percent'] if system_metrics else 0
        cpu_class = get_cpu_class(cpu)
        st.markdown(f"""
        <div class="status-card {cpu_class}">
            <h3>💻 CPU Usage</h3>
            <p class="metric">{cpu:.1f}%</p>
            <p class="subtext">Current Load</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        memory = system_metrics[0]['memory_percent'] if system_metrics else 0
        mem_class = get_memory_class(memory)
        st.markdown(f"""
        <div class="status-card {mem_class}">
            <h3>🧠 Memory</h3>
            <p class="metric">{memory:.1f}%</p>
            <p class="subtext">RAM Usage</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        health_score = get_system_health_score(cpu, memory, threat_level)
        health_class = get_cpu_class(100 - health_score)  # Invert for health score
        st.markdown(f"""
        <div class="status-card {health_class}">
            <h3>💚 Health Score</h3>
            <p class="metric">{health_score}</p>
            <p class="subtext">Overall Status</p>
        </div>
        """, unsafe_allow_html=True)
    
    # ==================== ACTIVE SECURITY ALERTS ====================
    
    active_alerts = current_status.get('security_status', {}).get('active_alerts', [])
    if active_alerts:
        st.markdown('<h2 class="section-header">🚨 Active Security Alerts</h2>', unsafe_allow_html=True)
        
        for i, alert in enumerate(active_alerts):
            st.markdown(f"""
            <div class="alert-card">
                <h4>⚠️ {alert}</h4>
                <p><strong>Status:</strong> Active & Under AI Management</p>
                <p><strong>Response:</strong> Automated defensive measures activated</p>
                <p><strong>Self-Healing:</strong> {current_status.get('security_status', {}).get('self_healing', 'Active')}</p>
                <p><strong>Last Detection:</strong> {format_timestamp(current_status.get('security_status', {}).get('last_attack'))}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # ==================== REAL-TIME PERFORMANCE CHARTS ====================
    
    if system_metrics:
        st.markdown('<h2 class="section-header">📈 Real-time Performance Analytics</h2>', unsafe_allow_html=True)
        
        # Convert to DataFrame for plotting
        df = pd.DataFrame(system_metrics)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Create two columns for charts
        col1, col2 = st.columns(2)
        
        with col1:
            # CPU Usage Chart
            fig_cpu = go.Figure()
            fig_cpu.add_trace(go.Scatter(
                x=df['timestamp'], 
                y=df['cpu_percent'],
                mode='lines+markers',
                name='CPU Usage',
                line=dict(color='#4285f4', width=3),
                marker=dict(size=6),
                fill='tonexty',
                fillcolor='rgba(66, 133, 244, 0.1)',
                hovertemplate='<b>CPU Usage</b><br>' +
                              'Time: %{x}<br>' +
                              'Usage: %{y:.1f}%<br>' +
                              '<extra></extra>'
            ))
            
            fig_cpu.update_layout(
                title={
                    'text': "💻 CPU Usage (Last 5 Minutes)",
                    'x': 0.5,
                    'font': {'size': 18, 'family': 'Arial, sans-serif'}
                },
                xaxis_title="Time",
                yaxis_title="CPU Usage (%)",
                yaxis=dict(range=[0, 100]),
                height=400,
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Arial, sans-serif"),
                hovermode='x unified'
            )
            
            # Add threshold lines
            fig_cpu.add_hline(y=80, line_dash="dash", line_color="red", 
                             annotation_text="Critical (80%)", annotation_position="bottom right")
            fig_cpu.add_hline(y=60, line_dash="dash", line_color="orange", 
                             annotation_text="Warning (60%)", annotation_position="bottom right")
            
            st.plotly_chart(fig_cpu, use_container_width=True)
        
        with col2:
            # Memory Usage Chart
            fig_mem = go.Figure()
            fig_mem.add_trace(go.Scatter(
                x=df['timestamp'], 
                y=df['memory_percent'],
                mode='lines+markers',
                name='Memory Usage',
                line=dict(color='#0f9d58', width=3),
                marker=dict(size=6),
                fill='tonexty',
                fillcolor='rgba(15, 157, 88, 0.1)',
                hovertemplate='<b>Memory Usage</b><br>' +
                              'Time: %{x}<br>' +
                              'Usage: %{y:.1f}%<br>' +
                              '<extra></extra>'
            ))
            
            fig_mem.update_layout(
                title={
                    'text': "🧠 Memory Usage (Last 5 Minutes)",
                    'x': 0.5,
                    'font': {'size': 18, 'family': 'Arial, sans-serif'}
                },
                xaxis_title="Time",
                yaxis_title="Memory Usage (%)",
                yaxis=dict(range=[0, 100]),
                height=400,
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Arial, sans-serif"),
                hovermode='x unified'
            )
            
            # Add threshold lines
            fig_mem.add_hline(y=80, line_dash="dash", line_color="red", 
                             annotation_text="Critical (80%)", annotation_position="bottom right")
            fig_mem.add_hline(y=60, line_dash="dash", line_color="orange", 
                             annotation_text="Warning (60%)", annotation_position="bottom right")
            
            st.plotly_chart(fig_mem, use_container_width=True)
        
        # System health trend
        if len(df) > 1:
            df['health_score'] = df.apply(
                lambda row: get_system_health_score(row['cpu_percent'], row['memory_percent'], threat_level), 
                axis=1
            )
            
            fig_health = go.Figure()
            fig_health.add_trace(go.Scatter(
                x=df['timestamp'], 
                y=df['health_score'],
                mode='lines+markers',
                name='System Health',
                line=dict(color='#9c27b0', width=3),
                marker=dict(size=6),
                fill='tonexty',
                fillcolor='rgba(156, 39, 176, 0.1)',
                hovertemplate='<b>System Health Score</b><br>' +
                              'Time: %{x}<br>' +
                              'Score: %{y:.1f}/100<br>' +
                              '<extra></extra>'
            ))
            
            fig_health.update_layout(
                title={
                    'text': "💚 Overall System Health Score",
                    'x': 0.5,
                    'font': {'size': 18, 'family': 'Arial, sans-serif'}
                },
                xaxis_title="Time",
                yaxis_title="Health Score",
                yaxis=dict(range=[0, 100]),
                height=300,
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Arial, sans-serif"),
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_health, use_container_width=True)
    
    # ==================== OPEN5GS SERVICES STATUS ====================
    
    with st.expander("🔧 Open5GS Services Status", expanded=False):
        st.markdown("### Service Health Monitor")
        
        services = get_open5gs_services()
        
        # Create columns for services
        cols = st.columns(4)
        
        for i, (service, status) in enumerate(services.items()):
            with cols[i % 4]:
                status_class = 'service-active' if status else 'service-inactive'
                status_icon = '🟢' if status else '🔴'
                status_text = 'Active' if status else 'Inactive'
                status_color = '#0f9d58' if status else '#f44336'
                
                st.markdown(f"""
                <div class="service-card {status_class}">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">{status_icon}</div>
                    <div class="service-name" style="color: {status_color};">{service}</div>
                    <div class="service-status">{status_text}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Service summary
        active_count = sum(services.values())
        total_count = len(services)
        
        if active_count == total_count:
            st.success(f"✅ All {total_count} services are running normally")
        elif active_count > 0:
            st.warning(f"⚠️ {active_count}/{total_count} services active - {total_count - active_count} services need attention")
        else:
            st.error(f"❌ All services are down - immediate attention required")

# ==================== CHATBOT COMPONENT ====================

def render_chatbot():
    """Render the floating chatbot interface"""
    
    # Chatbot toggle button (always visible)
    st.markdown("""
    <div class="chatbot-toggle" onclick="toggleChatbot()" id="chatbot-toggle">
        🤖
    </div>
    """, unsafe_allow_html=True)
    
    # Chatbot container
    st.markdown(f"""
    <div class="chatbot-container" id="chatbot-container">
        <div class="chatbot-header">
            <span>🤖 AI Network Assistant</span>
            <button onclick="toggleChatbot()" style="background: none; border: none; color: white; font-size: 20px; cursor: pointer; padding: 0;">✕</button>
        </div>
        <div class="chatbot-messages" id="chat-messages">
    """, unsafe_allow_html=True)
    
    # Display chat messages
    for message in st.session_state.chat_messages:
        role_class = "user-message" if message["role"] == "user" else "bot-message"
        st.markdown(f"""
        <div class="chat-message {role_class}">
            {message["content"]}
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("""
        </div>
        <div class="chatbot-input">
    """, unsafe_allow_html=True)
    
    # Chat input form
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input(
            "Type your message...", 
            key="chat_input", 
            label_visibility="collapsed",
            placeholder="Ask about security, performance, or network status..."
        )
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            submitted = st.form_submit_button("Send Message", use_container_width=True)
        
        with col2:
            if st.form_submit_button("Clear Chat", use_container_width=True):
                st.session_state.chat_messages = [
                    {
                        "role": "assistant", 
                        "content": "👋 Chat cleared! How can I help you with your 5G network today?"
                    }
                ]
                st.rerun()
        
        if submitted and user_input.strip():
            # Add user message to chat
            st.session_state.chat_messages.append({
                "role": "user", 
                "content": user_input
            })
            
            # Process with AI system
            with st.spinner("🤖 AI assistant is thinking..."):
                try:
                    result = st.session_state.agent_system.process_chat_query(user_input)
                    
                    # Extract response
                    if result.get('messages') and len(result['messages']) > 0:
                        bot_response = result['messages'][-1][1]
                    else:
                        # Generate contextual response based on query
                        if any(keyword in user_input.lower() for keyword in ['security', 'threat', 'attack', 'hack']):
                            bot_response = "🛡️ I can help with security analysis! Use the 'Security Scan' button above for a comprehensive threat assessment, or ask me specific security questions."
                        elif any(keyword in user_input.lower() for keyword in ['performance', 'cpu', 'memory', 'speed']):
                            bot_response = "📊 For performance insights, try the 'Performance Report' button above. I can also answer questions about system metrics and optimization."
                        elif any(keyword in user_input.lower() for keyword in ['service', 'open5gs', 'nrf', 'amf']):
                            bot_response = "🔧 I can help with Open5GS service status! Check the services section above, or ask me about specific network functions."
                        else:
                            bot_response = "I'm here to help with your 5G network! I can assist with:\n\n🛡️ Security analysis and threat detection\n📊 Performance monitoring and optimization\n🔧 Service status and troubleshooting\n\nWhat would you like to know?"
                    
                    # Add AI response to chat
                    st.session_state.chat_messages.append({
                        "role": "assistant", 
                        "content": bot_response
                    })
                    
                except Exception as e:
                    # Error handling with helpful message
                    error_response = f"❌ I encountered an error: {str(e)}\n\nPlease try:\n• Using the main dashboard buttons\n• Asking a different question\n• Refreshing the page if the issue persists"
                    
                    st.session_state.chat_messages.append({
                        "role": "assistant", 
                        "content": error_response
                    })
            
            st.rerun()
    
    st.markdown("""
        </div>
    </div>
    
    <script>
    function toggleChatbot() {
        const container = document.getElementById('chatbot-container');
        const toggle = document.getElementById('chatbot-toggle');
        
        if (container.style.display === 'none' || !container.style.display) {
            container.style.display = 'block';
            toggle.style.display = 'none';
        } else {
            container.style.display = 'none';
            toggle.style.display = 'flex';
        }
    }
    
    // Auto-scroll chat messages to bottom
    function scrollChatToBottom() {
        const chatMessages = document.getElementById('chat-messages');
        if (chatMessages) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }
    
    // Call scroll function after page loads
    setTimeout(scrollChatToBottom, 100);
    </script>
    """, unsafe_allow_html=True)

# ==================== MAIN APPLICATION ====================

def main():
    """Main application function"""
    
    # Render main dashboard
    render_main_dashboard()
    
    # Render floating chatbot
    render_chatbot()
    # Add to main() function, right before the existing auto-refresh
    if st.session_state.system_initialized:
        try:
            # Check for new threats every page load
            current_status = st.session_state.agent_system.get_current_status()
            if current_status.get('security_status', {}).get('active_alerts'):
                st.error("🚨 ACTIVE THREAT DETECTED!")
                # Auto-refresh every 5 seconds during attacks
                time.sleep(5)
                st.rerun()
        except:
            pass
    # Auto-refresh functionality
    if st.session_state.auto_refresh:
        # Show auto-refresh indicator
        st.sidebar.success("🔄 Auto-refresh active (30s)")
        time.sleep(30)
        st.rerun()
    
    # Footer with system information
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🧠 AI Network Manager**")
        st.caption("Enhanced with Self-Healing Technology")
    
    with col2:
        st.markdown("**📊 Monitoring Status**")
        if st.session_state.system_initialized:
            st.caption("✅ All systems operational")
        else:
            st.caption("❌ System initialization failed")
    
    with col3:
        st.markdown("**🛡️ Security Level**")
        if st.session_state.system_initialized:
            try:
                status = st.session_state.agent_system.get_current_status()
                threat_level = status.get('security_status', {}).get('threat_level', 'unknown')
                st.caption(f"Current: {threat_level.title()}")
            except:
                st.caption("Status unavailable")
        else:
            st.caption("Status unavailable")
    
    # Version info in sidebar
    with st.sidebar:
        st.markdown("### 📋 System Information")
        st.info("""
        **Version:** 2.0.0  
        **AI Engine:** Gemini 1.5 Flash  
        **Monitoring:** Real-time  
        **Self-Healing:** Active  
        **Rate Limiting:** Enabled  
        """)
        
        if st.button("🔄 Force Refresh System", key="force_refresh"):
            # Clear cache and reinitialize
            for key in ['agent_system', 'last_scan_time']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

# ==================== APPLICATION ENTRY POINT ====================

if __name__ == "__main__":
    main()