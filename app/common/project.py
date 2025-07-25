from enum import Enum

# ENUM for Project Status


class ProjectStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


# ENUM for Project Type
class ProjectType(str, Enum):
    KANBAN = "KANBAN"
    LIST = "LIST"
    GANTT = "GANTT"
