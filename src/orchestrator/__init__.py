"""
InsightCosmos Orchestrator Module

此模組負責協調各個 Agent 執行完整的日報與週報流程。
"""

from .daily_runner import DailyPipelineOrchestrator, run_daily_pipeline
from .weekly_runner import WeeklyPipelineOrchestrator

__all__ = [
    "DailyPipelineOrchestrator",
    "run_daily_pipeline",
    "WeeklyPipelineOrchestrator",
]

__version__ = "1.0.0"
