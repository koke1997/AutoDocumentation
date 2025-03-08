@echo off
setlocal

REM Root folder
mkdir autodocumentation

REM Top level files
type nul > autodocumentation\pyproject.toml
type nul > autodocumentation\README.md

REM Main package folder
mkdir autodocumentation\autodocumentation

REM Python files inside autodocumentation/
type nul > autodocumentation\autodocumentation\__init__.py
type nul > autodocumentation\autodocumentation\cli.py
type nul > autodocumentation\autodocumentation\config.py

REM Parsers folder and files
mkdir autodocumentation\autodocumentation\parsers
type nul > autodocumentation\autodocumentation\parsers\__init__.py
type nul > autodocumentation\autodocumentation\parsers\python_parser.py
type nul > autodocumentation\autodocumentation\parsers\java_parser.py
type nul > autodocumentation\autodocumentation\parsers\scala_parser.py

REM Generators folder and files
mkdir autodocumentation\autodocumentation\generators
type nul > autodocumentation\autodocumentation\generators\__init__.py
type nul > autodocumentation\autodocumentation\generators\sphinx_generator.py
type nul > autodocumentation\autodocumentation\generators\markdown_generator.py

REM LLM folder and files
mkdir autodocumentation\autodocumentation\llm
type nul > autodocumentation\autodocumentation\llm\__init__.py
type nul > autodocumentation\autodocumentation\llm\claude_client.py
type nul > autodocumentation\autodocumentation\llm\model_context_protocol.py

REM Utils folder and files
mkdir autodocumentation\autodocumentation\utils
type nul > autodocumentation\autodocumentation\utils\__init__.py
type nul > autodocumentation\autodocumentation\utils\file_utils.py

REM Other folders
mkdir autodocumentation\tests
mkdir autodocumentation\examples

echo Folder structure created successfully.
endlocal
