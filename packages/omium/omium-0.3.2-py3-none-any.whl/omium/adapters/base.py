from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from pathlib import Path

@dataclass
class WorkflowDefinition:
    """Represents a discovered workflow."""
    id: str
    name: str
    type: str  # "langgraph", "crewai", etc.
    definition: Dict[str, Any]
    config: Dict[str, Any] = field(default_factory=dict)
    source_file: Optional[str] = None
    description: Optional[str] = None

class BaseAdapter(ABC):
    """Base class for framework adapters."""
    
    @property
    @abstractmethod
    def framework_name(self) -> str:
        """Name of the framework (e.g., 'langgraph', 'crewai')."""
        pass

    @abstractmethod
    def can_handle(self, file_path: Path) -> bool:
        """Check if this adapter can handle the given file."""
        pass

    @abstractmethod
    def extract_workflows(self, file_path: Path) -> List[WorkflowDefinition]:
        """Extract workflows from the file."""
        pass
