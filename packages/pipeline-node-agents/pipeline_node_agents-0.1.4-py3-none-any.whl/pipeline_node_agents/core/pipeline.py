from __future__ import annotations
from pipeline_node_agents.core.helpers.pipeline_visualizer import PipelineVisualizer
from pipeline_node_agents.core.logging_config import get_logger

logger = get_logger(__name__)


class Pipeline:
    """Executes nodes in a defined order and manages shared context."""

    def __init__(self, *, nodes: list["Node"] | None = None, start_node: "Node" | None = None):
        """
        Create a pipeline either from a list of nodes (linear pipeline)
        or from a single start node (graph-based pipeline).

        Exactly one of `nodes` or `start_node` must be provided.
        """
        if (nodes is None and start_node is None) or (nodes is not None and start_node is not None):
            raise ValueError(
                "Exactly one of 'nodes' or 'start_node' must be provided."
            )

        self.nodes: dict[str, Node] = {}
        self.edges: dict[str, list[tuple[str, str]]] = {}

        if nodes is not None:
            self.start_node = nodes[0].name
            self._build_linear_pipeline(nodes)
        else:
            self.start_node = start_node.name
            self.add_node(start_node)


    def add_node(self, node):
        self.nodes[node.name] = node

    def add_edge(self, from_node, to_node, condition=None):
        """
        condition: None | callable(context) -> bool
        """
        self.edges.setdefault(from_node, []).append((condition, to_node))

    def add_pipeline(self, other_pipeline):
        """
        Adds all nodes and edges from another pipeline into this pipeline.
        """

        for node_name, node in other_pipeline.nodes.items():
            if node_name in self.nodes:
                raise ValueError(f"Node '{node_name}' already exists in pipeline")
            self.nodes[node_name] = node

        for from_node, transitions in other_pipeline.edges.items():
            for condition, to_node in transitions:
                self.edges.setdefault(from_node, []).append((condition, to_node))

    def run(self, initial_context=None, start_node=None):
        context = initial_context or {}
        current_node = start_node or self.start_node

        logger.info("=== Starting pipeline ===")
        
        logger.info("")
        PipelineVisualizer.visualize(self.edges, self.start_node)    
        logger.info("")

        if current_node is None:
            raise ValueError("No start node defined for the pipeline.")

        while current_node:
            node = self.nodes[current_node]
            logger.info(f"→ Running node: {node.name}")
            context = node.run(context)

            next_node = None
            for condition, target in self.edges.get(current_node, []):
                if condition is None or condition(context):
                    next_node = target
                    break

            current_node = next_node

        logger.info("=== Pipeline finished ===")
        return context

    def _build_linear_pipeline(self, nodes):
        for node in nodes:
            self.add_node(node)

        for i in range(len(nodes) - 1):
            self.add_edge(
                from_node=nodes[i].name,
                to_node=nodes[i + 1].name,
                condition=None
            )

        self.start_node = nodes[0].name