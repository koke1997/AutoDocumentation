# tests/test_scala_parser.py
import os
import sys
import pytest

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from autodocumentation.parsers.scala_parser import ScalaParser

def test_scala_parser_with_sample_file():
    """Test that the Scala parser can parse a sample file."""
    # Create a sample file path - adjust this to point to your example file
    sample_file = os.path.join(os.path.dirname(__file__), "..", "examples", "scala", "ReliableTransmission.scala")
    
    # Skip the test if the file doesn't exist
    if not os.path.exists(sample_file):
        pytest.skip(f"Sample file not found: {sample_file}")
    
    # Parse the file
    parser = ScalaParser()
    result = parser.parse_file(sample_file)
    
    # Verify basic structure
    assert 'package' in result
    assert result['package'] == 'services'
    assert 'objects' in result
    assert len(result['objects']) > 0
    
    # Check that we parsed the ReliableTransmission object
    reliable_transmission = next((obj for obj in result['objects'] if obj['name'] == 'ReliableTransmission'), None)
    assert reliable_transmission is not None
    
    # Check that we found the methods
    assert 'methods' in reliable_transmission
    method_names = [method['name'] for method in reliable_transmission['methods']]
    assert 'sendData' in method_names
    assert 'receiveData' in method_names