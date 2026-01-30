"""Sequence processing tools for MuseScore MCP."""

from ..client import MuseScoreClient


def setup_sequence_tools(mcp, client: MuseScoreClient):
    """Setup sequence processing tools."""

    @mcp.tool()
    async def processSequence(sequence: list):
        """Process a sequence of commands.

        Args:
            sequence: A list of action dictionaries with 'action' and 'params' keys
        """
        return await client.send_command("processSequence", {"sequence": sequence})