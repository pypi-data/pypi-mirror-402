"""
amux - Multi-agent coordination for AI coding assistants.

This is an alias package for 'devswarm'. All functionality is provided by devswarm.

    pip install devswarm

For documentation, see: https://github.com/jude-hawrani/devswarm
"""

# Re-export everything from devswarm
from devswarm import CoordinatorClient, load_config, find_config_file, main, __version__

__all__ = ["CoordinatorClient", "load_config", "find_config_file", "main", "__version__"]


def _main():
    """Entry point for amux CLI - redirects to devswarm."""
    from devswarm.cli import main as devswarm_main
    import sys
    sys.exit(devswarm_main())
