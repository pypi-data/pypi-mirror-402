from pipeline_node_agents.adapters.base_adapter import BaseAdapter

class PythonFnAdapter(BaseAdapter):
    """Adapter for wrapping simple Python functions."""

    def __init__(self, fn):
        self.fn = fn

    def invoke(self, **kwargs):
        result = self.fn(**kwargs)
        return result