"""
h_agent/screens/__init__.py - Screens Module

Full-screen UI components for h-agent.
Provides interactive full-screen experiences like doctor diagnostics.
"""

from h_agent.screens.doctor import run_doctor_screen, run_doctor_check

__all__ = [
    "run_doctor_screen",
    "run_doctor_check",
]
