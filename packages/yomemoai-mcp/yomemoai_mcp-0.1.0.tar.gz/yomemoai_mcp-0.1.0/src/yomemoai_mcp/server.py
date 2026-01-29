import asyncio
from mcp.server.fastmcp import FastMCP
from .client import MemoClient
import os

from dotenv import load_dotenv
load_dotenv()

mcp = FastMCP("yomemoai")

API_KEY = os.getenv("MEMO_API_KEY", "")
PRIV_KEY_PATH = os.getenv("MEMO_PRIVATE_KEY_PATH", "private.pem")
BASE_URL = os.getenv("MEMO_BASE_URL", "https://api.yomemo.ai")

if not API_KEY:
    raise ValueError("MEMO_API_KEY environment variable is required")

if not os.path.exists(PRIV_KEY_PATH):
    raise FileNotFoundError(
        f"Private key file not found: {PRIV_KEY_PATH}. "
        f"Please set MEMO_PRIVATE_KEY_PATH environment variable or place your private key at {PRIV_KEY_PATH}"
    )

try:
    with open(PRIV_KEY_PATH, "r") as f:
        private_pem = f.read()
except Exception as e:
    raise IOError(f"Failed to read private key from {PRIV_KEY_PATH}: {e}")

if not private_pem.strip():
    raise ValueError(f"Private key file {PRIV_KEY_PATH} is empty")

client = MemoClient(API_KEY, private_pem, BASE_URL)


@mcp.tool()
async def save_memory(content: str, handle: str = "general", description: str = "") -> str:
    """
    Store important information, user preferences, or conversation context as a permanent memory.
    Use this tool when the user explicitly asks to 'remember', 'save', or 'keep track of' something.

    :param content: The actual text/information to be remembered. Be concise but maintain context.
    :param handle: A short, unique category or tag (e.g., 'work', 'personal', 'project-x'). Defaults to 'general'.
    :param description: A brief summary of what this memory is about to help with future identification. don't include any sensitive information.
    """
    try:
        result = client.add_memory(
            content, handle=handle, description=description)
        return f"Successfully archived in memory. ID: {result.get('memory_id')}"
    except Exception as e:
        return f"Failed to save memory: {str(e)}"


@mcp.tool()
async def load_memories(handle: str = None) -> str:
    """
    Retrieve previously stored memories or context. 
    Use this tool when the user asks 'what do you remember about...', 'check my notes on...', or when 
    you need historical context to answer a question accurately.

    :param handle: Optional filter. If the user specifies a category (e.g., 'about my job'), 
                   extract and provide the relevant handle.
    """
    try:
        memories = client.get_memories(handle=handle)
        if not memories:
            return f"No memories found under the handle: {handle if handle else 'all'}."

        output = ["### Retrieved Memories:"]
        for m in memories:
            timestamp = m.get('created_at', 'N/A')
            output.append(
                f"Handle: [{m.get('handle')}]\nContent: {m.get('content')}\n---"
            )
        return "\n".join(output)
    except Exception as e:
        return f"Error retrieving memories: {str(e)}"

if __name__ == "__main__":
    mcp.run()
