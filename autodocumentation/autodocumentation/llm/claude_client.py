# autodocumentation/llm/model_context_protocol.py (updated)
import json
import subprocess
import tempfile
import os
import platform
from typing import Optional, Dict, Any

class ModelContextProtocolClient:
    """Client for interacting with Claude using the Model Context Protocol."""
    
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
                os.path.join(os.environ.get("PROGRAMFILES", "C:\\Program Files"), "Claude", "Claude.exe"),
                os.path.join(os.environ.get("LOCALAPPDATA", ""), "Claude", "Claude.exe")
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
    
    def generate_documentation(self, code_snippet: str, language: str, 
                              doc_format: str = "markdown", context: str = None,
                              model: str = "claude-3-opus-20240229", 
                              temperature: float = 0.2,
                              max_tokens: int = 4000) -> str:
        """
        Generate documentation for the given code snippet using Claude.
        
        Args:
            code_snippet: The source code to document
            language: Programming language of the code (python, java, scala, etc.)
            doc_format: Format for the documentation (markdown, rst, etc.)
            context: Additional context to help Claude understand the code
            model: Claude model to use
            temperature: Temperature for generation (0.0 to 1.0)
            max_tokens: Maximum tokens for generation
            
        Returns:
            The generated documentation as a string
        """
        prompt = self._create_prompt(
            code_snippet, language, doc_format, context
        )
        
        # Create the request object
        request = {
            "prompt": prompt,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # Write request to a temporary file
        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f:
            json.dump(request, f)
            prompt_file = f.name
        
        try:
            # Call Claude Desktop App with the Model Context Protocol
            # Ensure Claude is installed and running
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
                return response.get("content", "")
            except json.JSONDecodeError:
                # If we can't parse JSON, return the raw output
                return result.stdout
            
        finally:
            # Clean up the temporary file
            if os.path.exists(prompt_file):
                os.unlink(prompt_file)
    
    def _create_prompt(self, code_snippet: str, language: str, 
                      doc_format: str, context: Optional[str] = None) -> str:
        """Create a prompt for documentation generation."""
        context_str = context or ""
        
        # Different prompt templates for different languages
        if language == "python":
            template = """
            You are an expert Python documentation writer following PEP 257 docstring conventions. Generate comprehensive documentation for the following Python code.
            
            {context_str}
            
            Here is the code to document:
            
            ```python
            {code_snippet}
            ```
            
            Generate detailed documentation in {doc_format} format that includes:
            1. Module-level overview explaining the purpose of the code
            2. For each class:
               - Class description
               - Constructor parameters with type information
               - Methods with parameters, return types, and explanations
               - Attributes with types and descriptions
            3. For each function:
               - Purpose description
               - Parameters with types
               - Return values with types
               - Exceptions raised
            4. Usage examples showing common ways to use the code
            
            Focus on clarity, accuracy, and completeness.
            """
        elif language == "scala":
            template = """
            You are an expert Scala documentation writer following Scaladoc conventions. Generate comprehensive documentation for the following Scala code.
            
            {context_str}
            
            Here is the code to document:
            
            ```scala
            {code_snippet}
            ```
            
            Generate detailed documentation in {doc_format} format that includes:
            1. Package-level overview explaining the purpose of the code
            2. For each class/object/trait:
               - Description of its purpose and role
               - Constructor parameters with type information
               - Methods with parameters, return types, and explanations
               - Fields/values with types and descriptions
            3. For each method:
               - Purpose description
               - Parameters with types
               - Return values with types
               - Exceptions thrown
            4. Usage examples showing common ways to use the code
            
            Focus on functional programming concepts, immutability, and type safety where relevant.
            """
        else:
            # Generic template for other languages
            template = """
            You are an expert technical documentation writer. Generate comprehensive documentation for the following {language} code.
            
            {context_str}
            
            Here is the code to document:
            
            ```{language}
            {code_snippet}
            ```
            
            Generate detailed documentation in {doc_format} format that includes:
            1. A high-level overview of what the code does
            2. Detailed descriptions of functions/classes/methods
            3. Parameter descriptions with types
            4. Return value descriptions with types
            5. Usage examples
            6. Any important notes or warnings
            
            Focus on clarity and completeness.
            """
        
        # Format the template
        return template.format(
            context_str=context_str,
            code_snippet=code_snippet,
            language=language,
            doc_format=doc_format
        ).strip()