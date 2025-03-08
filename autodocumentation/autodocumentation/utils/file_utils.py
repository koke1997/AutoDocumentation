# autodocumentation/utils/file_utils.py
import os
from typing import List, Dict, Set

def find_files(directory: str, extensions: Set[str], recursive: bool = True) -> List[str]:
    """
    Find files with specific extensions in a directory.
    
    Args:
        directory: Directory to search
        extensions: Set of file extensions to find (e.g., {'.py', '.scala'})
        recursive: Whether to search recursively in subdirectories
        
    Returns:
        List of file paths
    """
    files = []
    
    if recursive:
        for root, _, filenames in os.walk(directory):
            for filename in filenames:
                if any(filename.endswith(ext) for ext in extensions):
                    files.append(os.path.join(root, filename))
    else:
        for filename in os.listdir(directory):
            if os.path.isfile(os.path.join(directory, filename)) and \
               any(filename.endswith(ext) for ext in extensions):
                files.append(os.path.join(directory, filename))
    
    return files

def ensure_directory(directory: str) -> None:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory: Directory path to ensure exists
    """
    os.makedirs(directory, exist_ok=True)