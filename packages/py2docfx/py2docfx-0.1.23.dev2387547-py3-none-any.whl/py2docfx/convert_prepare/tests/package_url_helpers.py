"""Helper utilities for constructing package URLs from different sources."""


def get_package_url(pypi_url: str, ado_url: str, ado_token: str = None) -> str:
    """
    Get the appropriate package URL based on whether an ADO token is provided.
    
    Args:
        pypi_url: The PyPI (files.pythonhosted.org) URL for the package
        ado_url: The Azure DevOps base URL for the package (without authentication)
        ado_token: Optional ADO authentication token
        
    Returns:
        The PyPI URL if ado_token is None or empty, otherwise the authenticated ADO URL
    """
    if not ado_token:
        return pypi_url
    return f"https://:{ado_token}@{ado_url}"
