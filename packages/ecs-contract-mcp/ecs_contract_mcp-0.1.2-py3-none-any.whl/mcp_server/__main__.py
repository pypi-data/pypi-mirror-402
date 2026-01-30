"""Module entry point for `python -m mcp_server`"""

# CRITICAL: Configure logging BEFORE any other imports
# This ensures mcp package and all other modules output to stderr
# instead of stdout (which is used for MCP JSON protocol communication)
import logging
import sys

# Remove any existing handlers and configure root logger to use stderr
root_logger = logging.getLogger()
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

stderr_handler = logging.StreamHandler(sys.stderr)
stderr_handler.setFormatter(logging.Formatter("%(message)s"))
root_logger.addHandler(stderr_handler)
root_logger.setLevel(logging.INFO)

# Now import and run the server
from mcp_server.server import main

if __name__ == "__main__":
    main()
