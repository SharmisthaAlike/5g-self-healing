# agentic_llm_workflow/langgraph_agent.py
"""
LangGraph Agent Workflow and State
"""

from langgraph.graph import END, StateGraph, START
from typing import Annotated, Dict, Optional
from typing_extensions import TypedDict
import pandas as pd
from langgraph.graph.message import add_messages

class UnifiedAgentState(TypedDict):
    """Enhanced unified state"""
    next: str
    agent_id: str
    messages: Annotated[list, add_messages]
    
    # Performance monitoring (preserved)
    average_kpis_df: Optional[pd.DataFrame]
    weighted_average_gain: Optional[pd.DataFrame]
    vars_current: Dict[str, int]
    vars_new: Dict[str, int]
    
    # Security monitoring
    security_alerts: list
    threat_level: str
    last_attack_time: Optional[str]
    active_attacks: Dict[str, int]
    log_monitor_active: bool
    system_monitor_active: bool

def create_unified_agent_workflow():
    """Create the unified LangGraph workflow"""
    from .agents import monitoring_agent, security_agent, config_agent, validation_agent
    
    builder = StateGraph(UnifiedAgentState)
    
    builder.add_node("monitoring_agent", monitoring_agent)
    builder.add_node("security_agent", security_agent)
    builder.add_node("config_agent", config_agent)
    builder.add_node("validation_agent", validation_agent)
    
    builder.add_edge(START, "monitoring_agent")
    
    def route_from_monitoring(state):
        next_agent = state.get("next")
        return next_agent if next_agent else END
    
    def route_from_config(state):
        return state.get("next", END)
    
    builder.add_conditional_edges("monitoring_agent", route_from_monitoring)
    builder.add_conditional_edges("config_agent", route_from_config)
    builder.add_edge("security_agent", END)
    builder.add_edge("validation_agent", END)
    
    return builder.compile()