
# tests/test_utils.py
from feedflow.main import mcp
from importlib.metadata import version

def test_mcp_config():
    """Verify that the MCP instance in main.py is configured correctly."""
    assert mcp.name == "FeedFlow"

    expected_version = version("feedflow")
    assert mcp.version == expected_version
    
