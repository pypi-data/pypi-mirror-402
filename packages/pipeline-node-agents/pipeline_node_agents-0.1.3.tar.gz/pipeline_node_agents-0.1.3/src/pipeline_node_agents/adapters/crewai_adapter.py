from pipeline_node_agents.adapters.base_adapter import BaseAdapter
from crewai import Agent, Task, Crew
from pipeline_node_agents.core.logging_config import get_logger

logger = get_logger(__name__)

class CrewAIAdapter(BaseAdapter):
    def __init__(self, agent_or_crew, task_description: str = None, expected_output: str = None):
        self.entity = agent_or_crew
        self.task_description = task_description
        self.expected_output = expected_output or "A detailed analysis based on the input."

    def invoke(self, **kwargs):
        if isinstance(self.entity, Agent):
            input_text = "\n\n".join(f"### {k.upper()} ###\n{v}" for k, v in kwargs.items())
            
            description = self.task_description or self.entity.goal or "Process this input"
            
            full_description = f"""YOUR TASK: {description}

Based on the following content, complete the task above. Focus specifically on answering the task.

---
{input_text}
---

Remember: {description}"""

            task = Task(
                description=full_description,
                agent=self.entity,
                expected_output=self.expected_output
            )

            logger.info(f"Full task description: {full_description}")
            logger.info(f"Expected output: {self.expected_output}")
            logger.info(f"Input length: {len(input_text)} chars")
            
            crew = Crew(agents=[self.entity], tasks=[task])
            output = crew.kickoff()

            logger.info(f"Output of the agent: \n{output}\n\n")
            return str(output)

        elif hasattr(self.entity, "kickoff"):
            output = self.entity.kickoff(inputs=kwargs)
            return str(output)
        
        else:
            raise ValueError("Entity must be a CrewAI Agent or Crew.")