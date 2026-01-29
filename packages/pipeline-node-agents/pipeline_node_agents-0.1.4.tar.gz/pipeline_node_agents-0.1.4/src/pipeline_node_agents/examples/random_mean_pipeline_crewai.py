import os, sys
import random, time
import logging

os.environ["OLLAMA_HOST"] = "http://localhost:11434"

from pipeline_node_agents.adapters.python_fn_adapter import PythonFnAdapter
from pipeline_node_agents.adapters.crewai_adapter import CrewAIAdapter
from pipeline_node_agents.core.node import FunctionNode, AgentNode
from pipeline_node_agents.core.pipeline import Pipeline
from crewai import Agent, LLM
from pipeline_node_agents.core.logger_bootstrap import init_pipeline_logger
from pipeline_node_agents.core.logging_config import get_logger


class RandomMeanPipelineCrewAI:
    """
    A single-run pipeline that generates random numbers and summarizes them using CrewAI.
    """

    def __init__(self, ollama_llm=None, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger(__name__)

        self.ollama_llm = ollama_llm or LLM(
            model="ollama/llama3.2",
            base_url="http://localhost:11434"
        )

        self.number_summary_agent = Agent(
            name="NumberSummaryAgent",
            role="Expert in statistics",
            goal="Receive a list of numbers and return a brief textual summary",
            backstory="Expert in statistics and data analysis with years of experience.",
            llm=self.ollama_llm
        )

    # --- Function Node 1: Generate random numbers ---
    def generate_random_numbers(self, limit: int) -> list[float]:
        numbers = [random.uniform(0, limit) for _ in range(10)]
        return numbers

    def run(self) -> dict:
        self.logger.info("Starting RandomMeanPipelineCrewAI")

        # Node 1: Generate random numbers
        node1 = FunctionNode(
            name="RandomNumberGenerator",
            adapter=PythonFnAdapter(self.generate_random_numbers),
            inputs=["limit"],
            output="random_numbers"
        )

        # Node 2: CrewAI summarization
        node2 = AgentNode(
            name="NumberSummaryNode",
            adapter=CrewAIAdapter(self.number_summary_agent),
            inputs=["random_numbers"],
            output="summary"
        )

        pipeline = Pipeline(nodes=[node1, node2])

        context = {"limit": 5}

        start_time = time.perf_counter()
        result = pipeline.run(context)
        elapsed = time.perf_counter() - start_time

        time.sleep(0.1)
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

        print()
        print(f"✅ Final Pipeline Output:\n{result.get('summary')}")
        print()
        print(f"⏱️  Execution time: {elapsed:.2f} seconds")
        print()

        self.logger.info("✅ Final Pipeline Output: %s", result.get('summary'))
        self.logger.info("⏱️  Execution time: %.2f seconds", elapsed)

        return result


if __name__ == "__main__":
    init_pipeline_logger(pipeline_name="random_mean_pipeline_crewai")
    logger = get_logger(__name__)
    pipeline = RandomMeanPipelineCrewAI(logger=logger)
    pipeline.run()