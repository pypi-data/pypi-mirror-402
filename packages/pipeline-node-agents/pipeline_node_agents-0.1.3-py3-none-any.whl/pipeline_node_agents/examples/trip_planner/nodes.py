from pipeline_node_agents.adapters.python_fn_adapter import PythonFnAdapter
from pipeline_node_agents.adapters.crewai_adapter import CrewAIAdapter
from pipeline_node_agents.core.node import FunctionNode, AgentNode
from pipeline_node_agents.examples.trip_planner.agents import TripPlannerAgents
from pipeline_node_agents.examples.trip_planner.functions import TripPlannerFunctions


class TripPlannerNodes:
    @classmethod
    def get_research_cities_node(cls) -> FunctionNode:
        return FunctionNode(
            name="ResearchCitiesNode",
            adapter=PythonFnAdapter(TripPlannerFunctions.research_cities),
            inputs=["list_of_cities", "dates"],
            output="weather_summaries"
        )

    @classmethod
    def get_city_selection_node(cls) -> AgentNode:
        return AgentNode(
            name="CitySelectionNode",
            adapter=CrewAIAdapter(
                TripPlannerAgents.get_city_selection_agent(),
                task_description="Choose one city from the provided list based on the weather summaries.",
                expected_output="First line: Chosen city name. Following lines: brief explanation of why this city was chosen."
            ),
            inputs=["weather_summaries"],
            output="chosen_city_summary"
        )

    @classmethod
    def get_extract_chosen_city_node(cls) -> FunctionNode:
        return FunctionNode(
            name="ExtractChosenCityNode",
            adapter=PythonFnAdapter(TripPlannerFunctions.extract_chosen_city),
            inputs=["chosen_city_summary"],
            output="chosen_city"
        )

    @classmethod
    def get_local_expert_node(cls) -> AgentNode:
        return AgentNode(
            name="LocalExpertNode",
            adapter=CrewAIAdapter(
                TripPlannerAgents.get_local_expert_agent(),
                task_description="Gather insights about key attractions, food places, and daily activity recommendations of the chosen city.",
                expected_output="City guide including hidden gems, cultural hotspots, and practical travel tips"
            ),
            inputs=["chosen_city", "dates"],
            output="list_of_attractions"
        )

    @classmethod
    def get_travel_concierge_node(cls) -> AgentNode:
        return AgentNode(
            name="TravelConciergeNode",
            adapter=CrewAIAdapter(
                TripPlannerAgents.get_travel_concierge_agent(),
                task_description="Plan a 7-day trip itinerary based on the chosen city and provided information.",
                expected_output="Detailed 7-day itinerary including daily activities, dining options, and transportation tips.",
            ),
            inputs=["chosen_city", "list_of_attractions", "dates"],
            output="trip_itinerary"
        )