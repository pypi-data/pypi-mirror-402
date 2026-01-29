import random, time
from statistics import mean
import logging

from pipeline_node_agents.adapters.python_fn_adapter import PythonFnAdapter
from pipeline_node_agents.core.node import FunctionNode
from pipeline_node_agents.core.pipeline import Pipeline
from pipeline_node_agents.core.logger_bootstrap import init_pipeline_logger
from pipeline_node_agents.core.logging_config import get_logger


class RandomMeanPipeline:
    """
    A single-run pipeline that generates random numbers and calculates their mean.
    """

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger(__name__)

    # --- Function Node 1: Generate random numbers ---
    def generate_random_numbers(self, limit: int) -> list[float]:
        numbers = [random.uniform(0, limit) for _ in range(10)]
        time.sleep(1)
        return numbers

    # --- Function Node 2: Compute mean ---
    def calculate_mean(self, random_numbers: list[float]) -> float:
        result = mean(random_numbers)
        time.sleep(3)
        return result

    def run(self) -> dict:
        self.logger.info("Starting RandomMeanPipeline")

        node1 = FunctionNode(
            name="RandomNumberGenerator",
            adapter=PythonFnAdapter(self.generate_random_numbers),
            inputs=["limit"],
            output="random_numbers",
        )

        node2 = FunctionNode(
            name="MeanCalculator",
            adapter=PythonFnAdapter(self.calculate_mean),
            inputs=["random_numbers"],
            output="mean_value",
        )

        pipeline = Pipeline(nodes=[node1, node2])

        start_time = time.perf_counter()
        result = pipeline.run(initial_context={"limit": 5})
        elapsed = time.perf_counter() - start_time

        print()
        print(f"✅Final Pipeline Output:\n{result}")
        print()
        print(f"⏱️  Execution time: {elapsed:.2f} seconds")
        print()

        self.logger.info("✅Final Pipeline Output: %s", result)
        self.logger.info("⏱️  Execution time: %.2f seconds", elapsed)

        return result

if __name__ == "__main__":
    init_pipeline_logger(pipeline_name="random_mean_pipeline")
    logger = get_logger(__name__)
    pipeline = RandomMeanPipeline(logger=logger)
    pipeline.run()