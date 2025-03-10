from typing import Optional

class PromptGenerator:
    """Generates prompts for documentation generation."""
    
    def get_system_prompt(self, language: str, doc_format: str) -> str:
        """Get the appropriate system prompt for the language and format."""
        base_prompt = f"You are an expert technical documentation writer specializing in {language} documentation."
        
        if doc_format == "rst" or doc_format == "sphinx":
            return base_prompt + " Create detailed, well-structured reStructuredText (RST) documentation that follows Sphinx conventions."
        else:
            return base_prompt + " Create detailed, well-structured Markdown documentation."
    
    def create_prompt(self, code_snippet: str, language: str, 
                     doc_format: str, context: Optional[str] = None) -> str:
        """Create a prompt for documentation generation."""
        context_str = context or ""
        
        if language == "scala":
            template = """
            Please create comprehensive Sphinx/RST documentation for this Scala code. 
            
            {context_str}
            
            ```scala
            {code_snippet}
            ```
            
            IMPORTANT: Your response must follow these requirements:
            1. Begin with a brief note that documentation was auto-generated
            2. Include a clear class/object heading with proper RST formatting
            3. Provide a detailed, meaningful description (3-5 sentences) that explains:
               - The class's purpose and primary responsibilities
               - Its role within the system architecture
               - Key functionality it provides
               - Typical usage patterns or scenarios
            4. Document ALL constructor parameters with:
               - Type information
               - Detailed purpose description
               - Any constraints or requirements
            5. Document ALL methods with:
               - Complete method signature
               - Detailed purpose description explaining WHAT it does and WHY
               - Parameter descriptions with types and purpose
               - Return type and description
               - Examples of usage where appropriate
            6. Document ALL fields/values with types and descriptions
            7. Format code references with double backticks like ``ClassName``
            8. Use proper RST section formatting with consistent underlines
            9. ALWAYS COMPLETE ALL DESCRIPTIONS - never cut off explanations mid-sentence
            10. Do not include any debug output like "getWindowArguments", "App is installed", etc.
            
            Output only valid RST documentation.
            """
        elif language == "python":
            template = """
            Please create comprehensive Sphinx/RST documentation for this Python code.
            
            {context_str}
            
            ```python
            {code_snippet}
            ```
            
            IMPORTANT: Your response must follow these requirements:
            1. Begin with a brief note that documentation was auto-generated
            2. Include a clear module/class heading with proper RST formatting
            3. Provide a detailed, meaningful description that explains:
               - The module/class purpose and primary responsibilities
               - Its role within the system architecture
               - Key functionality it provides
            4. Document ALL parameters with types and descriptions
            5. Document ALL methods/functions with:
               - Complete signature
               - Purpose description
               - Parameter descriptions with types
               - Return type and description
            6. Document ALL attributes/fields with types and descriptions
            7. Format code references with double backticks like ``ClassName``
            8. Use proper RST section formatting with consistent underlines
            9. ALWAYS COMPLETE ALL DESCRIPTIONS - never cut off explanations mid-sentence
            10. Do not include any debug output or irrelevant text
            
            Output only valid RST documentation.
            """
        elif language == "java":
            template = """
            Please create comprehensive Sphinx/RST documentation for this Java code.
            
            {context_str}
            
            ```java
            {code_snippet}
            ```
            
            IMPORTANT: Your response must follow these requirements:
            1. Begin with a brief note that documentation was auto-generated
            2. Include a clear class/interface heading with proper RST formatting
            3. Provide a detailed, meaningful description that explains:
               - The class's purpose and primary responsibilities
               - Its role within the system architecture
               - Key functionality it provides
            4. Document ALL constructor parameters with types and descriptions
            5. Document ALL methods with:
               - Complete signature
               - Purpose description
               - Parameter descriptions with types
               - Return type and description
               - Exceptions thrown
            6. Document ALL fields with types and descriptions
            7. Format code references with double backticks like ``ClassName``
            8. Use proper RST section formatting with consistent underlines
            9. ALWAYS COMPLETE ALL DESCRIPTIONS - never cut off explanations mid-sentence
            10. Do not include any debug output or irrelevant text
            
            Output only valid RST documentation.
            """
        else:
            # Generic template for other languages
            template = """
            Please create comprehensive documentation for this {language} code.
            
            {context_str}
            
            ```{language}
            {code_snippet}
            ```
            
            IMPORTANT: Your response must follow these requirements:
            1. Begin with a brief note that documentation was auto-generated
            2. Include a clear heading with proper formatting
            3. Provide a detailed, meaningful description that explains the code's purpose
            4. Document ALL parameters/arguments with types and descriptions
            5. Document ALL functions/methods with:
               - Complete signature
               - Purpose description
               - Parameter descriptions
               - Return values
            6. Document ALL fields/variables with types and descriptions
            7. Use proper formatting for code references
            8. Use consistent section formatting
            9. ALWAYS COMPLETE ALL DESCRIPTIONS - never cut off explanations mid-sentence
            10. Do not include any debug output or irrelevant text
            
            Output only valid documentation.
            """
        
        return template.format(
            context_str=context_str,
            code_snippet=code_snippet,
            language=language,
            doc_format=doc_format
        ).strip()