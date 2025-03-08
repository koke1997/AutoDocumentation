# autodocumentation/parsers/scala_parser.py
import os
import re
from typing import Dict, List, Any, Optional

class ScalaParser:
    """Parser for Scala source code."""
    
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a Scala file and extract documentation-relevant information.
        
        Args:
            file_path: Path to the Scala file to parse
            
        Returns:
            Dictionary containing the structure and details of the code
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            # Extract basic file information
            module_info = {
                'file_path': file_path,
                'module_name': os.path.basename(file_path).replace('.scala', ''),
                'package': self._extract_package(source),
                'imports': self._extract_imports(source),
                'classes': self._extract_classes(source),
                'objects': self._extract_objects(source),
                'traits': self._extract_traits(source),
                'source': source
            }
            
            return module_info
            
        except Exception as e:
            return {
                'file_path': file_path,
                'error': str(e),
                'source': open(file_path, 'r', encoding='utf-8').read() if os.path.exists(file_path) else None
            }
    
    def _extract_package(self, source: str) -> Optional[str]:
        """Extract package name from Scala source code."""
        package_match = re.search(r'package\s+([a-zA-Z0-9\.]+)', source)
        return package_match.group(1) if package_match else None
    
    def _extract_imports(self, source: str) -> List[Dict[str, Any]]:
        """Extract import statements from Scala source code."""
        import_matches = re.findall(r'import\s+([a-zA-Z0-9\.\{\}\s,_]+)', source)
        imports = []
        
        for match in import_matches:
            imports.append({
                'statement': match.strip()
            })
        
        return imports
    
    def _extract_classes(self, source: str) -> List[Dict[str, Any]]:
        """Extract class definitions from Scala source code."""
        # This regex will match class definitions - this is a simplification
        class_matches = re.finditer(
            r'(\/\*\*(?:(?!\*\/).)*\*\/\s*)?(class)\s+([a-zA-Z0-9_]+)(?:\[([^\]]*)\])?(?:\((.*?)\))?(?:\s+extends\s+([a-zA-Z0-9, \[\]\.]+))?(?:\s+with\s+([a-zA-Z0-9, \[\]\.]+))?\s*\{((?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*)\}', 
            source, 
            re.DOTALL
        )
        
        classes = []
        for match in class_matches:
            javadoc = match.group(1)
            class_name = match.group(3)
            type_params = match.group(4)
            constructor_params = match.group(5)
            extends_clause = match.group(6)
            with_clause = match.group(7)
            body = match.group(8)
            
            classes.append({
                'name': class_name,
                'type_parameters': type_params.strip() if type_params else None,
                'constructor_parameters': self._parse_constructor_params(constructor_params) if constructor_params else [],
                'extends': extends_clause.strip() if extends_clause else None,
                'with': with_clause.strip() if with_clause else None,
                'javadoc': self._clean_javadoc(javadoc) if javadoc else None,
                'methods': self._extract_methods(body),
                'fields': self._extract_fields(body)
            })
        
        return classes
    
    def _extract_objects(self, source: str) -> List[Dict[str, Any]]:
        """Extract object definitions from Scala source code."""
        # Similar regex pattern as classes, but for objects
        object_matches = re.finditer(
            r'(\/\*\*(?:(?!\*\/).)*\*\/\s*)?(object)\s+([a-zA-Z0-9_]+)(?:\s+extends\s+([a-zA-Z0-9, \[\]\.]+))?(?:\s+with\s+([a-zA-Z0-9, \[\]\.]+))?\s*\{((?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*)\}', 
            source, 
            re.DOTALL
        )
        
        objects = []
        for match in object_matches:
            javadoc = match.group(1)
            object_name = match.group(3)
            extends_clause = match.group(4)
            with_clause = match.group(5)
            body = match.group(6)
            
            objects.append({
                'name': object_name,
                'extends': extends_clause.strip() if extends_clause else None,
                'with': with_clause.strip() if with_clause else None,
                'javadoc': self._clean_javadoc(javadoc) if javadoc else None,
                'methods': self._extract_methods(body),
                'fields': self._extract_fields(body)
            })
        
        return objects
    
    def _extract_traits(self, source: str) -> List[Dict[str, Any]]:
        """Extract trait definitions from Scala source code."""
        # Similar regex pattern as classes, but for traits
        trait_matches = re.finditer(
            r'(\/\*\*(?:(?!\*\/).)*\*\/\s*)?(trait)\s+([a-zA-Z0-9_]+)(?:\[([^\]]*)\])?(?:\s+extends\s+([a-zA-Z0-9, \[\]\.]+))?(?:\s+with\s+([a-zA-Z0-9, \[\]\.]+))?\s*\{((?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*)\}', 
            source, 
            re.DOTALL
        )
        
        traits = []
        for match in trait_matches:
            javadoc = match.group(1)
            trait_name = match.group(3)
            type_params = match.group(4)
            extends_clause = match.group(5)
            with_clause = match.group(6)
            body = match.group(7)
            
            traits.append({
                'name': trait_name,
                'type_parameters': type_params.strip() if type_params else None,
                'extends': extends_clause.strip() if extends_clause else None,
                'with': with_clause.strip() if with_clause else None,
                'javadoc': self._clean_javadoc(javadoc) if javadoc else None,
                'methods': self._extract_methods(body),
                'fields': self._extract_fields(body)
            })
        
        return traits
    
    def _extract_methods(self, body: str) -> List[Dict[str, Any]]:
        """Extract method definitions from a class/object/trait body."""
        # This regex matches method definitions
        method_matches = re.finditer(
            r'(\/\*\*(?:(?!\*\/).)*\*\/\s*)?(?:override\s+)?(?:def)\s+([a-zA-Z0-9_]+)(?:\[([^\]]*)\])?(?:\((.*?)\))(?:\s*:\s*([a-zA-Z0-9\[\]\._]+))?(?:\s*=\s*(.+?))?', 
            body
        )
        
        methods = []
        for match in method_matches:
            javadoc = match.group(1)
            method_name = match.group(2)
            type_params = match.group(3)
            parameters = match.group(4)
            return_type = match.group(5)
            
            methods.append({
                'name': method_name,
                'type_parameters': type_params.strip() if type_params else None,
                'parameters': self._parse_parameters(parameters) if parameters else [],
                'return_type': return_type.strip() if return_type else None,
                'javadoc': self._clean_javadoc(javadoc) if javadoc else None
            })
        
        return methods
    
    def _extract_fields(self, body: str) -> List[Dict[str, Any]]:
        """Extract field definitions from a class/object/trait body."""
        # This regex matches val/var field definitions
        field_matches = re.finditer(
            r'(\/\*\*(?:(?!\*\/).)*\*\/\s*)?(?:private|protected)?\s*(val|var)\s+([a-zA-Z0-9_]+)(?:\s*:\s*([a-zA-Z0-9\[\]\._]+))?(?:\s*=\s*(.+?))?', 
            body
        )
        
        fields = []
        for match in field_matches:
            javadoc = match.group(1)
            field_type = match.group(2)  # val or var
            field_name = match.group(3)
            data_type = match.group(4)
            
            fields.append({
                'name': field_name,
                'field_type': field_type,
                'data_type': data_type.strip() if data_type else None,
                'javadoc': self._clean_javadoc(javadoc) if javadoc else None
            })
        
        return fields
    
    def _parse_constructor_params(self, params_str: str) -> List[Dict[str, str]]:
        """Parse constructor parameters string into a structured format."""
        if not params_str:
            return []
        
        # Split by commas, but respect parentheses and brackets for complex types
        params = []
        current_param = ""
        paren_depth = 0
        bracket_depth = 0
        
        for char in params_str + ',':  # Add comma at the end for easy processing
            if char == ',' and paren_depth == 0 and bracket_depth == 0:
                # End of parameter
                if current_param.strip():
                    parts = current_param.split(':', 1)
                    param_name = parts[0].strip()
                    param_type = parts[1].strip() if len(parts) > 1 else None
                    
                    params.append({
                        'name': param_name,
                        'type': param_type
                    })
                current_param = ""
            else:
                current_param += char
                if char == '(':
                    paren_depth += 1
                elif char == ')':
                    paren_depth -= 1
                elif char == '[':
                    bracket_depth += 1
                elif char == ']':
                    bracket_depth -= 1
        
        return params
    
    def _parse_parameters(self, params_str: str) -> List[Dict[str, str]]:
        """Parse method parameters string into a structured format."""
        # We can reuse the constructor params parsing
        return self._parse_constructor_params(params_str)
    
    def _clean_javadoc(self, javadoc: str) -> str:
        """Clean Javadoc comments from formatting."""
        if not javadoc:
            return None
        
        # Remove leading /** and trailing */
        javadoc = re.sub(r'^\s*\/\*\*', '', javadoc)
        javadoc = re.sub(r'\*\/\s*$', '', javadoc)
        
        # Remove leading * from each line
        lines = javadoc.split('\n')
        cleaned_lines = []
        for line in lines:
            line = re.sub(r'^\s*\*\s?', '', line)
            if line.strip():
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip()