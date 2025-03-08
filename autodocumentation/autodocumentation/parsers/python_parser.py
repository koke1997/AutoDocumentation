# autodocumentation/parsers/python_parser.py
import ast
import inspect
import importlib.util
from typing import Dict, List, Any

class PythonParser:
    """Parser for Python source code."""
    
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a Python file and extract documentation-relevant information.
        
        Args:
            file_path: Path to the Python file to parse
            
        Returns:
            Dictionary containing the structure and details of the code
        """
        try:
            # Load the module
            spec = importlib.util.spec_from_file_location("module.name", file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Parse the file with AST
            with open(file_path, 'r') as f:
                source = f.read()
            
            tree = ast.parse(source)
            module_info = {
                'file_path': file_path,
                'module_name': spec.name,
                'classes': [],
                'functions': [],
                'imports': [],
                'constants': [],
                'source': source
            }
            
            # Extract classes and functions
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_info = self._extract_class_info(node, module)
                    module_info['classes'].append(class_info)
                elif isinstance(node, ast.FunctionDef) and node.parent_field == tree:
                    # Only get top-level functions
                    func_info = self._extract_function_info(node, module)
                    module_info['functions'].append(func_info)
                elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    import_info = self._extract_import_info(node)
                    module_info['imports'].append(import_info)
                elif isinstance(node, ast.Assign):
                    # Look for module-level constants
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id.isupper():
                            module_info['constants'].append({
                                'name': target.id,
                                'value': ast.unparse(node.value)
                            })
            
            return module_info
            
        except Exception as e:
            return {
                'file_path': file_path,
                'error': str(e),
                'source': open(file_path, 'r').read() if os.path.exists(file_path) else None
            }
    
    def _extract_class_info(self, node: ast.ClassDef, module) -> Dict[str, Any]:
        """Extract information about a class."""
        class_info = {
            'name': node.name,
            'docstring': ast.get_docstring(node),
            'methods': [],
            'attributes': [],
            'bases': [base.id if isinstance(base, ast.Name) else ast.unparse(base) for base in node.bases]
        }
        
        # Get methods and attributes
        for child in node.body:
            if isinstance(child, ast.FunctionDef):
                method_info = self._extract_function_info(child, module, is_method=True)
                class_info['methods'].append(method_info)
            elif isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        class_info['attributes'].append({
                            'name': target.id,
                            'value': ast.unparse(child.value)
                        })
        
        return class_info
    
    def _extract_function_info(self, node: ast.FunctionDef, module, is_method=False) -> Dict[str, Any]:
        """Extract information about a function or method."""
        function_info = {
            'name': node.name,
            'docstring': ast.get_docstring(node),
            'parameters': [],
            'return_annotation': ast.unparse(node.returns) if node.returns else None,
            'is_method': is_method
        }
        
        # Extract parameters
        args = node.args
        defaults = len(args.defaults)
        params = []
        
        # Handle normal args
        for i, arg in enumerate(args.args):
            has_default = i >= len(args.args) - defaults
            default_value = ast.unparse(args.defaults[i - (len(args.args) - defaults)]) if has_default else None
            
            params.append({
                'name': arg.arg,
                'annotation': ast.unparse(arg.annotation) if arg.annotation else None,
                'default': default_value,
                'kind': 'POSITIONAL_OR_KEYWORD'
            })
        
        # Handle *args
        if args.vararg:
            params.append({
                'name': args.vararg.arg,
                'annotation': ast.unparse(args.vararg.annotation) if args.vararg.annotation else None,
                'kind': 'VAR_POSITIONAL'
            })
        
        # Handle keyword-only args
        for i, arg in enumerate(args.kwonlyargs):
            default_value = ast.unparse(args.kw_defaults[i]) if args.kw_defaults[i] else None
            params.append({
                'name': arg.arg,
                'annotation': ast.unparse(arg.annotation) if arg.annotation else None,
                'default': default_value,
                'kind': 'KEYWORD_ONLY'
            })
        
        # Handle **kwargs
        if args.kwarg:
            params.append({
                'name': args.kwarg.arg,
                'annotation': ast.unparse(args.kwarg.annotation) if args.kwarg.annotation else None,
                'kind': 'VAR_KEYWORD'
            })
        
        function_info['parameters'] = params
        return function_info
    
    def _extract_import_info(self, node) -> Dict[str, Any]:
        """Extract information about imports."""
        if isinstance(node, ast.Import):
            return {
                'type': 'import',
                'names': [alias.name for alias in node.names],
                'aliases': {alias.name: alias.asname for alias in node.names if alias.asname}
            }
        elif isinstance(node, ast.ImportFrom):
            return {
                'type': 'import_from',
                'module': node.module,
                'names': [alias.name for alias in node.names],
                'aliases': {alias.name: alias.asname for alias in node.names if alias.asname}
            }