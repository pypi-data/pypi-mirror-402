import os, sys
import random, time
import logging

os.environ["OLLAMA_HOST"] = "http://localhost:11434"

from pipeline_node_agents.adapters.python_fn_adapter import PythonFnAdapter
from pipeline_node_agents.adapters.crewai_adapter import CrewAIAdapter
from pipeline_node_agents.core.node import FunctionNode, AgentNode
from pipeline_node_agents.core.pipeline import Pipeline
from crewai import Agent, LLM
from pipeline_node_agents.tools.scraper import Scraper
from pipeline_node_agents.tools.websearch import WebSearcher
from pipeline_node_agents.core.logger_bootstrap import init_pipeline_logger
from pipeline_node_agents.core.logging_config import get_logger


class ConditioningPipeline:
    """
    A pipeline that demonstrates conditional branching based on a coin flip.
    Goes to park (LocalExpertNode) on heads, cinema (CinemaExpertNode) on tails.
    """

    def __init__(self, ollama_llm=None, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger(__name__)

        self.ollama_llm = ollama_llm or LLM(
            model="ollama/llama3.2",
            base_url="http://localhost:11434"
        )

        self.cinema_expert_agent = Agent(
            name="CinemaExpertAgent",
            role="Expert in cinema and film recommendations.",
            goal="Provide the best film recommendation based on text content.",
            backstory="You are a highly skilled cinema expert.",
            llm=self.ollama_llm
        )

        self.local_expert_agent = Agent(
            name="LocalExpertAgent",
            role="Local Expert in defined city.",
            goal="Provide the best recommendation where to go in defined city based on text content.",
            backstory="You are a highly skilled local expert of defined city.",
            llm=self.ollama_llm
        )

    def flip_coin(self) -> bool:
        """Flip a coin and return True (heads) or False (tails)."""
        choice = random.choice([True, False])
        self.logger.info("[DecisionNode] Coin flip result: %s",
                         'True -> Going to park!' if choice else 'False -> Going to cinema!')
        return choice

    def run(self) -> dict:
        self.logger.info("Starting ConditioningPipeline")

        decision_node = FunctionNode(
            name="DecisionNode",
            adapter=PythonFnAdapter(self.flip_coin),
            inputs=[],
            output="decision"
        )

        search_node = FunctionNode(
            name="DuckDuckGoSearchNode",
            adapter=PythonFnAdapter(WebSearcher.duckduckgo_search),
            inputs=["query", "max_results"],
            output="search_results"
        )

        scrape_node = FunctionNode(
            name="ScrapeNode",
            adapter=PythonFnAdapter(Scraper.scrape),
            inputs=["search_results"],
            output="page_content"
        )

        local_expert_node = AgentNode(
            name="LocalExpertNode",
            adapter=CrewAIAdapter(
                self.local_expert_agent,
                task_description="Recommend places based on provided context to go in defined city.",
                expected_output="2-3 top places of this city with short descriptions."
            ),
            inputs=["city", "type_of_place"],
            output="summary"
        )

        cinema_expert_node = AgentNode(
            name="CinemaExpertNode",
            adapter=CrewAIAdapter(
                self.cinema_expert_agent,
                task_description="Analyze the provided text content and recommend a film to go in cinema.",
                expected_output="A single film recommendation with 2-3 highlights of this film."
            ),
            inputs=["page_content"],
            output="summary"
        )

        main_pipeline = Pipeline(start_node=decision_node)
        main_pipeline.add_node(decision_node)
        main_pipeline.add_node(local_expert_node)
        main_pipeline.add_pipeline(Pipeline(nodes=[search_node, scrape_node, cinema_expert_node]))

        main_pipeline.add_edge(
            "DecisionNode",
            "LocalExpertNode",
            condition=lambda ctx: ctx["decision"] is True
        )
        main_pipeline.add_edge(
            "DecisionNode",
            "DuckDuckGoSearchNode",
            condition=lambda ctx: ctx["decision"] is False
        )

        # default query: imdb showtimes
        context = {"query": "imdb showtimes", "max_results": 5, "city": "Vienna", "type_of_place": "parks"}

        start_time = time.perf_counter()
        result = main_pipeline.run(context)
        elapsed_time = time.perf_counter() - start_time

        time.sleep(0.1)
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

        print("\n✅ Final Pipeline Output:")
        print(result.get("summary"))
        print(f"\n⏱️  Execution time: {elapsed_time:.2f} seconds")

        self.logger.info("✅Final Pipeline Output: %s", result.get('summary'))
        self.logger.info("⏱️  Execution time: %.2f seconds", elapsed_time)

        return result


def main():
    init_pipeline_logger(pipeline_name="conditioning_pipeline")
    logger = get_logger(__name__)

    pipeline = ConditioningPipeline(logger=logger)
    pipeline.run()


if __name__ == "__main__":
    main()