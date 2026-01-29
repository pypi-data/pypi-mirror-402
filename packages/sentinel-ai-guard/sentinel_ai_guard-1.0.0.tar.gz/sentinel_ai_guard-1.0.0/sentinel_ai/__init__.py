"""
Sentinel-AI: Immune System for AI Agents
=========================================

A lightweight, plug-and-play middleware to prevent semantic hijacking in AI agents.

Usage:
    from sentinel_ai import configure_sentinel, sentinel_guard, sentinel_prompt
    
    # Configure once
    configure_sentinel(llm_provider='openai', api_key='sk-xxx', model='gpt-4')
    
    # Enhance user prompt
    enhanced = sentinel_prompt("Summarize my invoices")
    
    # Protect tools
    @sentinel_guard(risk_level='high')
    def send_payment(amount, recipient):
        return f"Paid ${amount} to {recipient}"
"""

from .core import (
    SentinelGuard,
    configure_sentinel,
    sentinel_guard,
    sentinel_prompt,
    get_current_user_goal,
    clear_sentinel_context
)
from .redactor import SentinelRedactor
from .policy import SecurityPolicy

__version__ = "1.0.0"
__all__ = [
    "SentinelGuard",
    "configure_sentinel",
    "sentinel_guard",
    "sentinel_prompt",
    "get_current_user_goal",
    "clear_sentinel_context",
    "SentinelRedactor",
    "SecurityPolicy"
]
