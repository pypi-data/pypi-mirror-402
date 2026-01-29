from datetime import datetime
from pathlib import Path

from pipeline_node_agents.core.helpers.paths import get_project_root
from pipeline_node_agents.core.logging_config import configure_logging


def init_pipeline_logger(
    pipeline_name: str,
    project_root: str | None = None,
    log_subdir: str = "logs",
    level: str = "INFO",
):
    if project_root is None:
        project_root = get_project_root()
    else:
        project_root = Path(project_root)
    log_root = project_root / log_subdir

    timestamp = datetime.now().strftime("%d_%m_%y__%H_%M_%S")

    log_file = (
        log_root
        / pipeline_name
        / f"{pipeline_name}_run_{timestamp}.log"
    )

    configure_logging(log_file=log_file, level=level)

    return log_file
