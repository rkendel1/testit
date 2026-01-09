#!/usr/bin/env python3
"""
Test script to verify dockerfile_generator.py generates proper Dockerfiles
This test verifies the fix for debconf errors during apt-get install.
"""
import sys
import tempfile
from pathlib import Path
from app.dockerfile_generator import DockerfileGenerator
from app.models import LanguageType


def test_python_dockerfile():
    """Test Python Dockerfile generation includes DEBIAN_FRONTEND"""
    print("\n=== Test 1: Python Dockerfile Generation ===")
    
    # Create temporary directory with requirements.txt
    with tempfile.TemporaryDirectory() as temp_dir:
        requirements_file = Path(temp_dir) / "requirements.txt"
        requirements_file.write_text("flask==2.0.0\n")
        
        dockerfile = DockerfileGenerator.generate_dockerfile(LanguageType.PYTHON, temp_dir)
        
        # Check that DEBIAN_FRONTEND is set
        if "ENV DEBIAN_FRONTEND=noninteractive" in dockerfile:
            print("✓ SUCCESS: Python Dockerfile contains DEBIAN_FRONTEND=noninteractive")
        else:
            print("✗ FAILED: Python Dockerfile missing DEBIAN_FRONTEND setting")
            print(f"Generated Dockerfile:\n{dockerfile}")
            return False
        
        # Check that apt-get install comes after DEBIAN_FRONTEND
        debian_pos = dockerfile.find("ENV DEBIAN_FRONTEND=noninteractive")
        aptget_pos = dockerfile.find("apt-get update")
        
        if debian_pos < aptget_pos:
            print("✓ SUCCESS: DEBIAN_FRONTEND is set before apt-get commands")
        else:
            print("✗ FAILED: DEBIAN_FRONTEND is not before apt-get commands")
            return False
    
    return True


def test_node_dockerfile():
    """Test Node.js Dockerfile generation includes DEBIAN_FRONTEND"""
    print("\n=== Test 2: Node.js Dockerfile Generation ===")
    
    # Create temporary directory with package.json
    with tempfile.TemporaryDirectory() as temp_dir:
        package_file = Path(temp_dir) / "package.json"
        package_file.write_text('{"name": "test", "version": "1.0.0"}')
        
        dockerfile = DockerfileGenerator.generate_dockerfile(LanguageType.NODE, temp_dir)
        
        # Check that DEBIAN_FRONTEND is set
        if "ENV DEBIAN_FRONTEND=noninteractive" in dockerfile:
            print("✓ SUCCESS: Node.js Dockerfile contains DEBIAN_FRONTEND=noninteractive")
        else:
            print("✗ FAILED: Node.js Dockerfile missing DEBIAN_FRONTEND setting")
            print(f"Generated Dockerfile:\n{dockerfile}")
            return False
        
        # Check that apt-get install comes after DEBIAN_FRONTEND
        debian_pos = dockerfile.find("ENV DEBIAN_FRONTEND=noninteractive")
        aptget_pos = dockerfile.find("apt-get update")
        
        if debian_pos < aptget_pos:
            print("✓ SUCCESS: DEBIAN_FRONTEND is set before apt-get commands")
        else:
            print("✗ FAILED: DEBIAN_FRONTEND is not before apt-get commands")
            return False
    
    return True


def test_java_dockerfile():
    """Test Java Dockerfile generation (no apt-get, so no DEBIAN_FRONTEND needed)"""
    print("\n=== Test 3: Java Dockerfile Generation (informational) ===")
    
    # Create temporary directory with pom.xml
    with tempfile.TemporaryDirectory() as temp_dir:
        pom_file = Path(temp_dir) / "pom.xml"
        pom_file.write_text('<project></project>')
        
        dockerfile = DockerfileGenerator.generate_dockerfile(LanguageType.JAVA, temp_dir)
        
        # Java Dockerfiles use official images and don't run apt-get
        print("✓ INFO: Java Dockerfile generated (uses official images, no apt-get)")
    
    return True


def test_go_dockerfile():
    """Test Go Dockerfile generation (no apt-get, so no DEBIAN_FRONTEND needed)"""
    print("\n=== Test 4: Go Dockerfile Generation (informational) ===")
    
    # Create temporary directory with go.mod
    with tempfile.TemporaryDirectory() as temp_dir:
        go_mod = Path(temp_dir) / "go.mod"
        go_mod.write_text('module test\n')
        
        dockerfile = DockerfileGenerator.generate_dockerfile(LanguageType.GO, temp_dir)
        
        # Go Dockerfiles use alpine images and don't run apt-get
        print("✓ INFO: Go Dockerfile generated (uses alpine, no apt-get)")
    
    return True


if __name__ == '__main__':
    try:
        print("Testing Dockerfile Generator...")
        
        all_passed = True
        all_passed = test_python_dockerfile() and all_passed
        all_passed = test_node_dockerfile() and all_passed
        all_passed = test_java_dockerfile() and all_passed
        all_passed = test_go_dockerfile() and all_passed
        
        if all_passed:
            print("\n=== All Tests Passed! ===")
            sys.exit(0)
        else:
            print("\n=== Some Tests Failed ===")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n✗ Test script failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
