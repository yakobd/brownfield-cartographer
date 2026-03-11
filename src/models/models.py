from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, SerializeAsAny


EdgeType = Literal[
    "CONTAINS",
    "CALLS",
    "DEPENDS_ON",
    "READS_FROM",
    "WRITES_TO",
    "DEFINES",
    "DECLARED_IN",
    "FEEDS",
]

class CodeEntity(BaseModel):
    """Represents a function, class, or constant within a file."""
    name: str
    type: str  # "function", "class", "async_def"
    line_start: int
    line_end: int
    docstring: Optional[str] = None

class FileNode(BaseModel):
    """The primary unit of the Surveyor's map."""
    file_path: str
    language: str  # "python", "sql", "yaml"
    file_size: int
    imports: List[str] = Field(default_factory=list)
    entities: List[CodeEntity] = Field(default_factory=list)
    git_last_modified: Optional[datetime] = None
    change_frequency: int = 0  # Git Velocity


class BaseNode(BaseModel):
    """Base graph node model used for specialized node types."""
    id: str
    type: str


class ModuleNode(BaseNode):
    """Represents a source module/file in the codebase."""
    type: Literal["module"] = "module"
    file_path: str
    language: str
    file_size: int
    imports: List[str] = Field(default_factory=list)
    change_frequency: int = 0


class DatasetNode(BaseNode):
    """Represents a logical data asset (table/file/topic)."""
    type: Literal["dataset"] = "dataset"
    dataset_name: str
    database: Optional[str] = None
    # 'schema' is a reserved Pydantic term. Using 'db_schema' with an alias fixes it.
    db_schema: Optional[str] = Field(default=None, alias="schema")
    
    class Config:
        populate_by_name = True  # Allows using 'schema' or 'db_schema' in code


class FunctionNode(BaseNode):
    """Represents a callable code entity inside a module."""
    type: Literal["function"] = "function"
    module_id: str
    function_name: str
    line_start: int
    line_end: int


class TransformationNode(BaseNode):
    """Represents a transformation unit, commonly SQL-centric."""
    type: Literal["transformation"] = "transformation"
    sql_dialect: Optional[str] = None
    source_datasets: List[str] = Field(default_factory=list)
    sink_datasets: List[str] = Field(default_factory=list)


class Node(BaseNode):
    """Backward-compatible generic node model."""
    properties: Dict[str, str] = Field(default_factory=dict)


class BaseEdge(BaseModel):
    """Directed graph edge between two nodes."""
    source: str
    target: str
    relation: EdgeType


class Edge(BaseEdge):
    """Backward-compatible edge alias."""
    pass


class KnowledgeGraph(BaseModel):
    """Container for graph nodes and edges."""
    nodes: List[SerializeAsAny[BaseNode]] = Field(default_factory=list)
    edges: List[SerializeAsAny[BaseEdge]] = Field(default_factory=list)