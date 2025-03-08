import json
import subprocess
import tempfile
import os
import platform
from typing import Optional, Dict, Any, List

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
                os.path.join(os.environ.get("PROGRAMFILES", "C:\\Program Files"), "Anthropic", "Claude", "Claude.exe"),
                os.path.join(os.environ.get("LOCALAPPDATA", ""), "Anthropic", "Claude", "Claude.exe"),
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
    
    def generate_documentation(self, 
                              code_snippet: str, 
                              language: str, 
                              doc_format: str = "markdown", 
                              context: str = None,
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
        
        # Create the MCP request object
        request = {
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "system": self._get_system_prompt(language, doc_format)
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
    
    def _get_system_prompt(self, language: str, doc_format: str) -> str:
        """Get the appropriate system prompt for the language and format."""
        base_prompt = f"You are an expert technical documentation writer specializing in {language} documentation."
        
        if doc_format == "rst" or doc_format == "sphinx":
            return base_prompt + " Create detailed, well-structured reStructuredText (RST) documentation that follows Sphinx conventions."
        else:
            return base_prompt + " Create detailed, well-structured Markdown documentation."
    
    def _create_prompt(self, code_snippet: str, language: str, 
                      doc_format: str, context: Optional[str] = None) -> str:
        """Create a prompt for documentation generation."""
        context_str = context or ""
        
        # Different prompt templates for different languages
        if language == "python":
            template = """
            I need comprehensive documentation for the following Python code.
            
            {context_str}
            
            Please document this code following PEP 257 conventions:
            
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
            
            Please format the documentation in clean {doc_format} with proper syntax highlighting.
            """
        elif language == "scala":
            template = """
            I need comprehensive documentation for the following Scala code.
            
            {context_str}
            
            Please document this code following Scaladoc conventions:
            
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
            
            Please format the documentation in clean {doc_format} with proper syntax highlighting.
            Focus on functional programming concepts, immutability, and type safety where relevant.
            """
        elif language == "java":
            template = """
            I need comprehensive documentation for the following Java code.
            
            {context_str}
            
            Please document this code following Javadoc conventions:
            
            ```java
            {code_snippet}
            ```
            
            Generate detailed documentation in {doc_format} format that includes:
            1. Package-level overview explaining the purpose of the code
            2. For each class/interface:
               - Class description
               - Constructor parameters with type information
               - Methods with parameters, return types, and explanations
               - Fields with types and descriptions
            3. For each method:
               - Purpose description
               - Parameters with types
               - Return values with types
               - Exceptions thrown
            4. Usage examples showing common ways to use the code
            
            Please format the documentation in clean {doc_format} with proper syntax highlighting.
            """
        else:
            # Generic template for other languages
            template = """
            I need comprehensive documentation for the following {language} code.
            
            {context_str}
            
            Please document this code:
            
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
            
            Please format the documentation in clean {doc_format} with proper syntax highlighting.
            """
        
        # Format the template
        return template.format(
            context_str=context_str,
            code_snippet=code_snippet,
            language=language,
            doc_format=doc_format
        ).strip()

    def run_batch_documentation(self, 
                               files_with_languages: List[tuple], 
                               output_dir: str,
                               doc_format: str = "sphinx",
                               model: str = "claude-3-opus-20240229",
                               temperature: float = 0.2,
                               max_tokens: int = 4000) -> Dict[str, Any]:
        """
        Run batch documentation generation for multiple files.
        
        Args:
            files_with_languages: List of (file_path, language) tuples
            output_dir: Directory to output documentation
            doc_format: Format for the documentation
            model: Claude model to use
            temperature: Temperature for generation
            max_tokens: Maximum tokens for generation
            
        Returns:
            Dictionary with results statistics
        """
        results = {
            "success": [],
            "failure": [],
            "total": len(files_with_languages)
        }
        
        from autodocumentation.parsers.python_parser import PythonParser
        from autodocumentation.parsers.scala_parser import ScalaParser
        from autodocumentation.parsers.java_parser import JavaParser
        from autodocumentation.generators.sphinx_generator import SphinxGenerator
        from autodocumentation.generators.scala_sphinx_generator import ScalaSphinxGenerator
        from autodocumentation.generators.markdown_generator import MarkdownGenerator
        
        parsers = {
            "python": PythonParser(),
            "scala": ScalaParser(),
            "java": JavaParser() if "JavaParser" in locals() else None
        }
        
        generators = {
            "sphinx": {
                "python": SphinxGenerator(output_dir),
                "scala": ScalaSphinxGenerator(output_dir),
                "java": SphinxGenerator(output_dir)
            },
            "markdown": {
                "python": MarkdownGenerator(output_dir),
                "scala": MarkdownGenerator(output_dir),
                "java": MarkdownGenerator(output_dir)
            }
        }
        
        for file_path, language in files_with_languages:
            try:
                # Check if we have a parser for this language
                if language not in parsers or parsers[language] is None:
                    results["failure"].append((file_path, f"No parser available for {language}"))
                    continue
                
                # Parse the code
                parsed_code = parsers[language].parse_file(file_path)
                
                # Check for parse errors
                if 'error' in parsed_code:
                    results["failure"].append((file_path, f"Parse error: {parsed_code['error']}"))
                    continue
                
                # Read the source code
                with open(file_path, 'r', encoding='utf-8') as f:
                    source_code = f.read()
                
                # Generate documentation
                documentation = self.generate_documentation(
                    code_snippet=source_code,
                    language=language,
                    doc_format="rst" if doc_format == "sphinx" else "markdown",
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                # Get the appropriate generator
                generator = generators[doc_format][language]
                
                # Generate the output
                output_file = generator.generate_from_parsed_code(parsed_code, documentation)
                
                results["success"].append((file_path, output_file))
                
            except Exception as e:
                results["failure"].append((file_path, str(e)))
        
        return results