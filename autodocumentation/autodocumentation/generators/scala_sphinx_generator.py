# autodocumentation/generators/scala_sphinx_generator.py
import os
import re
from pathlib import Path
from typing import Dict, Any

class ScalaSphinxGenerator:
    """Generator for Sphinx documentation of Scala code."""
    
    def __init__(self, output_dir):
        """Initialize with output directory."""
        self.output_dir = output_dir
        self.api_dir = os.path.join(output_dir, "api", "scala")
        os.makedirs(self.api_dir, exist_ok=True)
    
    def generate_from_parsed_code(self, parsed_code: Dict[str, Any], documentation: str) -> str:
        """Generate documentation from parsed code and LLM-generated text."""
        # Extract class name 
        class_name = parsed_code.get("name", "")
        file_path = parsed_code.get("file_path", "")
        
        if not class_name:
            # Try to extract from file path
            if file_path:
                class_name = Path(file_path).stem
            else:
                # Try to extract from documentation
                class_match = re.search(r'([A-Z][A-Za-z0-9_]+)\n={3,}', documentation)
                class_name = class_match.group(1) if class_match else "Unknown"
        
        # Clean the documentation
        documentation = self._clean_documentation(documentation)
        
        # Generate class diagram if possible
        if file_path:
            try:
                from autodocumentation.autodocumentation.analyzers.simple_diagram import generate_class_diagram
                
                # Use parent directory as source dir (e.g., app/controllers -> app)
                source_dir = str(Path(file_path).parent.parent)
                
                diagram_file = generate_class_diagram(
                    class_name, 
                    source_dir, 
                    self.api_dir
                )
                
                if diagram_file:
                    diagram_section = f"""
Class Relationships
------------------

The following diagram shows the relationships between ``{class_name}`` and other classes:

.. image:: {diagram_file}
   :alt: {class_name} class relationships
   :align: center

"""
                    # Insert diagram before API Reference if it exists
                    if "API Reference" in documentation:
                        parts = documentation.split("API Reference", 1)
                        documentation = parts[0] + diagram_section + "API Reference" + parts[1]
                    else:
                        # Otherwise add it to the end
                        documentation += "\n\n" + diagram_section
            except Exception as e:
                print(f"Warning: Could not generate diagram for {class_name}: {e}")
        
        # Write to file
        output_file = os.path.join(self.api_dir, f"{class_name}.rst")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(documentation)
        
        return output_file
    
    def _clean_documentation(self, documentation: str) -> str:
        """Clean the documentation text."""
        # Remove filepath comment
        if documentation.startswith("// filepath:"):
            documentation = "\n".join(documentation.split("\n")[1:])
        
        # Remove debug output patterns
        patterns = [
            r"getWindowArguments \[\].*?(?=\n\n|\Z)",
            r"App is installed.*?(?=\n\n|\Z)",
            r"Checking for updates.*?(?=\n\n|\Z)"
        ]
        
        for pattern in patterns:
            documentation = re.sub(pattern, "", documentation, flags=re.IGNORECASE | re.DOTALL)
        
        # Clean up multiple newlines
        documentation = re.sub(r'\n{3,}', '\n\n', documentation)
        
        return documentation