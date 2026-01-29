import os, sys
import time
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


class SearchAndSummarizePipeline:
    """
    A pipeline that searches the web and summarizes results using a business analyst agent.
    """

    def __init__(self, ollama_llm=None, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger(__name__)

        self.ollama_llm = ollama_llm or LLM(
            model="ollama/llama3.2",
            base_url="http://localhost:11434"
        )

        self.analyst_agent = Agent(
            name="AnalystAgent",
            role="Expert business analyst.",
            goal="Provide the best country for business based on text content.",
            backstory="You are a highly skilled business analyst.",
            llm=self.ollama_llm
        )

    def run(self) -> dict:
        self.logger.info("Starting SearchAndSummarizePipeline")

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

        analyst_node = AgentNode(
            name="AnalystNode",
            adapter=CrewAIAdapter(
                self.analyst_agent,
                task_description="Analyze the provided text content and determine the best country for business. Explain your reasoning based on the information given.",
                expected_output="A single country recommendation with 2-3 bullet points explaining why it's the best choice."
            ),
            inputs=["page_content"],
            output="summary"
        )

        pipeline = Pipeline(nodes=[search_node, scrape_node, analyst_node])

        context = {"query": "best country for business", "max_results": 5}

        start_time = time.perf_counter()
        result = pipeline.run(context)
        elapsed_time = time.perf_counter() - start_time

        # Workaround for Rich FileProxy recursion issue
        time.sleep(0.1)
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

        print(f"\n⏱️  Execution time: {elapsed_time:.2f} seconds\n")

        print("\n✅ Final Pipeline Output:")
        print(result.get("summary"))

        self.logger.info("✅Final Pipeline Output:\n%s", result.get('summary'))
        self.logger.info("⏱️  Execution time: %.2f seconds", elapsed_time)

        return result


def main():
    init_pipeline_logger(pipeline_name="search_and_summarize_pipeline")
    logger = get_logger(__name__)

    pipeline = SearchAndSummarizePipeline(logger=logger)
    pipeline.run()


if __name__ == "__main__":
    main()