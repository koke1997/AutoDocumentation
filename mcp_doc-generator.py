"""
MCP Documentation Generator

This script analyzes the Model Context Protocol (MCP) codebase and generates
comprehensive documentation with special focus on the filesystem server component.
"""

import os
import re
import json
import argparse
import subprocess
import networkx as nx
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any

# --- Configuration ---
SPHINX_CONFIG = """
project = '{project_name}'
copyright = '{year}, {author}'
author = '{author}'
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.graphviz',
    'sphinx.ext.inheritance_diagram',
    'sphinxcontrib.plantuml',
    'sphinx_scala',
    'sphinx_markdown_tables',
    'recommonmark',
]
templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
html_theme = 'sphinx_rtd_theme'
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}
"""

INDEX_RST = """
Welcome to {project_name} Documentation!
=========================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   overview
   architecture
   filesystem_server
   packages
   claude_review

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
"""

OVERVIEW_RST = """
Overview
========

Model Context Protocol (MCP)
---------------------------

{overview_content}

Project Structure
----------------

.. code-block:: text

{project_structure}
"""

ARCHITECTURE_RST = """
Architecture
===========

Component Diagram
----------------

.. graphviz::

{graphviz_content}

Module Dependencies
-----------------

.. image:: _static/module_dependencies.png
   :width: 100%
   :alt: Module dependencies graph
"""

FILESYSTEM_SERVER_RST = """
Filesystem Server
===============

{filesystem_readme}

Implementation Details
-------------------

{filesystem_details}

API Reference
-----------

{filesystem_api}
"""

PACKAGES_RST = """
Packages and Classes
==================

{packages_content}
"""

CLAUDE_REVIEW_RST = """
Documentation Notes for Claude Review
===================================

This section contains extracted code snippets and notes for Claude desktop app review.
You can copy sections from here into the Claude desktop app to get additional insights
and to enhance the documentation.

Filesystem Server Analysis
------------------------

{filesystem_analysis}

Key Components
------------

{key_components}

Suggested Questions for Claude
---------------------------

1. How does the MCP filesystem server handle file system operations?
2. What are the security considerations for the filesystem server implementation?
3. How could the filesystem server implementation be improved?
4. What are potential scalability limits of the current implementation?
5. How does the filesystem server fit into the broader MCP architecture?
"""

# Basic overview content for the MCP repository
MCP_OVERVIEW = """
The Model Context Protocol (MCP) is a system for letting language models access external data sources.
It consists of:

1. A protocol specification
2. Server implementations 
3. Client libraries to connect to MCP servers

The filesystem server component allows language models to access and manipulate files
in a controlled way, providing a secure interface to the file system.
"""

