import sys
import os
import importlib.util
import inspect
import json
from pathlib import Path
from typing import List, Any
from .base import BaseAdapter, WorkflowDefinition
from ...output import print_warning, print_info

class LangGraphAdapter(BaseAdapter):
    """Adapter for LangGraph/LangChain workflows."""
    
    @property
    def framework_name(self) -> str:
        return "langgraph"

    def can_handle(self, file_path: Path) -> bool:
        """Check if file might contain LangGraph code."""
        if file_path.suffix != ".py":
            return False
            
        try:
            content = file_path.read_text(encoding="utf-8")
            indicators = [
                "langgraph",
                "StateGraph",
                "MessageGraph",
                "create_react_agent",
                "create_supervisor"
            ]
            return any(ind in content for ind in indicators)
        except:
            return False

    def extract_workflows(self, file_path: Path) -> List[WorkflowDefinition]:
        """Import module and find LangGraph objects."""
        active_workflows = []
        
        try:
            # Add project root to sys.path
            cwd = Path.cwd()
            if str(cwd) not in sys.path:
                sys.path.insert(0, str(cwd))

            # Determine module name relative to CWD
            try:
                rel_path = file_path.relative_to(cwd)
                module_name = str(rel_path.with_suffix("")).replace(os.sep, ".")
                
                # Use standard import mechanism which handles packages correctly
                module = importlib.import_module(module_name)
            except (ValueError, ImportError) as e:
                # If cannot resolve relative path or import fails, try direct loading
                # This is a fallback for scripts outside packages
                print_info(f"Fallback import for {file_path.name}: {e}")
                sys.path.insert(0, str(file_path.parent))
                spec = importlib.util.spec_from_file_location(file_path.stem, str(file_path))
                if not spec or not spec.loader:
                    return []
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

            # Scan for LangGraph objects
            for name, obj in inspect.getmembers(module):
                if name.startswith("_"):
                    continue
                
                # Check directly for compiled graph capabilities
                if hasattr(obj, "get_graph") or hasattr(obj, "stream"):
                    try:
                        definition = self._serialize_graph(obj)
                        if definition:
                            active_workflows.append(WorkflowDefinition(
                                id=f"{module_name}-{name}",
                                name=name.replace("_", " ").title(),
                                type="langgraph",
                                definition=definition,
                                source_file=str(file_path.name),
                                description=f"Auto-discovered from {file_path.name}:{name}"
                            ))
                    except Exception as e:
                        # Skip objects that fail during inspection
                        pass
                        
        except Exception as e:
            print_warning(f"Failed to analyze {file_path.name}: {e}")
            
        return active_workflows

    def _serialize_graph(self, graph_obj: Any) -> Any:
        """Serialize a LangGraph object to JSON format."""
        try:
            # Try to get the graph representation
            if hasattr(graph_obj, "get_graph"):
                 # xray=True is important for subgraphs
                graph = graph_obj.get_graph(xray=True)
                json_repr = graph.to_json()
                
                # Normalize for Omium schema
                return {
                    "nodes": json_repr.get("nodes", []),
                    "edges": json_repr.get("edges", []),
                    "type": "langgraph"
                }
        except:
            return None
        return None
