# autodocumentation/parsers/scala_parser.py
import re
import os
from typing import Dict, Any

class ScalaParser:
    """Parser for Scala code."""
    
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a Scala file to extract class structure.
        
        Args:
            file_path: Path to the Scala file
            
        Returns:
            Dictionary containing parsed code information
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Get filename without extension
            file_name = os.path.basename(file_path)
            base_name = os.path.splitext(file_name)[0]
            
            # Extract package name
            package_match = re.search(r'package\s+([^\s{;]+)', content)
            package = package_match.group(1) if package_match else "unknown"
            
            # Extract class/object/trait name
            class_match = re.search(r'(class|object|trait)\s+([^\s({]+)', content)
            class_name = class_match.group(2) if class_match else base_name
            
            # If class name still doesn't match file name, use the file name instead
            if class_name != base_name and not class_name in base_name and not base_name in class_name:
                class_name = base_name
                
            return {
                "name": class_name,
                "package": package,
                "file_path": file_path,
                "content": content
            }
        except Exception as e:
            return {"error": str(e)}