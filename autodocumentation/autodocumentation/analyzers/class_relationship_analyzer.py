import re
import os
from typing import Dict, List, Set, Tuple, Optional

class ClassRelationshipAnalyzer:
    """Analyzes relationships between classes in a codebase."""
    
    def __init__(self, directory: str):
        """
        Initialize the analyzer.
        
        Args:
            directory: Root directory of the codebase
        """
        self.directory = directory
        self.classes: Dict[str, Dict] = {}
        self.relationships: Dict[str, Dict[str, List[str]]] = {}
    
    def analyze_scala_codebase(self) -> Dict:
        """
        Analyze a Scala codebase to extract class relationships.
        
        Returns:
            Dictionary containing class relationships
        """
        # Find all Scala files
        scala_files = []
        for root, _, files in os.walk(self.directory):
            for file in files:
                if file.endswith(".scala"):
                    scala_files.append(os.path.join(root, file))
        
        # First pass: identify all classes and their packages
        for file_path in scala_files:
            self._extract_classes_from_file(file_path)
        
        # Second pass: analyze relationships between classes
        for file_path in scala_files:
            self._analyze_relationships_from_file(file_path)
        
        return {
            "classes": self.classes,
            "relationships": self.relationships
        }
    
    def _extract_classes_from_file(self, file_path: str):
        """Extract all class definitions from a Scala file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract package name
            package_match = re.search(r'package\s+([^\s{;]+)', content)
            package = package_match.group(1) if package_match else "default"
            
            # Extract class names
            class_matches = re.finditer(r'(class|object|trait)\s+([^\s({]+)', content)
            
            for match in class_matches:
                class_type = match.group(1)  # class, object, trait
                class_name = match.group(2)
                
                self.classes[class_name] = {
                    "type": class_type,
                    "package": package,
                    "file_path": file_path,
                }
                self.relationships[class_name] = {
                    "imports": [],
                    "extends": [],
                    "uses": []
                }
        except Exception as e:
            print(f"Error processing file {file_path}: {str(e)}")
    
    def _analyze_relationships_from_file(self, file_path: str):
        """Analyze relationships between classes in a Scala file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Get classes defined in this file
            file_classes = [name for name, info in self.classes.items() if info["file_path"] == file_path]
            
            if not file_classes:
                return
            
            # Extract imports
            import_matches = re.finditer(r'import\s+([^\s;]+)', content)
            imports = [match.group(1) for match in import_matches]
            
            # Extract extends relationships
            for class_name in file_classes:
                # Find class definition
                class_def_pattern = r'(class|object|trait)\s+' + re.escape(class_name) + r'[^\{]*'
                class_def_match = re.search(class_def_pattern, content)
                
                if not class_def_match:
                    continue
                
                class_def = class_def_match.group(0)
                
                # Find extends relationships
                extends_match = re.search(r'extends\s+([^\s{(]+)', class_def)
                if extends_match:
                    parent_class = extends_match.group(1)
                    self.relationships[class_name]["extends"].append(parent_class)
                
                # Find uses relationships - check which other classes are used
                for other_class in self.classes:
                    if other_class == class_name:
                        continue
                    
                    # Simple check: does the class name appear in the file content
                    pattern = r'\b' + re.escape(other_class) + r'\b'
                    if re.search(pattern, content):
                        self.relationships[class_name]["uses"].append(other_class)
                
                # Add imports
                for imp in imports:
                    for other_class in self.classes:
                        if other_class in imp:
                            self.relationships[class_name]["imports"].append(other_class)
        
        except Exception as e:
            print(f"Error analyzing relationships in {file_path}: {str(e)}")
    
    def generate_graphviz(self, class_name: Optional[str] = None) -> str:
        """
        Generate Graphviz DOT language diagram of class relationships.
        
        Args:
            class_name: Optional class name to focus on
            
        Returns:
            String containing the DOT diagram code
        """
        if class_name:
            return self.generate_class_diagram_for(class_name)
        
        dot = [
            'digraph "Class Relationships" {',
            '  rankdir=LR;',
            '  node [shape=box, style="filled", color="lightblue"];',
            '  overlap=false;',
            '  splines=true;',
            '  fontname="Helvetica";',
            '  edge [fontname="Helvetica", fontsize=10];'
        ]
        
        # Add nodes (classes)
        for class_name, info in self.classes.items():
            class_type = info.get("type", "class")
            package = info.get("package", "default")
            label = f"{class_name}\\n({class_type})\\n{package}"
            
            color = {
                "class": "lightblue",
                "object": "lightyellow", 
                "trait": "lightgreen"
            }.get(class_type, "lightgray")
            
            dot.append(f'  "{class_name}" [label="{label}", fillcolor="{color}"];')
        
        # Add edges (relationships)
        for class_name, relations in self.relationships.items():
            # Extends relationships (inheritance)
            for parent in relations.get("extends", []):
                if parent in self.classes:
                    dot.append(f'  "{class_name}" -> "{parent}" [label="extends", style="solid", arrowhead="empty", color="blue"];')
            
            # Usage relationships
            for used in relations.get("uses", []):
                if used in self.classes and used not in relations.get("extends", []):
                    dot.append(f'  "{class_name}" -> "{used}" [label="uses", style="dashed", color="gray"];')
        
        dot.append('}')
        return '\n'.join(dot)
    
    def generate_mermaid(self) -> str:
        """
        Generate Mermaid diagram code for class relationships.
        
        Returns:
            String containing the Mermaid diagram code
        """
        mermaid = ['classDiagram']
        
        # Add class definitions
        for class_name, info in self.classes.items():
            class_type = info.get("type", "class")
            mermaid.append(f'  class {class_name} {{')
            mermaid.append(f'    {info.get("package", "")}')
            mermaid.append(f'    {class_type}')
            mermaid.append('  }')
        
        # Add relationships
        for class_name, relations in self.relationships.items():
            # Extends relationships (inheritance)
            for parent in relations.get("extends", []):
                if parent in self.classes:
                    mermaid.append(f'  {parent} <|-- {class_name} : extends')
            
            # Usage relationships
            for used in relations.get("uses", []):
                if used in self.classes and used not in relations.get("extends", []):
                    mermaid.append(f'  {class_name} ..> {used} : uses')
        
        return '\n'.join(mermaid)

    def generate_class_diagram_for(self, class_name: str) -> str:
        """
        Generate a focused diagram for a specific class and its relationships.
        
        Args:
            class_name: Name of the class to focus on
            
        Returns:
            String containing the DOT diagram code
        """
        if class_name not in self.classes:
            return f'digraph "Class Diagram" {{ label = "Class {class_name} not found"; }}'
        
        dot = [
            'digraph "Class Diagram" {',
            '  rankdir=LR;',
            '  node [shape=box, style="filled", color="lightblue"];',
            '  overlap=false;',
            '  splines=true;',
            '  fontname="Helvetica";',
            '  edge [fontname="Helvetica", fontsize=10];'
        ]
        
        # Set of classes to include in the diagram
        related_classes = {class_name}
        
        # Add direct relationships
        if class_name in self.relationships:
            relations = self.relationships[class_name]
            
            # Add classes this one extends
            for parent in relations.get("extends", []):
                if parent in self.classes:
                    related_classes.add(parent)
            
            # Add classes this one uses
            for used in relations.get("uses", []):
                if used in self.classes:
                    related_classes.add(used)
        
        # Add classes that use this one
        for other, relations in self.relationships.items():
            if other == class_name:
                continue
            
            if class_name in relations.get("uses", []) or class_name in relations.get("extends", []):
                related_classes.add(other)
        
        # Add nodes for all related classes
        for related_class in related_classes:
            info = self.classes.get(related_class, {})
            class_type = info.get("type", "class")
            package = info.get("package", "default")
            label = f"{related_class}\\n({class_type})\\n{package}"
            
            # Highlight the focus class
            if related_class == class_name:
                dot.append(f'  "{related_class}" [label="{label}", fillcolor="orange", penwidth=2];')
            else:
                color = {
                    "class": "lightblue",
                    "object": "lightyellow", 
                    "trait": "lightgreen"
                }.get(class_type, "lightgray")
                dot.append(f'  "{related_class}" [label="{label}", fillcolor="{color}"];')
        
        # Add relationship edges between these classes only
        for src in related_classes:
            if src not in self.relationships:
                continue
                
            relations = self.relationships[src]
            
            # Extends relationships
            for parent in relations.get("extends", []):
                if parent in related_classes:
                    dot.append(f'  "{src}" -> "{parent}" [label="extends", style="solid", arrowhead="empty", color="blue"];')
            
            # Usage relationships
            for used in relations.get("uses", []):
                if used in related_classes and used not in relations.get("extends", []):
                    dot.append(f'  "{src}" -> "{used}" [label="uses", style="dashed", color="gray"];')
        
        dot.append('}')
        return '\n'.join(dot)