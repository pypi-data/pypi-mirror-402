from __future__ import annotations
from atlassian import Jira
import json
from fastmcp import FastMCP
import os
from typing import Annotated
from pydantic import Field


JIRA_URL = os.getenv("JIRA_URL")
TOKEN = os.getenv("JIRA_PERSONAL_TOKEN")


jira_mcp = FastMCP("MCP Jira")


def get_jira_client():
    if not TOKEN:
        raise ValueError("JIRA_PERSONAL_TOKEN missing!")
    
    jira = Jira(
        url=JIRA_URL,
        token=TOKEN,
        verify_ssl=True
    )

    jira.session.headers.update({"Authorization": f"Bearer {TOKEN}"})
    return jira

@jira_mcp.tool(
    name="jira_get_remote_links",
    description="Lists the remote links connected to a given Jira task.",
    tags=["jira", "read"],
    annotations={"title": "get_remote_links", "readOnlyHint": True}
)
def get_remote_links(issue_key: Annotated[str, Field(description="Jira issue key (e.g., 'PROJ-2495')")]) -> str:
    """
    Retrieves 'Remote Links' and Wiki pages associated with a Jira task (Issue).

    Args:
        issue_key: Jira task ID (e.g., PROJ-2495, PROJ-2945). Not just the number, but the project code must also be included.

    Returns:
        URL list in JSON format.
    """
    try:
        jira = get_jira_client()
        response = jira.get_issue_remotelinks(issue_key)
        links = map(lambda x: x['object']['url'], response)
        return json.dumps(list(links), indent=2, ensure_ascii=False)
        
    except Exception as e:
        return f"Error occurred: {str(e)}"

def main():
    jira_mcp.run()

if __name__ == "__main__":
    main()