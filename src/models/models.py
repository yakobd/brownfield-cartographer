from pydantic import BaseModel, Field
from typing import List, Optional, Dict
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