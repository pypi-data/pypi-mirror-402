import os, sys
import time
import argparse
import logging

os.environ["OLLAMA_HOST"] = "http://localhost:11434"

from pipeline_node_agents.adapters.python_fn_adapter import PythonFnAdapter
from pipeline_node_agents.adapters.crewai_adapter import CrewAIAdapter
from pipeline_node_agents.core.node import FunctionNode, AgentNode
from pipeline_node_agents.core.pipeline import Pipeline
from crewai import Agent, LLM
from pipeline_node_agents.core.logger_bootstrap import init_pipeline_logger
from pipeline_node_agents.core.logging_config import get_logger


class InputCheckerPipeline:
    """
    A pipeline that validates user-provided city names using a geographical expert agent.
    """

    def __init__(self, ollama_llm=None, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger(__name__)

        self.ollama_llm = ollama_llm or LLM(
            model="ollama/llama3.2",
            base_url="http://localhost:11434"
        )

        self.input_validator_agent = Agent(
            name="GeographicalExpertAgent",
            role="Expert in geographical locations and settlements.",
            goal="Check whether the provided list of cities are real settlements on Earth.",
            backstory="You are a highly skilled geographical expert.",
            llm=self.ollama_llm
        )

    def get_user_input(self, input_parameters: dict[str, str]) -> dict:
        """
        Get string input fields from user.

        Args:
            input_parameters: dict mapping parameter names to their descriptions

        Returns:
            dict mapping parameter names to user-provided values
        """
        result = {}
        for name, description in input_parameters.items():
            value = input(description + ": ")
            result[name] = value
        return result

    def get_validation_result(self, validation_summary: str) -> bool:
        is_valid = "false" not in validation_summary.lower()
        return is_valid

    def run(self, loop: bool = False) -> dict:
        self.logger.info("Starting InputCheckerPipeline")

        user_input_node = FunctionNode(
            name="UserInputNode",
            adapter=PythonFnAdapter(self.get_user_input),
            inputs=["input_parameters"],
            output="list_of_cities"
        )

        input_validator_node = AgentNode(
            name="InputValidatorNode",
            adapter=CrewAIAdapter(
                self.input_validator_agent,
                task_description="Validate this statement: 'In the LIST_OF_CITIES all entries are populated places.' Say whether it is True or False.",
                expected_output="Brief explanation of the validation result. The last word MUST contain either 'True' or 'False' based on the validity of the statement."
            ),
            inputs=["list_of_cities"],
            output="validation_summary"
        )

        input_validation_result_node = FunctionNode(
            name="InputValidationResultNode",
            adapter=PythonFnAdapter(self.get_validation_result),
            inputs=["validation_summary"],
            output="is_valid"
        )

        main_pipeline = Pipeline(nodes=[user_input_node, input_validator_node, input_validation_result_node])

        if loop:
            main_pipeline.add_edge(
                "InputValidationResultNode",
                "UserInputNode",
                condition=lambda ctx: ctx.get("is_valid") == False
            )

        context = {"input_parameters": {"list_of_cities": "Enter list of cities"}}

        start_time = time.perf_counter()
        result = main_pipeline.run(context)
        elapsed_time = time.perf_counter() - start_time

        time.sleep(0.1)
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

        print("\n✅ Final Pipeline Output:")
        print("Validation summary:", result.get("validation_summary"))
        print(f"\n⏱️  Execution time: {elapsed_time:.2f} seconds\n")
        print("Is input valid:", result.get("is_valid"))

        self.logger.info("⏱️  Execution time: %.2f seconds", elapsed_time)
        self.logger.info("✅Final Pipeline Output:\n validation_summary: %s\n is_valid: %s",
                         result.get('validation_summary'), result.get('is_valid'))

        return result


def main():
    parser = argparse.ArgumentParser(description="Input checker pipeline")
    parser.add_argument("--loop", type=lambda x: x.lower() == 'true', default=False,
                        help="Enable loopback to UserInputNode if input is invalid (True/False)")
    args = parser.parse_args()

    init_pipeline_logger(pipeline_name="input_checker_pipeline")
    logger = get_logger(__name__)

    pipeline = InputCheckerPipeline(logger=logger)
    pipeline.run(loop=args.loop)


if __name__ == "__main__":
    main()