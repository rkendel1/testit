#!/usr/bin/env python3
"""
Test script to verify docker_utils.py works correctly with docker 7.1.0
This test verifies the fix for the "http+docker" URL scheme error.
"""
import os
import sys

def test_docker_client_creation():
    """Test that Docker client can be created successfully"""
    from app.docker_utils import create_docker_client
    import docker
    
    print(f"Testing with docker-py version: {docker.__version__}")
    
    # Test 1: With DOCKER_HOST set to unix socket
    print("\n=== Test 1: DOCKER_HOST=unix:///var/run/docker.sock ===")
    os.environ['DOCKER_HOST'] = 'unix:///var/run/docker.sock'
    try:
        client = create_docker_client()
        client.ping()
        print("✓ SUCCESS: Docker client created and ping successful")
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False
    
    # Test 2: Without DOCKER_HOST (default behavior)
    print("\n=== Test 2: No DOCKER_HOST (default) ===")
    if 'DOCKER_HOST' in os.environ:
        del os.environ['DOCKER_HOST']
    try:
        client = create_docker_client()
        client.ping()
        print("✓ SUCCESS: Docker client created and ping successful")
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False
    
    # Test 3: Verify no "http+docker" error
    print("\n=== Test 3: Verify no http+docker error ===")
    os.environ['DOCKER_HOST'] = 'unix:///var/run/docker.sock'
    try:
        client = create_docker_client()
        # This would previously fail with "Not supported URL scheme http+docker"
        version = client.version()
        print(f"✓ SUCCESS: Got Docker version: {version.get('Version', 'unknown')}")
    except Exception as e:
        error_msg = str(e)
        if 'http+docker' in error_msg:
            print(f"✗ FAILED: http+docker error still present: {error_msg}")
            return False
        else:
            print(f"✗ FAILED: {error_msg}")
            return False
    
    print("\n=== All Tests Passed! ===")
    return True

if __name__ == '__main__':
    try:
        success = test_docker_client_creation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test script failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
