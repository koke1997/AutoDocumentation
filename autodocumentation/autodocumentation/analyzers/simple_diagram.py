import os
import re
import networkx as nx
import subprocess
from pathlib import Path
from typing import Dict, Set, Optional

def generate_class_diagram(class_name: str, source_dir: str, output_dir: str) -> Optional[str]:
    """
    Generate a class diagram for a specific class using NetworkX and Graphviz.
    
    Args:
        class_name: Name of the class to diagram
        source_dir: Directory containing source code
        output_dir: Directory to save diagram files
        
    Returns:
        Path to generated SVG file or None if generation failed
    """
    # Create a directed graph
    G = nx.DiGraph()
    
    # Find all Scala files
    scala_files = list(Path(source_dir).glob("**/*.scala"))
    
    # Extract class information
    classes = {}
    for file_path in scala_files:
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Extract package
            package_match = re.search(r'package\s+([^\s{;]+)', content)
            package = package_match.group(1) if package_match else "unknown"
            
            # Extract classes/objects/traits
            for match in re.finditer(r'(class|object|trait)\s+([^\s({]+)', content):
                cls_type = match.group(1)
                cls_name = match.group(2)
                
                # Add node to graph
                G.add_node(cls_name, 
                          type=cls_type, 
                          package=package,
                          file=file_path.name,
                          fillcolor={"class": "lightblue", "object": "lightyellow", "trait": "lightgreen"}.get(cls_type, "lightgray"))
                
                # Check relations with our target class
                if cls_name != class_name:
                    # If target class is used in this class's content
                    if class_name in content:
                        G.add_edge(cls_name, class_name, relationship="uses")
                    
                    # If this class is used in our target class
                    if class_name in classes and cls_name in classes[class_name]["content"]:
                        G.add_edge(class_name, cls_name, relationship="uses")
                
                classes[cls_name] = {
                    "type": cls_type,
                    "package": package,
                    "content": content
                }
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    # If target class not found, create a placeholder node
    if class_name not in G.nodes():
        G.add_node(class_name, type="class", package="unknown", fillcolor="orange")
    else:
        # Highlight the target class
        G.nodes[class_name]["fillcolor"] = "orange"
        G.nodes[class_name]["penwidth"] = 2
    
    # Keep only nodes connected to the target class (within distance 1)
    nodes_to_keep = {class_name} | set(nx.neighbors(G, class_name)) | {n for n in G.nodes() if class_name in nx.neighbors(G, n)}
    nodes_to_remove = [n for n in G.nodes() if n not in nodes_to_keep]
    G.remove_nodes_from(nodes_to_remove)
    
    # Generate DOT file
    dot_file = os.path.join(output_dir, f"{class_name}_diagram.dot")
    svg_file = os.path.join(output_dir, f"{class_name}_diagram.svg")
    
    with open(dot_file, 'w', encoding='utf-8') as f:
        f.write('digraph "Class Diagram" {\n')
        f.write('  rankdir=LR;\n')
        f.write('  node [shape=box, style="filled"];\n')
        f.write('  fontname="Helvetica";\n')
        
        # Add nodes
        for node, attrs in G.nodes(data=True):
            label = f"{node}\\n({attrs.get('type', 'class')})\\n{attrs.get('package', 'unknown')}"
            fillcolor = attrs.get('fillcolor', 'lightgray')
            penwidth = attrs.get('penwidth', 1)
            f.write(f'  "{node}" [label="{label}", fillcolor="{fillcolor}", penwidth={penwidth}];\n')
        
        # Add edges
        for src, dst, attrs in G.edges(data=True):
            relationship = attrs.get('relationship', 'connects to')
            if relationship == "extends":
                f.write(f'  "{src}" -> "{dst}" [label="extends", style="solid", arrowhead="empty", color="blue"];\n')
            else:
                f.write(f'  "{src}" -> "{dst}" [label="uses", style="dashed", color="gray"];\n')
        
        f.write('}\n')
    
    # Run dot command
    try:
        subprocess.run(["dot", "-Tsvg", dot_file, "-o", svg_file], 
                      check=True, capture_output=True)
        return f"{class_name}_diagram.svg"
    except subprocess.CalledProcessError as e:
        print(f"Error generating diagram: {e.stderr}")
        return None
    except FileNotFoundError:
        print("Error: Graphviz not found. Please ensure 'dot' is in your PATH.")
        return None