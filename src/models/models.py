from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime

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


class Node(BaseModel):
    """Generic graph node representation for serialized knowledge graphs."""
    id: str
    type: str
    properties: Dict[str, Any] = Field(default_factory=dict)


class Edge(BaseModel):
    """Directed graph edge between two nodes."""
    source: str
    target: str
    relation: str


class KnowledgeGraph(BaseModel):
    """Container for graph nodes and edges."""
    nodes: List[Node] = Field(default_factory=list)
    edges: List[Edge] = Field(default_factory=list)