"""
FastAPI Swagger Splitter - Custom Swagger UI with tag-based filtering and download links.

This package provides enhanced Swagger UI documentation for FastAPI applications with:
- Custom CSS styling
- Tag-based OpenAPI JSON filtering
- Download links for complete and tag-specific OpenAPI schemas
- Search functionality for tags
"""

from fastapi_swagger_splitter.splitter import setup_swagger_splitter

__version__ = "0.1.1"
__all__ = ["setup_swagger_splitter"]
