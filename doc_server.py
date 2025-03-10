from mcp.server.fastmcp import FastMCP
import os
from pathlib import Path

# Create a documentation server
mcp = FastMCP("Documentation Server")

@mcp.resource("file://{path}")
def read_file(path: str) -> str:
    """Read file contents for Claude to use as context"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

@mcp.tool()
def save_documentation(file_path: str, content: str) -> str:
    """Save generated documentation to a file"""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Write content to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return f"Documentation saved to {file_path}"
    except Exception as e:
        return f"Error saving documentation: {str(e)}"

@mcp.tool()
def list_code_files(directory: str, extension: str = None) -> str:
    """List code files in a directory"""
    try:
        files = []
        for root, _, filenames in os.walk(directory):
            for filename in filenames:
                if not extension or filename.endswith(extension):
                    files.append(os.path.join(root, filename))
        
        return "\n".join(files)
    except Exception as e:
        return f"Error listing files: {str(e)}"

if __name__ == "__main__":
    print("Starting Documentation Server...", file=sys.stderr)
    try:
        mcp.run()
    except Exception as e:
        print(f"Error running server: {str(e)}", file=sys.stderr)