# --- Code Analysis ---
class MCPCodeAnalyzer:
    def __init__(self, root_dir: str, ignore_dirs: List[str] = None):
        self.root_dir = Path(root_dir).absolute()
        self.ignore_dirs = ignore_dirs or ['.git', 'target', 'project/target', '.idea', '.metals', '.bloop']
        self.packages = {}
        self.dependencies = {}
        self.classes = {}
        self.traits = {}
        self.objects = {}
        self.module_graph = nx.DiGraph()
        self.filesystem_files = []
        self.readme_content = ""
        
    def analyze(self) -> None:
        """Analyze the entire codebase."""
        print(f"Analyzing MCP code in {self.root_dir}...")
        self._load_filesystem_readme()
        scala_files = self._find_scala_files()
        
        for file_path in scala_files:
            rel_path = file_path.relative_to(self.root_dir)
            # Track filesystem related files
            if "filesystem" in str(rel_path):
                self.filesystem_files.append(file_path)
                
            with open(file_path, 'r', encoding='utf-8') as file:
                try:
                    content = file.read()
                    self._analyze_file(str(rel_path), content)
                except Exception as e:
                    print(f"Error analyzing {file_path}: {e}")
        
        self._build_dependency_graph()
    
    def _load_filesystem_readme(self) -> None:
        """Load the filesystem server README."""
        readme_path = self.root_dir / "src" / "filesystem" / "README.md"
        if readme_path.exists():
            with open(readme_path, 'r', encoding='utf-8') as f:
                self.readme_content = f.read()
        else:
            print(f"README not found at {readme_path}")
            # Try to find it elsewhere
            for readme in self.root_dir.glob("**/filesystem/**/README.md"):
                with open(readme, 'r', encoding='utf-8') as f:
                    self.readme_content = f.read()
                    print(f"Found README at {readme}")
                    break
    
    def _find_scala_files(self) -> List[Path]:
        """Find all Scala files in the project."""
        scala_files = []
        for path in self.root_dir.glob('**/*.scala'):
            if not any(ignore_dir in path.parts for ignore_dir in self.ignore_dirs):
                scala_files.append(path)
        return scala_files
    
    def _analyze_file(self, file_path: str, content: str) -> None:
        """Analyze a single Scala file."""
        # Extract package declaration
        package_match = re.search(r'package\s+([\w\.]+)', content)
        package_name = package_match.group(1) if package_match else "default"
        
        if package_name not in self.packages:
            self.packages[package_name] = {
                'files': [],
                'classes': [],
                'traits': [],
                'objects': [],
                'imports': set(),
            }
        
        self.packages[package_name]['files'].append(file_path)
        
        # Extract imports
        import_matches = re.finditer(r'import\s+([\w\.\_\{\}\,\s=>]+)', content)
        for match in import_matches:
            import_stmt = match.group(1).strip()
            self.packages[package_name]['imports'].add(import_stmt)
        
        # Extract classes
        class_matches = re.finditer(r'(case\s+)?class\s+(\w+)(?:\[.+?\])?(?:\(.*?\))?(?:\s+extends\s+([\w\.\s]+))?(?:\s+with\s+([\w\.\s]+))?', content)
        for match in class_matches:
            is_case = match.group(1) is not None
            class_name = match.group(2)
            extends = match.group(3)
            with_traits = match.group(4)
            
            class_info = {
                'name': class_name,
                'is_case': is_case,
                'extends': extends,
                'traits': with_traits,
                'package': package_name,
                'file': file_path,
            }
            
            self.packages[package_name]['classes'].append(class_name)
            self.classes[f"{package_name}.{class_name}"] = class_info
        
        # Extract traits
        trait_matches = re.finditer(r'trait\s+(\w+)(?:\[.+?\])?(?:\s+extends\s+([\w\.\s]+))?(?:\s+with\s+([\w\.\s]+))?', content)
        for match in trait_matches:
            trait_name = match.group(1)
            extends = match.group(2)
            with_traits = match.group(3)
            
            trait_info = {
                'name': trait_name,
                'extends': extends,
                'traits': with_traits,
                'package': package_name,
                'file': file_path,
            }
            
            self.packages[package_name]['traits'].append(trait_name)
            self.traits[f"{package_name}.{trait_name}"] = trait_info
        
        # Extract objects
        object_matches = re.finditer(r'object\s+(\w+)(?:\s+extends\s+([\w\.\s]+))?(?:\s+with\s+([\w\.\s]+))?', content)
        for match in object_matches:
            object_name = match.group(1)
            extends = match.group(2)
            with_traits = match.group(3)
            
            object_info = {
                'name': object_name,
                'extends': extends,
                'traits': with_traits,
                'package': package_name,
                'file': file_path,
            }
            
            self.packages[package_name]['objects'].append(object_name)
            self.objects[f"{package_name}.{object_name}"] = object_info
    
    def _build_dependency_graph(self) -> None:
        """Build a dependency graph of packages."""
        for package, info in self.packages.items():
            self.module_graph.add_node(package)
            
            # Add dependencies based on imports
            for import_stmt in info['imports']:
                # Process import statement to extract package
                parts = import_stmt.split('.')
                if len(parts) > 1:
                    # Handle Scala's import syntax
                    if '{' in import_stmt:
                        base_package = import_stmt.split('{')[0].strip()
                        if base_package and base_package in self.packages:
                            self.module_graph.add_edge(package, base_package)
                    else:
                        # Try to find the longest matching package
                        for i in range(len(parts) - 1, 0, -1):
                            potential_package = '.'.join(parts[:i])
                            if potential_package in self.packages:
                                self.module_graph.add_edge(package, potential_package)
                                break
    
    def generate_module_graph(self, output_path: str) -> None:
        """Generate a visualization of module dependencies."""
        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(self.module_graph)
        nx.draw(self.module_graph, pos, with_labels=True, 
                node_color='lightblue', node_size=1500, 
                font_size=10, font_weight='bold',
                arrows=True, arrowsize=15, edge_color='gray')
        plt.tight_layout()
        plt.savefig(output_path, format='png', dpi=300)
        plt.close()
    
    def generate_graphviz(self) -> str:
        """Generate Graphviz DOT representation of the package architecture."""
        dot = ["digraph G {", "  rankdir=LR;", "  node [shape=box, style=filled, fillcolor=lightblue];"]
        
        # Add nodes for packages
        for package in self.packages:
            # Use the last part of the package as the label
            label = package.split('.')[-1]
            dot.append(f'  "{package}" [label="{label}"];')
        
        # Add edges for dependencies
        for src, dst in self.module_graph.edges():
            dot.append(f'  "{src}" -> "{dst}";')
        
        dot.append("}")
        return "\n".join(dot)
    
    def generate_filesystem_details(self) -> str:
        """Generate details about the filesystem implementation."""
        fs_packages = [pkg for pkg in self.packages.keys() if "filesystem" in pkg]
        fs_classes = [name for name, info in self.classes.items() if any(pkg in name for pkg in fs_packages)]
        fs_traits = [name for name, info in self.traits.items() if any(pkg in name for pkg in fs_packages)]
        
        details = []
        details.append("Key Filesystem Server Packages\n")
        details.append("----------------------------\n\n")
        for pkg in fs_packages:
            details.append(f"* ``{pkg}``\n")
        
        details.append("\nKey Classes\n")
        details.append("----------\n\n")
        for cls in fs_classes:
            details.append(f"* ``{cls}``\n")
        
        details.append("\nKey Interfaces\n")
        details.append("-------------\n\n")
        for trait in fs_traits:
            details.append(f"* ``{trait}``\n")
        
        return "".join(details)
    
    def extract_filesystem_api(self) -> str:
        """Extract API details from the filesystem implementation."""
        api_content = []
        
        # Look for key API classes in filesystem packages
        for name, info in self.classes.items():
            if "filesystem" in name and ("Server" in name or "Service" in name or "Handler" in name):
                api_content.append(f"``{name}``\n")
                api_content.append("-" * len(name) + "\n\n")
                
                # Methods from the file (this is a simplified heuristic)
                file_path = self.root_dir / info['file']
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Look for method declarations - this is a simplistic approach
                        methods = re.findall(r'def\s+(\w+)(?:\[.+?\])?(?:\(.*?\))', content)
                        if methods:
                            api_content.append("Methods:\n\n")
                            for method in methods:
                                api_content.append(f"* ``{method}``\n")
                            api_content.append("\n")
        
        return "".join(api_content)
    
    def generate_project_structure(self) -> str:
        """Generate a text representation of the project structure."""
        structure = []
        
        def add_directory(path, indent=0):
            if path.name in self.ignore_dirs:
                return
            
            if path.is_dir():
                structure.append(f"{' ' * indent}├── {path.name}/")
                
                # Process subdirectories first
                subdirs = [p for p in path.iterdir() if p.is_dir() and p.name not in self.ignore_dirs]
                for subdir in sorted(subdirs):
                    add_directory(subdir, indent + 4)
                
                # Then process files
                files = [p for p in path.iterdir() if p.is_file() and (p.name.endswith('.scala') or p.name == "README.md")]
                for file in sorted(files):
                    structure.append(f"{' ' * indent}│   ├── {file.name}")
        
        add_directory(self.root_dir)
        return "\n".join(structure)
    
    def extract_filesystem_analysis(self) -> Dict[str, str]:
        """Extract code from filesystem implementation for Claude review."""
        analysis = {}
        
        # Get representative filesystem files
        for file_path in self.filesystem_files[:5]:  # Limit to 5 files
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Limit to first 50 lines to avoid overwhelming Claude
                    content_lines = content.split("\n")[:50]
                    rel_path = file_path.relative_to(self.root_dir)
                    analysis[str(rel_path)] = "\n".join(content_lines)
        
        return analysis
    
    def extract_key_components(self) -> Dict[str, List]:
        """Extract key components for Claude review."""
        # Filter for filesystem related components
        fs_classes = [name for name, info in self.classes.items() if "filesystem" in name]
        fs_traits = [name for name, info in self.traits.items() if "filesystem" in name]
        fs_objects = [name for name, info in self.objects.items() if "filesystem" in name]
        
        return {
            'classes': fs_classes,
            'traits': fs_traits,
            'objects': fs_objects
        }

