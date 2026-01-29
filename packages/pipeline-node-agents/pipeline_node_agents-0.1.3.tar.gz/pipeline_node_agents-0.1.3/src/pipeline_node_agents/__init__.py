"""Pipeline Node Agents - A framework for building LLM-powered pipelines."""

from pipeline_node_agents.core.node import FunctionNode, AgentNode
from pipeline_node_agents.core.pipeline import Pipeline
from pipeline_node_agents.examples.conditioning_pipeline import ConditioningPipeline
from pipeline_node_agents.examples.input_checker_pipeline import InputCheckerPipeline
from pipeline_node_agents.examples.random_mean_pipeline import RandomMeanPipeline
from pipeline_node_agents.examples.random_mean_pipeline_crewai import RandomMeanPipelineCrewAI
from pipeline_node_agents.examples.search_and_summarize import SearchAndSummarizePipeline
from pipeline_node_agents.examples.trip_planner.pipeline import TripPlannerPipeline
from pipeline_node_agents.core.logger_bootstrap import init_pipeline_logger
from pipeline_node_agents.core.logging_config import get_logger


__version__ = "0.1.3"
__all__ = ["FunctionNode", "AgentNode", "Pipeline", "greet", "ConditioningPipeline", "InputCheckerPipeline", 
           "RandomMeanPipeline", "RandomMeanPipelineCrewAI", "SearchAndSummarizePipeline", "TripPlannerPipeline",
           "init_pipeline_logger", "get_logger"]


def greet(name: str = "World") -> str:
    """Simple greeting function to verify the package works."""
    return f"Hello, {name}! Pipeline Node Agents v{__version__} is working."
