from setuptools import setup
from setuptools.command.build_py import build_py
import subprocess
import sys
from pathlib import Path


class BuildPyCommand(build_py):
    """Custom build command that generates proto files before building."""

    def run(self):
        """Run proto generation before building."""
        # Import and run proto generation
        try:
            from build_proto import generate_proto_files
            generate_proto_files()
        except ImportError:
            # If build_proto.py doesn't exist, try running it as a script
            build_proto_path = Path(__file__).parent / "build_proto.py"
            if build_proto_path.exists():
                subprocess.check_call([sys.executable, str(build_proto_path)])
        except Exception as e:
            print(f"Warning: Proto generation failed: {e}")
            print("Continuing build anyway - proto files may need manual generation")
        
        # Run normal build
        super().run()


# All metadata and dependencies are defined in pyproject.toml (PEP 621).
# This file hooks into the build process to generate proto files.
setup(cmdclass={"build_py": BuildPyCommand})
