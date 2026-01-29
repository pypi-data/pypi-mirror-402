"""
Shared fixtures for convert_prepare tests
"""
import os
import pytest


@pytest.fixture(scope="session")
def ado_token():
    """
    Get ADO token from environment variable.
    
    In Azure Pipeline: Set via env in build.yml
    
    Returns:
        str: ADO token or empty string if not available
    """
    return os.getenv("SYSTEM_ACCESSTOKEN", "")