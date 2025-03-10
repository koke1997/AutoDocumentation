import os
import re
import glob

def clean_rst_files(directory):
    """Clean up RST files in the given directory."""
    # Get list of RST files
    rst_files = glob.glob(os.path.join(directory, "*.rst"))
    
    for file_path in rst_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove file path comments
        if content.startswith("// filepath:"):
            lines = content.split("\n")
            content = "\n".join(lines[1:])
        
        # Remove debug output
        content = re.sub(
            r"getWindowArguments \[\]\nApp is installed, enabling initial check and auto-updates\nChecking for updates\n+",
            "\n", 
            content
        )
        
        # Fix RST heading formats (ensure proper underline length)
        lines = content.split("\n")
        fixed_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            fixed_lines.append(line)
            
            # Check if next line exists and is an underline
            if i + 1 < len(lines) and lines[i+1] and all(c == '=' or c == '-' or c == '~' for c in lines[i+1]):
                if len(lines[i+1]) < len(line):
                    # Replace with proper length underline
                    char = lines[i+1][0]  # Get the character used (=, -, ~)
                    fixed_lines.append(char * len(line))
                    i += 2  # Skip the original underline
                    continue
            i += 1
        
        # Add class description if missing
        class_name = os.path.basename(file_path).replace(".rst", "")
        if "**Package:**" in content and not re.search(r'=+\n+[A-Za-z0-9\s]+\n+\*\*Package:\*\*', content, re.MULTILINE):
            content_parts = content.split("**Package:**", 1)
            header_parts = content_parts[0].split("\n")
            
            # Find where to insert the description
            for i, line in enumerate(header_parts):
                if line.strip() == class_name:
                    # Insert description after class name and underline
                    if i+2 < len(header_parts):
                        header_parts.insert(i+2, "\n" + class_name + " is responsible for handling web-related functionality in the application.\n")
                    break
            
            content = "\n".join(header_parts) + "\n**Package:**" + content_parts[1]
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(fixed_lines) if fixed_lines else content)
        
        print(f"Cleaned {os.path.basename(file_path)}")

if __name__ == "__main__":
    clean_rst_files(r"C:\Users\Ivan\Documents\GitHub\AutoDocumentation\docs\api\scala")