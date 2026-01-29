"""
amux - Multi-agent coordination for AI coding assistants.

This is an alias package for 'claude-co'. All functionality is provided by claude-co.

    pip install claude-co

For documentation, see: https://github.com/jude-hawrani/claude-co
"""

# Re-export everything from claude-co
from claude_co import CoordinatorClient, load_config, find_config_file, main, __version__

__all__ = ["CoordinatorClient", "load_config", "find_config_file", "main", "__version__"]


def _main():
    """Entry point for amux CLI - redirects to claude-co."""
    from claude_co.cli import main as claude_co_main
    import sys
    sys.exit(claude_co_main())
