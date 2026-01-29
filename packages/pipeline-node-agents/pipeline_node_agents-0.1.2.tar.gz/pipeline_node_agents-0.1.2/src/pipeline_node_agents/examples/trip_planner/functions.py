import time, sys
from pipeline_node_agents.adapters.python_fn_adapter import PythonFnAdapter
from pipeline_node_agents.adapters.crewai_adapter import CrewAIAdapter
from pipeline_node_agents.core.node import FunctionNode, AgentNode
from pipeline_node_agents.core.pipeline import Pipeline
from pipeline_node_agents.tools.scraper import Scraper
from pipeline_node_agents.tools.websearch import WebSearcher
from pipeline_node_agents.examples.trip_planner.agents import TripPlannerAgents
from pipeline_node_agents.core.logging_config import get_logger

logger = get_logger(__name__)

class TripPlannerFunctions:
    @staticmethod
    def format_dict_as_sections(data: dict[str, str]) -> str:
        """Format a dictionary into sections with headers."""
        lines = []
        for key, value in data.items():
            lines.append(f"### {key}")
            lines.append("")
            lines.append(str(value))
            lines.append("")
        return "\n".join(lines).strip()

    @staticmethod
    def research_cities(list_of_cities: list[str], dates: tuple[str, str]) -> str:
        """Choose a city out of the list with the best weather on provided dates."""
        weather_summaries = {}
        
        for city in list_of_cities:
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

            weather_summary_node = AgentNode(
                name="WeatherSummaryNode",
                adapter=CrewAIAdapter(
                    TripPlannerAgents.get_summary_agent(),
                    task_description=f"Analyze the provided text and summarize information about weather in {city} around dates {dates[0]} and {dates[1]}.",
                    expected_output="Short summary of the weather information."
                ),
                inputs=["page_content"],
                output="summary"
            )

            city_pipeline = Pipeline(nodes=[search_node, scrape_node, weather_summary_node])
            city_context = {"query": f"weather forecast {city} from {dates[0]} to {dates[1]}", "max_results": 5}
            result = city_pipeline.run(city_context)

            time.sleep(0.1)
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__

            print(f"\n✅ Pipeline Output of {city}:")
            print(result.get("summary"))

            logger.info(f"✅Pipeline Output of {city}:\n{result.get('summary')}")

            weather_summaries[city] = result.get("summary")

        return TripPlannerFunctions.format_dict_as_sections(weather_summaries)

    @staticmethod
    def extract_chosen_city(chosen_city_summary: str) -> str:
        """Extract the chosen city from the agent's summary."""
        first_line = chosen_city_summary.splitlines()[0]
        chosen_city = first_line.strip()
        return chosen_city