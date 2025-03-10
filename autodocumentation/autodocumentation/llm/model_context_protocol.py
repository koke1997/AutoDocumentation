import json
import subprocess
import tempfile
import os
import platform
from typing import Optional, Dict, Any, List

from .base_client import BaseClaudeClient
from .prompt_generators import PromptGenerator
from .documentation_processor import DocumentationProcessor

class ModelContextProtocolClient:
    """Client for interacting with Claude using the Model Context Protocol."""
    
    def __init__(self, claude_executable_path=None):
        """
        Initialize the Claude client.
        
        Args:
            claude_executable_path: Path to the Claude Desktop App executable.
                If None, will attempt to find it automatically.
        """
        self.base_client = BaseClaudeClient(claude_executable_path)
        self.prompt_generator = PromptGenerator()
        self.doc_processor = DocumentationProcessor()
    
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
        """
        # Generate the appropriate prompt
        prompt = self.prompt_generator.create_prompt(
            code_snippet, language, doc_format, context
        )
        
        # Get the system prompt
        system_prompt = self.prompt_generator.get_system_prompt(language, doc_format)
        
        # Call Claude to generate documentation
        raw_response = self.base_client.call_claude(
            prompt, system_prompt, model, temperature, max_tokens
        )
        
        # Process the response - make sure this line is present!
        processed_response = self.doc_processor.process_documentation(
            raw_response, language, doc_format
        )
        
        return processed_response
    
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
        try:
            from autodocumentation.parsers.java_parser import JavaParser
        except ImportError:
            JavaParser = None
        
        from autodocumentation.generators.sphinx_generator import SphinxGenerator
        from autodocumentation.generators.scala_sphinx_generator import ScalaSphinxGenerator
        from autodocumentation.generators.markdown_generator import MarkdownGenerator
        
        parsers = {
            "python": PythonParser(),
            "scala": ScalaParser(),
            "java": JavaParser() if 'JavaParser' in locals() else None
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
                    context=f"This file is part of the project at {os.path.dirname(file_path)}",
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