# --- Documentation Generator ---
class MCPDocGenerator:
    def __init__(self, code_analyzer: MCPCodeAnalyzer, output_dir: str, project_name: str, author: str):
        self.analyzer = code_analyzer
        self.output_dir = Path(output_dir)
        self.project_name = project_name
        self.author = author
    
    def init_sphinx(self) -> None:
        """Initialize Sphinx documentation structure."""
        docs_dir = self.output_dir
        docs_dir.mkdir(exist_ok=True)
        
        # Create conf.py
        with open(docs_dir / 'conf.py', 'w') as f:
            import datetime
            year = datetime.datetime.now().year
            f.write(SPHINX_CONFIG.format(
                project_name=self.project_name,
                year=year,
                author=self.author
            ))
        
        # Create index.rst
        with open(docs_dir / 'index.rst', 'w') as f:
            f.write(INDEX_RST.format(project_name=self.project_name))
        
        # Create _static directory
        static_dir = docs_dir / '_static'
        static_dir.mkdir(exist_ok=True)
        
        # Generate module dependencies graph
        self.analyzer.generate_module_graph(str(static_dir / 'module_dependencies.png'))
    
    def generate_overview(self) -> None:
        """Generate overview documentation."""
        # Get project structure
        project_structure = self.analyzer.generate_project_structure()
        
        # Write to overview.rst
        with open(self.output_dir / 'overview.rst', 'w') as f:
            f.write(OVERVIEW_RST.format(
                overview_content=MCP_OVERVIEW,
                project_structure="\n".join(f"    {line}" for line in project_structure.split('\n'))
            ))
    
    def generate_architecture(self) -> None:
        """Generate architecture documentation."""
        graphviz_content = self.analyzer.generate_graphviz()
        
        # Write to architecture.rst
        with open(self.output_dir / 'architecture.rst', 'w') as f:
            f.write(ARCHITECTURE_RST.format(
                graphviz_content="\n".join(f"    {line}" for line in graphviz_content.split('\n'))
            ))
    
    def generate_filesystem_doc(self) -> None:
        """Generate filesystem server documentation."""
        filesystem_details = self.analyzer.generate_filesystem_details()
        filesystem_api = self.analyzer.extract_filesystem_api()
        
        # Write to filesystem_server.rst
        with open(self.output_dir / 'filesystem_server.rst', 'w') as f:
            f.write(FILESYSTEM_SERVER_RST.format(
                filesystem_readme=self.analyzer.readme_content,
                filesystem_details=filesystem_details,
                filesystem_api=filesystem_api
            ))
    
    def generate_packages_doc(self) -> None:
        """Generate packages documentation."""
        packages_content = []
        
        for package, info in self.analyzer.packages.items():
            packages_content.append(f"{package}\n" + "-" * len(package) + "\n\n")
            
            if info['classes']:
                packages_content.append("Classes:\n\n")
                for class_name in info['classes']:
                    packages_content.append(f"* ``{class_name}``\n")
                packages_content.append("\n")
            
            if info['traits']:
                packages_content.append("Traits:\n\n")
                for trait_name in info['traits']:
                    packages_content.append(f"* ``{trait_name}``\n")
                packages_content.append("\n")
            
            if info['objects']:
                packages_content.append("Objects:\n\n")
                for object_name in info['objects']:
                    packages_content.append(f"* ``{object_name}``\n")
                packages_content.append("\n")
        
        # Write to packages.rst
        with open(self.output_dir / 'packages.rst', 'w') as f:
            f.write(PACKAGES_RST.format(
                packages_content="".join(packages_content)
            ))
    
    def generate_claude_review(self) -> None:
        """Generate notes for Claude review."""
        # Extract filesystem code samples
        fs_analysis = self.analyzer.extract_filesystem_analysis()
        fs_analysis_text = []
        
        for file_path, content in fs_analysis.items():
            fs_analysis_text.append(f"File: ``{file_path}``\n\n.. code-block:: scala\n\n{content}\n\n")
        
        # Extract key components
        key_components = self.analyzer.extract_key_components()
        key_components_text = []
        
        key_components_text.append("Key Classes:\n\n")
        for class_name in key_components['classes'][:5]:  # Limit to 5
            key_components_text.append(f"* ``{class_name}``\n")
        
        key_components_text.append("\nKey Traits:\n\n")
        for trait_name in key_components['traits'][:5]:  # Limit to 5
            key_components_text.append(f"* ``{trait_name}``\n")
        
        key_components_text.append("\nKey Objects:\n\n")
        for object_name in key_components['objects'][:5]:  # Limit to 5
            key_components_text.append(f"* ``{object_name}``\n")
        
        # Write to claude_review.rst
        with open(self.output_dir / 'claude_review.rst', 'w') as f:
            f.write(CLAUDE_REVIEW_RST.format(
                filesystem_analysis="".join(fs_analysis_text),
                key_components="".join(key_components_text)
            ))
    
    def create_documentation_json(self) -> None:
        """Create a JSON file with filesystem server information for Claude."""
        fs_data = {
            'project_name': self.project_name,
            'filesystem_readme': self.analyzer.readme_content,
            'filesystem_classes': [name for name, info in self.analyzer.classes.items() if "filesystem" in name],
            'filesystem_traits': [name for name, info in self.analyzer.traits.items() if "filesystem" in name],
            'filesystem_objects': [name for name, info in self.analyzer.objects.items() if "filesystem" in name],
        }
        
        with open(self.output_dir / 'filesystem_info.json', 'w') as f:
            json.dump(fs_data, f, indent=2)
    
    def build_docs(self) -> None:
        """Build the Sphinx documentation."""
        try:
            subprocess.run(['sphinx-build', str(self.output_dir), str(self.output_dir / '_build')], check=True)
            print(f"Documentation successfully built at {self.output_dir / '_build'}")
        except subprocess.CalledProcessError as e:
            print(f"Error building documentation: {e}")
        except FileNotFoundError:
            print("sphinx-build command not found. Make sure Sphinx is installed.")
    
    def generate(self) -> None:
        """Generate the complete documentation."""
        self.init_sphinx()
        self.generate_overview()
        self.generate_architecture()
        self.generate_filesystem_doc()
        self.generate_packages_doc()
        self.generate_claude_review()
        self.create_documentation_json()
        self.build_docs()

