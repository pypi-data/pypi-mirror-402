"""Adapters for different execution backends."""

from pipeline_node_agents.adapters.base_adapter import BaseAdapter
from pipeline_node_agents.adapters.python_fn_adapter import PythonFnAdapter
from pipeline_node_agents.adapters.crewai_adapter import CrewAIAdapter

__all__ = ["BaseAdapter", "PythonFnAdapter", "CrewAIAdapter"]
