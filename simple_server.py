#!/usr/bin/env python3
from mcp.server.fastmcp import FastMCP
import sys
import os
import traceback

# Create an MCP server
mcp = FastMCP("Simple File Reader")

@mcp.resource("file://{path}")
def read_file(path: str) -> str:
    """Read file contents for Claude to use as context"""
    try:
        print(f"Attempting to read file: {path}", file=sys.stderr)
        
        # Normalize path (handles both forward and backslashes)
        normalized_path = os.path.normpath(path)
        
        # Validate the path
        if not os.path.exists(normalized_path):
            error_msg = f"File not found: {normalized_path}"
            print(error_msg, file=sys.stderr)
            return error_msg
            
        if not os.path.isfile(normalized_path):
            error_msg = f"Not a file: {normalized_path}"
            print(error_msg, file=sys.stderr)
            return error_msg
        
        # Read and return the file content
        with open(normalized_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"Successfully read file: {normalized_path} ({len(content)} bytes)", file=sys.stderr)
            return content
            
    except UnicodeDecodeError:
        # Try binary read for non-text files
        try:
            with open(normalized_path, 'rb') as f:
                binary_content = f.read()
            error_msg = f"File appears to be binary (not text): {normalized_path}"
            print(error_msg, file=sys.stderr)
            return error_msg
        except Exception as bin_err:
            error_msg = f"Error reading binary file {normalized_path}: {str(bin_err)}"
            print(error_msg, file=sys.stderr)
            return error_msg
            
    except Exception as e:
        error_msg = f"Error reading file {path}: {str(e)}"
        print(error_msg, file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        return error_msg

@mcp.resource("directory://{path}")
def list_directory(path: str) -> str:
    """List contents of a directory for Claude to browse"""
    try:
        print(f"Attempting to list directory: {path}", file=sys.stderr)
        
        # Normalize path
        normalized_path = os.path.normpath(path)
        
        # Validate path
        if not os.path.exists(normalized_path):
            error_msg = f"Directory not found: {normalized_path}"
            print(error_msg, file=sys.stderr)
            return error_msg
            
        if not os.path.isdir(normalized_path):
            error_msg = f"Not a directory: {normalized_path}"
            print(error_msg, file=sys.stderr)
            return error_msg
        
        # List directory contents
        items = os.listdir(normalized_path)
        
        # Create formatted output
        result = f"Directory contents of {normalized_path}:\n\n"
        
        # Separate files and directories
        directories = []
        files = []
        
        for item in items:
            full_path = os.path.join(normalized_path, item)
            if os.path.isdir(full_path):
                directories.append(item + "/")
            else:
                files.append(item)
        
        # Sort both lists
        directories.sort()
        files.sort()
        
        # Add directories to result
        if directories:
            result += "Directories:\n"
            for directory in directories:
                result += f"- {directory}\n"
            result += "\n"
        
        # Add files to result
        if files:
            result += "Files:\n"
            for file in files:
                result += f"- {file}\n"
        
        print(f"Successfully listed directory: {normalized_path} ({len(items)} items)", file=sys.stderr)
        return result
        
    except Exception as e:
        error_msg = f"Error listing directory {path}: {str(e)}"
        print(error_msg, file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        return error_msg

if __name__ == "__main__":
    print("Starting Simple File Reader MCP server...", file=sys.stderr)
    try:
        mcp.run()
    except Exception as e:
        print(f"Error starting server: {str(e)}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)