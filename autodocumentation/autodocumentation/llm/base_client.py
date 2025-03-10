import json
import subprocess
import tempfile
import os
import platform
from typing import Optional, Dict, Any

class BaseClaudeClient:
    """Base client for interacting with Claude Desktop App."""
    
    def __init__(self, claude_executable_path=None):
        """
        Initialize the Claude client.
        
        Args:
            claude_executable_path: Path to the Claude Desktop App executable.
                If None, will attempt to find it automatically.
        """
        self.claude_executable_path = claude_executable_path or self._find_claude_executable()
        if not self.claude_executable_path:
            raise ValueError(
                "Could not find Claude Desktop App executable. "
                "Please specify the path using --claude-executable or set it in the configuration."
            )
    
    def _find_claude_executable(self) -> Optional[str]:
        """Attempt to locate the Claude Desktop App executable based on OS."""
        system = platform.system()
        
        if system == "Darwin":  # macOS
            possible_paths = [
                "/Applications/Claude.app/Contents/MacOS/Claude",
                os.path.expanduser("~/Applications/Claude.app/Contents/MacOS/Claude")
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    return path
                    
        elif system == "Windows":
            possible_paths = [
                os.path.join(os.environ.get("PROGRAMFILES", "C:\\Program Files"), "Anthropic", "Claude", "Claude.exe"),
                os.path.join(os.environ.get("LOCALAPPDATA", ""), "Anthropic", "Claude", "Claude.exe"),
                os.path.join(os.environ.get("LOCALAPPDATA", ""), "AnthropicClaude", "Claude.exe"),
                os.path.join(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)"), "Anthropic", "Claude", "Claude.exe"),
                # Add common installation locations
                "C:\\Program Files\\Anthropic\\Claude\\Claude.exe",
                "C:\\Program Files (x86)\\Anthropic\\Claude\\Claude.exe"
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    return path
                    
        elif system == "Linux":
            # Look for Claude in common locations
            possible_paths = [
                "/usr/bin/claude",
                "/usr/local/bin/claude",
                os.path.expanduser("~/.local/bin/claude")
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    return path
        
        return None
    
    def call_claude(self, 
                   prompt: str, 
                   system_prompt: str,
                   model: str = "claude-3-opus-20240229", 
                   temperature: float = 0.2,
                   max_tokens: int = 4000) -> str:
        """
        Call Claude Desktop App with the Model Context Protocol.
        
        Args:
            prompt: The prompt to send to Claude
            system_prompt: The system prompt to use
            model: Claude model to use
            temperature: Temperature for generation
            max_tokens: Maximum tokens for generation
            
        Returns:
            The generated text as a string
        """
        # Create the MCP request object
        request = {
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "system": system_prompt
        }
        
        # Write request to a temporary file
        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f:
            json.dump(request, f)
            prompt_file = f.name
        
        try:
            # Call Claude Desktop App with the Model Context Protocol
            cmd = [self.claude_executable_path, "--model-context-protocol", prompt_file]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False  # Don't raise exception on non-zero return code
            )
            
            # Check for errors
            if result.returncode != 0:
                error_msg = result.stderr.strip() or f"Claude returned error code: {result.returncode}"
                raise Exception(f"Claude error: {error_msg}")
            
            # Parse the response
            try:
                response = json.loads(result.stdout)
                if "error" in response:
                    raise Exception(f"Claude API error: {response['error']}")
                
                # Extract content from the response
                if "messages" in response and len(response["messages"]) > 0:
                    return response["messages"][0]["content"]
                elif "content" in response:
                    return response["content"]
                else:
                    return "No content found in response"
                
            except json.JSONDecodeError:
                # If we can't parse JSON, return the raw output
                return result.stdout
            
        finally:
            # Clean up the temporary file
            if os.path.exists(prompt_file):
                os.unlink(prompt_file)