# --- Main Function ---
def main():
    parser = argparse.ArgumentParser(description='Generate documentation for the MCP project')
    parser.add_argument('--src', required=True, help='Source directory of the MCP project')
    parser.add_argument('--output', default='docs', help='Output directory for documentation')
    parser.add_argument('--project-name', default='Model Context Protocol', help='Name of the project')
    parser.add_argument('--author', default='MCP Doc Generator', help='Author of the documentation')
    
    args = parser.parse_args()
    
    # Install required dependencies if not already installed
    required_packages = [
        'sphinx', 'sphinx-rtd-theme', 'sphinxcontrib-plantuml', 
        'networkx', 'matplotlib', 'recommonmark', 'sphinx-markdown-tables'
    ]
    
    try:
        import importlib
        for package in required_packages:
            try:
                importlib.import_module(package.replace('-', '_').replace('_tables', ''))
            except ImportError:
                print(f"Installing {package}...")
                subprocess.check_call(['pip', 'install', package])
        
        # Install sphinx-scala
        subprocess.check_call(['pip', 'install', 'git+https://github.com/scala/scala-sphinx.git#egg=sphinx-scala'])
        
    except Exception as e:
        print(f"Error installing dependencies: {e}")
        print("Please install the following packages manually:")
        for package in required_packages:
            print(f"  - {package}")
        print("  - sphinx-scala (from https://github.com/scala/scala-sphinx.git)")
        return
    
    # Clone the repository if it doesn't exist
    if not os.path.exists(args.src):
        print(f"Source directory {args.src} does not exist. Cloning the repository...")
        try:
            subprocess.check_call(['git', 'clone', 'https://github.com/modelcontextprotocol/servers.git', args.src])
        except subprocess.CalledProcessError as e:
            print(f"Error cloning repository: {e}")
            return
    
    # Analyze code
    analyzer = MCPCodeAnalyzer(args.src)
    analyzer.analyze()
    
    # Generate documentation
    doc_generator = MCPDocGenerator(analyzer, args.output, args.project_name, args.author)
    doc_generator.generate()
    
    print(f"Documentation generated successfully in {args.output}")
    print("\nNext steps:")
    print("1. Open the generated documentation in your browser")
    print("2. Use the 'Documentation Notes for Claude Review' section with the Claude desktop app")
    print("3. Share the filesystem_info.json file with Claude for detailed analysis")

if __name__ == "__main__":
    main()