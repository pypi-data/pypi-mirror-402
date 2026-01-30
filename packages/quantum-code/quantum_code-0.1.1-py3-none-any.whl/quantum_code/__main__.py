"""Enable running quantum_code as a module: python -m quantum_code.

Runs the MCP server (matching official MCP server patterns).
For CLI usage, use the 'quantum' command instead.
"""

from quantum_code.server import main

if __name__ == "__main__":
    main()
