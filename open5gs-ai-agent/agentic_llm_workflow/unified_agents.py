# agentic_llm_workflow/unified_agents.py
"""
Complete Unified 5G Network AI Agent System - Fixed Version
"""
# At the top of unified_agents.py, add:
import time
from copy import deepcopy
from .langgraph_agent import create_unified_agent_workflow
from .monitoring import ContinuousSystemMonitor
from .open5gs_manager import Open5GSMetricsCollector

class UnifiedNetworkAgent:
    """Complete unified network management system"""

    def __init__(self):
        print("🚀 Initializing Unified Network Agent System...")

        try:
            self.workflow = create_unified_agent_workflow()
            self.system_monitor = ContinuousSystemMonitor()
            self.metrics_collector = Open5GSMetricsCollector()

            print("🔄 Starting continuous monitoring systems...")
            self.system_monitor.start_monitoring()
            self.start_real_time_monitoring()
            self.state = {
                "next": None,
                "agent_id": "system",
                "messages": [],
                "vars_current": {
                    "p0_nominal": -90,
                    "dl_carrierBandwidth": 51,
                    "ul_carrierBandwidth": 51,
                    "att_tx": 10,
                    "att_rx": 10
                },
                "vars_new": None,
                "security_alerts": [],
                "threat_level": "normal",
                "last_attack_time": None,
                "active_attacks": {},
                "average_kpis_df": None,
                "weighted_average_gain": None,
                "log_monitor_active": True,
                "system_monitor_active": True
            }

            print("✅ Unified Network Agent System Initialized")
            print("🛡️ Real-time security monitoring: ACTIVE")
            print("📊 Continuous system monitoring: ACTIVE")
            print("🤖 AI agent workflow: READY")
            
        except Exception as e:
            print(f"❌ Initialization error: {e}")
            raise

    def run_security_scan(self):
        """Run security-focused analysis"""
        try:
            # Collect recent metrics first
            if hasattr(self, 'metrics_collector'):
                try:
                    self.metrics_collector.collect_all_metrics()
                except:
                    pass
            
            # Run monitoring agent which does local security analysis
            from .agents import monitoring_agent
            result = monitoring_agent(self.state)
            
            # Ensure result is valid
            if not result or not isinstance(result, dict):
                result = {
                    "security_alerts": [],
                    "threat_level": "normal",
                    "messages": [("assistant", "Security scan completed - no data")]
                }
            
            self.state.update(result)
            
            # If threats detected, run security agent
            if result.get('security_alerts'):
                try:
                    from .agents import security_agent
                    security_result = security_agent(self.state)
                    if security_result and isinstance(security_result, dict):
                        self.state.update(security_result)
                except Exception as e:
                    print(f"[!] Security agent error: {e}")
            
            return self.state
            
        except Exception as e:
            print(f"❌ Security scan error: {e}")
            # Return safe fallback state
            return {
                "security_alerts": [],
                "threat_level": "error",
                "messages": [("assistant", f"Security scan error: {e}")]
            }

    def run_performance_report(self):
        """Run performance analysis"""
        try:
            # Collect recent metrics
            self.metrics_collector.collect_all_metrics()
            
            # Run config agent for performance analysis
            from .agents import config_agent
            result = config_agent(self.state)
            self.state.update(result)
            return self.state
        except Exception as e:
            print(f"❌ Performance report error: {e}")
            return self.state
    def start_real_time_monitoring(self):
        """Start background threat detection"""
        import threading
        
        def monitor_loop():
            while True:
                try:
                    # Check every 2 seconds
                    result = self.run_security_scan()
                    if result.get('security_alerts'):
                        print(f"🚨 REAL-TIME ALERT: {result['security_alerts']}")
                    time.sleep(2)
                except:
                    time.sleep(5)
        
        thread = threading.Thread(target=monitor_loop)
        thread.daemon = True
        thread.start()
    def process_chat_query(self, query: str):
        """Process chat query with local analysis"""
        try:
            # Route to appropriate analysis based on query
            if any(keyword in query.lower() for keyword in ['security', 'threat', 'attack']):
                return self.run_security_scan()
            elif any(keyword in query.lower() for keyword in ['performance', 'cpu', 'memory']):
                return self.run_performance_report()
            else:
                # Simple response for general queries
                self.state["messages"] = [("assistant", "I can help with security scans and performance reports. What would you like me to analyze?")]
                return self.state
        except Exception as e:
            print(f"❌ Chat error: {e}")
            return self.state

    def get_current_status(self):
        """Get comprehensive current status"""
        try:
            # Get recent system metrics
            system_metrics = self.system_monitor.get_recent_metrics(5)
            current_metrics = system_metrics.iloc[0].to_dict() if not system_metrics.empty else {}
            
            return {
                "security_status": {
                    "threat_level": self.state.get("threat_level", "normal"),
                    "active_alerts": self.state.get("security_alerts", []),
                    "last_attack": self.state.get("last_attack_time"),
                    "self_healing": True
                },
                "system_metrics": current_metrics,
                "monitoring_status": {
                    "system_monitor": self.system_monitor.monitoring,
                    "self_healing": True
                },
                "last_agent": self.state.get("agent_id", "none")
            }
        except Exception as e:
            print(f"❌ Status error: {e}")
            return {"error": str(e)}

    def get_continuous_metrics(self):
        """Get metrics for charts"""
        try:
            system_metrics = self.system_monitor.get_recent_metrics(5)
            return {
                'system_metrics': system_metrics.to_dict('records') if not system_metrics.empty else [],
                'monitoring_status': {
                    'system_monitor': self.system_monitor.monitoring,
                    'self_healing': True
                }
            }
        except Exception as e:
            print(f"❌ Metrics error: {e}")
            return {'system_metrics': [], 'monitoring_status': {'system_monitor': False, 'self_healing': False}}

    def get_open5gs_metrics(self, minutes=5):
        """Get recent Open5GS metrics"""
        try:
            return self.metrics_collector.get_recent_metrics(minutes)
        except Exception as e:
            print(f"❌ Open5GS metrics error: {e}")
            return None

    def shutdown(self):
        """Graceful shutdown"""
        print("🛑 Shutting down Unified Network Agent...")
        try:
            self.system_monitor.stop_monitoring()
            print("✅ Shutdown complete")
        except Exception as e:
            print(f"⚠️ Shutdown warning: {e}")

    def __del__(self):
        """Cleanup when object is destroyed"""
        try:
            self.shutdown()
        except:
            pass