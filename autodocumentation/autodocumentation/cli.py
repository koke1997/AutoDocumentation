# autodocumentation/cli.py
import argparse
import os
import sys
import time
from typing import List, Optional
from pathlib import Path
import tqdm

from autodocumentation.parsers.python_parser import PythonParser
from autodocumentation.parsers.scala_parser import ScalaParser
try:
    from autodocumentation.parsers.java_parser import JavaParser
except ImportError:
    JavaParser = None
from autodocumentation.generators.sphinx_generator import SphinxGenerator
from autodocumentation.generators.scala_sphinx_generator import ScalaSphinxGenerator
from autodocumentation.generators.markdown_generator import MarkdownGenerator
from autodocumentation.llm.model_context_protocol import ModelContextProtocolClient
from autodocumentation.config import Config
from autodocumentation.utils.file_utils import find_files, ensure_directory

def main(args: List[str] = None) -> int:
    """
    Main entry point for the AutoDocumentation CLI.
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    parser = argparse.ArgumentParser(
        description="AutoDocumentation: Generate documentation from source code using Claude"
    )
    
    parser.add_argument(
        "source",
        help="Source file or directory to document"
    )
    
    parser.add_argument(
        "--output-dir", "-o",
        help="Output directory for documentation (default: docs)"
    )
    
    parser.add_argument(
        "--format", "-f",
        choices=["sphinx", "markdown"],
        help="Documentation format (default: sphinx)"
    )
    
    parser.add_argument(
        "--claude-executable",
        help="Path to the Claude Desktop App executable"
    )
    
    parser.add_argument(
        "--recursive", "-r",
        action="store_true",
        help="Recursively process directories"
    )
    
    parser.add_argument(
        "--language",
        choices=["python", "java", "scala", "auto"],
        help="Source code language (default: auto - detect by file extension)"
    )
    
    parser.add_argument(
        "--model",
        help="Claude model to use (e.g., claude-3-sonnet-20240229)"
    )
    
    parser.add_argument(
        "--temperature",
        type=float,
        help="Temperature for generation (0.0 to 1.0)"
    )
    
    parser.add_argument(
        "--max-tokens",
        type=int,
        help="Maximum tokens for generation"
    )
    
    parser.add_argument(
        "--config",
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Process files in batch mode (faster, but less verbose output)"
    )
    
    cli_args = parser.parse_args(args)
    
    # Load configuration
    config = Config(cli_args.config)
    
    # Override config with command line arguments
    output_dir = cli_args.output_dir or config.get("output_dir", "docs")
    doc_format = cli_args.format or config.get("default_format", "sphinx")
    language = cli_args.language or config.get("default_language", "auto")
    claude_executable = cli_args.claude_executable or config.get("claude_executable")
    model = cli_args.model or config.get("model", "claude-3-opus-20240229")
    temperature = cli_args.temperature or config.get("temperature", 0.2)
    max_tokens = cli_args.max_tokens or config.get("max_tokens", 4000)
    
    # Initialize the Claude client
    try:
        claude_client = ModelContextProtocolClient(claude_executable)
        print(f"Initialized Claude client with model: {model}")
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    # Check if source exists
    if not os.path.exists(cli_args.source):
        print(f"Error: Source path '{cli_args.source}' does not exist", file=sys.stderr)
        return 1
    
    # Create output directory
    ensure_directory(output_dir)
    
    # Find files to process
    files_to_process = []
    
    if os.path.isfile(cli_args.source):
        # Single file processing
        file_path = cli_args.source
        file_language = detect_language(file_path) if language == "auto" else language
        if file_language:
            files_to_process.append((file_path, file_language))
        else:
            print(f"Warning: Could not determine language for {file_path}. Skipping.", file=sys.stderr)
    else:
        # Directory processing
        extensions = {".py", ".scala", ".java"}
        found_files = find_files(cli_args.source, extensions, cli_args.recursive)
        
        for file_path in found_files:
            file_language = detect_language(file_path) if language == "auto" else language
            if file_language and (language == "auto" or file_path.endswith(f".{language}")):
                files_to_process.append((file_path, file_language))
    
    if not files_to_process:
        print(f"Warning: No files found to process", file=sys.stderr)
        return 0
    
    # Process files
    total_files = len(files_to_process)
    print(f"\nFound {total_files} files to process")
    
    if cli_args.batch:
        # Process files in batch mode
        print(f"Processing files in batch mode using {model}...")
        results = claude_client.run_batch_documentation(
            files_with_languages=files_to_process,
            output_dir=output_dir,
            doc_format=doc_format,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Print summary
        success_count = len(results["success"])
        error_count = len(results["failure"])
        
        print(f"\nDocumentation generation complete!")
        print(f"✓ Successfully processed: {success_count}/{total_files} files")
        
        if error_count > 0:
            print(f"✗ Errors encountered: {error_count} files")
            for file_path, error_msg in results["failure"]:
                print(f"  - {os.path.basename(file_path)}: {error_msg}")
        
        return 0 if error_count == 0 else 1
    else:
        # Process each file individually
        try:
            import tqdm
            progress_bar = tqdm.tqdm(total=total_files, desc="Generating Documentation")
        except ImportError:
            progress_bar = None
            
        success_count = 0
        error_count = 0
        skipped_count = 0
        
        for index, (file_path, file_language) in enumerate(files_to_process):
            try:
                print(f"\n[{index+1}/{total_files}] Processing {file_path} as {file_language}...")
                
                # Initialize parser based on language
                parser = get_parser(file_language)
                if not parser:
                    print(f"Skipping {file_path}: Language '{file_language}' not supported")
                    skipped_count += 1
                    continue
                
                # Initialize generator based on format and language
                generator = get_generator(doc_format, file_language, output_dir)
                if not generator:
                    print(f"Skipping {file_path}: Format '{doc_format}' not supported for {file_language}")
                    skipped_count += 1
                    continue
                
                # Parse the code
                print(f"  Parsing {file_path}...")
                start_time = time.time()
                parsed_code = parser.parse_file(file_path)
                parse_time = time.time() - start_time
                
                # Check for parse errors
                if 'error' in parsed_code:
                    print(f"  Error parsing {file_path}: {parsed_code['error']}")
                    error_count += 1
                    continue
                
                # Read the original source code
                with open(file_path, 'r', encoding='utf-8') as f:
                    source_code = f.read()
                
                # Generate documentation using Claude
                print(f"  Generating documentation with Claude ({model})...")
                start_time = time.time()
                documentation = claude_client.generate_documentation(
                    code_snippet=source_code,
                    language=file_language,
                    doc_format="rst" if doc_format == "sphinx" else "markdown",
                    context=f"This file is from the project at {os.path.abspath(cli_args.source)}",
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                claude_time = time.time() - start_time
                
                # Generate output using the appropriate generator
                print(f"  Creating documentation files...")
                output_file = generator.generate_from_parsed_code(parsed_code, documentation)
                
                print(f"  ✓ Successfully generated documentation: {output_file}")
                print(f"    Parse time: {parse_time:.2f}s, Claude time: {claude_time:.2f}s")
                success_count += 1
                
            except KeyboardInterrupt:
                print("\nProcess interrupted by user. Exiting...")
                if progress_bar:
                    progress_bar.close()
                break
            except Exception as e:
                print(f"  ✗ Error processing {file_path}: {str(e)}", file=sys.stderr)
                error_count += 1
                
            if progress_bar:
                progress_bar.update(1)
        
        if progress_bar:
            progress_bar.close()
            
        print(f"\nDocumentation generation complete!")
        print(f"✓ Successfully processed: {success_count} files")
        if skipped_count:
            print(f"⚠ Skipped: {skipped_count} files")
        if error_count:
            print(f"✗ Errors encountered: {error_count} files")
        
        return 0 if error_count == 0 else 1

def detect_language(file_path: str) -> Optional[str]:
    """
    Detect language from file extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Detected language or None if not recognized
    """
    ext = Path(file_path).suffix.lower()
    language_map = {
        ".py": "python",
        ".scala": "scala",
        ".java": "java"
    }
    return language_map.get(ext)

def get_parser(language: str):
    """
    Get the appropriate parser for the language.
    
    Args:
        language: Programming language
        
    Returns:
        Parser instance or None if language not supported
    """
    if language == "python":
        return PythonParser()
    elif language == "scala":
        return ScalaParser()
    elif language == "java":
        if JavaParser:
            return JavaParser()
        else:
            print("Java parser not available. Please make sure required dependencies are installed.")
            return None
    return None

def get_generator(doc_format: str, language: str, output_dir: str):
    """
    Get the appropriate documentation generator.
    
    Args:
        doc_format: Documentation format
        language: Programming language
        output_dir: Output directory
        
    Returns:
        Generator instance or None if format not supported
    """
    if doc_format == "sphinx":
        if language == "scala":
            return ScalaSphinxGenerator(output_dir)
        else:
            return SphinxGenerator(output_dir)
    elif doc_format == "markdown":
        return MarkdownGenerator(output_dir)
    return None

if __name__ == "__main__":
    sys.exit(main())