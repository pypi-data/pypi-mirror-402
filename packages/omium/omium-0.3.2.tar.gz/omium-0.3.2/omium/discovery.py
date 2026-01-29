import os
from pathlib import Path
from typing import List, Type
from .adapters.base import BaseAdapter, WorkflowDefinition
from .adapters.langgraph import LangGraphAdapter
from .output import print_info, print_warning

# Registry of available adapters
ADAPTERS: List[Type[BaseAdapter]] = [
    LangGraphAdapter
]

class DiscoveryEngine:
    """Engine for discovering workflows in a project."""
    
    def __init__(self):
        self.adapters = [adapter_cls() for adapter_cls in ADAPTERS]

    def scan_directory(self, root_path: Path) -> List[WorkflowDefinition]:
        """Scan a directory for valid workflows."""
        discovered = []
        
        # Walk through directory
        for root, dirs, files in os.walk(root_path):
            # Skip hidden directories and common ignore patterns
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["__pycache__", "venv", "env", "node_modules"]]
            
            for file in files:
                file_path = Path(root) / file
                
                # Check each adapter
                for adapter in self.adapters:
                    if adapter.can_handle(file_path):
                        try:
                            workflows = adapter.extract_workflows(file_path)
                            if workflows:
                                print_info(f"Discovered {len(workflows)} {adapter.framework_name} workflow(s) in {file}")
                                discovered.extend(workflows)
                        except Exception as e:
                            print_warning(f"Error scanning {file} with {adapter.framework_name}: {e}")
                            
        return discovered

def discover_workflows(root_path: Path) -> List[WorkflowDefinition]:
    """Helper function to run discovery."""
    engine = DiscoveryEngine()
    return engine.scan_directory(root_path)
