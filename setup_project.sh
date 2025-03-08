#!/bin/bash
# setup_project.sh

# Create project directory structure
mkdir -p autodocumentation/{parsers,generators,llm,utils} tests examples/{scala,python}

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install pytest black isort mypy sphinx sphinxcontrib-scaladoc

# Create pyproject.toml
cat > pyproject.toml << 'EOL'
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "autodocumentation"
version = "0.1.0"
authors = [
    {name = "Your Name", email = "your.email@example.com"},
]
description = "Automatic documentation generator using Claude"
readme = "README.md"
requires-python = ">=3.8"
classifiers = [
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
]
dependencies = [
    "argparse",
]

[project.scripts]
autodoc = "autodocumentation.cli:main"

[project.urls]
"Homepage" = "https://github.com/yourusername/autodocumentation"
"Bug Tracker" = "https://github.com/yourusername/autodocumentation/issues"
EOL

# Create README.md
cat > README.md << 'EOL'
# AutoDocumentation

AutoDocumentation is a tool that automatically generates high-quality documentation from source code using Claude AI.

## Features

- Parse source code from multiple programming languages (Python, Scala)
- Generate comprehensive documentation using Claude AI
- Support for multiple output formats (Sphinx, Markdown)
- Command-line interface for easy integration into workflows

## Installation

```bash
pip install autodocumentation