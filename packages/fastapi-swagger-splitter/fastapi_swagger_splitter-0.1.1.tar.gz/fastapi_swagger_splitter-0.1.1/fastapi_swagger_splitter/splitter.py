"""
Swagger customization utilities for FastAPI.
Provides custom CSS, JavaScript, and tag-based OpenAPI filtering.
"""
import logging
from typing import Any, Dict, Set

from fastapi import Request
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


def get_all_tags(openapi_schema: Dict[str, Any]) -> list[str]:
    """Extract all unique tags from the OpenAPI schema."""
    tags = set()

    # Get tags from document.tags array
    if "tags" in openapi_schema and openapi_schema["tags"]:
        for tag in openapi_schema["tags"]:
            if isinstance(tag, dict) and "name" in tag:
                tags.add(tag["name"])
            elif isinstance(tag, str):
                tags.add(tag)

    # Extract tags from path operations
    if "paths" in openapi_schema:
        for path_item in openapi_schema["paths"].values():
            if isinstance(path_item, dict):
                for operation in path_item.values():
                    if isinstance(operation, dict) and "tags" in operation:
                        for tag in operation["tags"]:
                            tags.add(tag)

    return sorted(list(tags))


def filter_openapi_by_tag(openapi_schema: Dict[str, Any], tag: str) -> Dict[str, Any]:
    """Filter OpenAPI schema to include only paths and schemas for a specific tag."""
    used_schemas: Set[str] = set()

    # Filter paths
    filtered_paths: Dict[str, Any] = {}
    if "paths" in openapi_schema:
        for path, path_item in openapi_schema["paths"].items():
            filtered_path_item: Dict[str, Any] = {}
            if isinstance(path_item, dict):
                for method, operation in path_item.items():
                    if (
                        isinstance(operation, dict)
                        and "tags" in operation
                        and tag in operation["tags"]
                    ):
                        filtered_path_item[method] = operation
                        # Collect schema references from this operation
                        _collect_schema_refs(operation, used_schemas)

            if filtered_path_item:
                filtered_paths[path] = filtered_path_item

    # Filter components/schemas to only include used ones
    filtered_components = None
    if "components" in openapi_schema and openapi_schema["components"]:
        components = openapi_schema["components"]
        if "schemas" in components and components["schemas"]:
            filtered_schemas: Dict[str, Any] = {}
            schemas = components["schemas"]

            # First pass: collect directly used schemas
            for schema_name in used_schemas:
                if schema_name in schemas:
                    filtered_schemas[schema_name] = schemas[schema_name]

            # Second pass: recursively collect nested schema references
            _collect_nested_schemas(
                filtered_schemas, schemas, filtered_schemas.copy()
            )

            filtered_components = {
                **components,
                "schemas": filtered_schemas,
            }

    # Filter tags
    filtered_tags = None
    if "tags" in openapi_schema and openapi_schema["tags"]:
        filtered_tags = [
            t for t in openapi_schema["tags"] if isinstance(t, dict) and t.get("name") == tag
        ]

    # Build filtered document
    filtered_document = {
        **openapi_schema,
        "paths": filtered_paths,
    }

    if filtered_components:
        filtered_document["components"] = filtered_components

    if filtered_tags:
        filtered_document["tags"] = filtered_tags

    return filtered_document


def _collect_schema_refs(obj: Any, schema_refs: Set[str]) -> None:
    """Recursively collect schema references from an object."""
    if isinstance(obj, dict):
        if "$ref" in obj and isinstance(obj["$ref"], str):
            ref = obj["$ref"]
            if ref.startswith("#/components/schemas/"):
                schema_name = ref.replace("#/components/schemas/", "")
                schema_refs.add(schema_name)
        for value in obj.values():
            _collect_schema_refs(value, schema_refs)
    elif isinstance(obj, list):
        for item in obj:
            _collect_schema_refs(item, schema_refs)


def _collect_nested_schemas(
    target_schemas: Dict[str, Any],
    all_schemas: Dict[str, Any],
    processed: Set[str],
) -> None:
    """Recursively collect nested schema references."""
    for schema_name, schema in list(target_schemas.items()):
        if schema_name in processed:
            continue
        processed.add(schema_name)

        _collect_schema_refs_from_schema(schema, target_schemas, all_schemas, processed)


def _collect_schema_refs_from_schema(
    schema: Any,
    target_schemas: Dict[str, Any],
    all_schemas: Dict[str, Any],
    processed: Set[str],
) -> None:
    """Collect schema references from a schema object."""
    if isinstance(schema, dict):
        if "$ref" in schema:
            ref = schema["$ref"]
            if ref.startswith("#/components/schemas/"):
                nested_schema_name = ref.replace("#/components/schemas/", "")
                if (
                    nested_schema_name not in target_schemas
                    and nested_schema_name in all_schemas
                ):
                    target_schemas[nested_schema_name] = all_schemas[nested_schema_name]
                    processed.add(nested_schema_name)
                    _collect_schema_refs_from_schema(
                        all_schemas[nested_schema_name],
                        target_schemas,
                        all_schemas,
                        processed,
                    )

        # Check properties, items, allOf, anyOf, oneOf
        for key in ["properties", "items", "allOf", "anyOf", "oneOf"]:
            if key in schema:
                if isinstance(schema[key], dict):
                    _collect_schema_refs_from_schema(
                        schema[key], target_schemas, all_schemas, processed
                    )
                elif isinstance(schema[key], list):
                    for item in schema[key]:
                        _collect_schema_refs_from_schema(
                            item, target_schemas, all_schemas, processed
                        )

        # Recursively process all values
        for value in schema.values():
            _collect_schema_refs_from_schema(
                value, target_schemas, all_schemas, processed
            )


def get_custom_swagger_html(app, swagger_path: str = "/docs") -> str:
    """Generate custom Swagger UI HTML with custom CSS and JavaScript."""
    from fastapi.openapi.docs import get_swagger_ui_html

    # Get app attributes with defaults
    openapi_url = getattr(app, "openapi_url", "/openapi.json")
    app_title = getattr(app, "title", "API") + " - Swagger UI"

    # Get the default Swagger UI HTML (returns HTMLResponse)
    html_response = get_swagger_ui_html(
        openapi_url=openapi_url,
        title=app_title,
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
    )
    
    # Extract HTML content from the response
    # HTMLResponse.body is bytes, so we need to decode it
    html = html_response.body.decode("utf-8")

    # Inject custom CSS
    custom_css = """
    <style>
      .swagger-ui .info .title {
        margin-bottom: 20px;
      }
      .controller-links {
        background: #f7f7f7;
        border: 1px solid #d4edda;
        border-radius: 5px;
        padding: 15px;
        margin: 20px 0;
      }
      .controller-links h4 {
        color: #155724;
        margin-bottom: 10px;
        font-size: 16px;
      }
      .controller-link {
        display: inline-block;
        margin: 5px 10px 5px 0;
        padding: 8px 12px;
        background: #609ddeff;
        color: white;
        text-decoration: none;
        border-radius: 4px;
        font-size: 14px;
        transition: background-color 0.2s;
      }
      .controller-link:hover {
        background: #598dc5ff;
        color: white !important;
        text-decoration: none;
      }
      .controller-link.hidden {
        display: none;
      }
      .tag-search-input {
        width: 100%;
        padding: 8px 12px;
        margin-bottom: 15px;
        border: 1px solid #ddd;
        border-radius: 4px;
        font-size: 14px;
        box-sizing: border-box;
      }
      .tag-search-input:focus {
        outline: none;
        border-color: #609ddeff;
        box-shadow: 0 0 0 2px rgba(96, 157, 222, 0.2);
      }
      .tag-links-container {
        display: flex;
        flex-wrap: wrap;
        gap: 5px;
      }
    </style>
    """

    # Inject custom JavaScript
    # Escape the swagger_path for use in JavaScript string
    escaped_path = swagger_path.replace("'", "\\'")
    custom_js = f"""
    <script>
      setTimeout(function() {{
        // Fetch available tags and add links
        fetch('{escaped_path}/tags')
          .then(response => response.json())
          .then(data => {{
            const tags = data.tags || [];
            if (tags.length > 0) {{
              const infoSection = document.querySelector('.swagger-ui .info');
              if (infoSection) {{
                const linksDiv = document.createElement('div');
                linksDiv.className = 'controller-links';
                
                // Create search input
                const searchInput = document.createElement('input');
                searchInput.type = 'text';
                searchInput.className = 'tag-search-input';
                searchInput.placeholder = 'Search tags...';
                searchInput.setAttribute('aria-label', 'Search tags');
                
                // Create container for tag links
                const tagLinksContainer = document.createElement('div');
                tagLinksContainer.className = 'tag-links-container';
                
                // Create all tag links
                const tagLinks = tags.map(tag => {{
                  const link = document.createElement('a');
                  link.href = '{escaped_path}/json/' + encodeURIComponent(tag);
                  link.className = 'controller-link';
                  link.target = '_blank';
                  link.title = 'Download OpenAPI JSON for ' + tag;
                  link.textContent = tag;
                  link.setAttribute('data-tag', tag.toLowerCase());
                  return link;
                }});
                
                // Add links to container
                tagLinks.forEach(link => tagLinksContainer.appendChild(link));
                
                // Filter function
                function filterTags(searchTerm) {{
                  const term = searchTerm.toLowerCase().trim();
                  tagLinks.forEach(link => {{
                    const tagName = link.getAttribute('data-tag');
                    if (term === '' || tagName.includes(term)) {{
                      link.classList.remove('hidden');
                    }} else {{
                      link.classList.add('hidden');
                    }}
                  }});
                }}
                
                // Add search input event listener
                searchInput.addEventListener('input', function(e) {{
                  filterTags(e.target.value);
                }});
                
                // Build the HTML structure
                linksDiv.innerHTML = 
                  '<h4>📋 Download Complete OpenAPI JSON:</h4>' +
                  '<a href="{escaped_path}/json" class="controller-link" target="_blank" title="Download Complete OpenAPI JSON">Complete OpenAPI JSON</a>' +
                  '<h4>📋 Download Tag-Specific OpenAPI JSON:</h4>';
                
                // Append search input
                linksDiv.appendChild(searchInput);
                
                // Append tag links container
                linksDiv.appendChild(tagLinksContainer);
                
                infoSection.appendChild(linksDiv);
              }}
            }}
          }})
          .catch(console.error);
      }}, 1000);
    </script>
    """

    # Insert custom CSS before closing head tag
    html = html.replace("</head>", custom_css + "</head>")

    # Insert custom JavaScript before closing body tag
    html = html.replace("</body>", custom_js + "</body>")

    return html


def _get_openapi_schema(app):
    """Get or generate the OpenAPI schema."""
    if app.openapi_schema:
        return app.openapi_schema
    # Generate the schema if it doesn't exist yet
    return get_openapi(
        title=getattr(app, "title", "API"),
        version=getattr(app, "version", "1.0.0"),
        description=getattr(app, "description", ""),
        routes=app.routes,
    )


def setup_swagger_splitter(app, swagger_path: str = "/docs") -> None:
    """
    Set up custom Swagger endpoints and override the default docs route.
    
    Args:
        app: FastAPI application instance
        swagger_path: Path where Swagger UI will be available (default: "/docs")
    
    Example:
        ```python
        from fastapi import FastAPI
        from fastapi_swagger_splitter import setup_swagger_splitter
        
        app = FastAPI(docs_url=None)  # Disable default docs
        setup_swagger_splitter(app, swagger_path="/docs")
        ```
    """
    # Ensure swagger_path doesn't have trailing slash for consistency
    swagger_path = swagger_path.rstrip("/")

    logger.info(f"Setting up custom Swagger UI at {swagger_path}")

    # Override the default /docs endpoint with custom HTML
    @app.get(swagger_path, include_in_schema=False)
    async def custom_swagger_ui_html(request: Request):
        try:
            html_content = get_custom_swagger_html(app, swagger_path)
            return HTMLResponse(content=html_content)
        except Exception as e:
            logger.error(f"Error generating custom Swagger HTML: {e}", exc_info=True)
            raise

    # Endpoint to get complete OpenAPI JSON
    @app.get(f"{swagger_path}/json", include_in_schema=False)
    async def get_complete_openapi_json():
        try:
            openapi_schema = _get_openapi_schema(app)
            return JSONResponse(content=openapi_schema)
        except Exception as e:
            logger.error(f"Error getting complete OpenAPI JSON: {e}", exc_info=True)
            return JSONResponse(
                content={"error": "Failed to generate OpenAPI schema"},
                status_code=500,
            )

    # Endpoint to get tag-specific OpenAPI JSON
    @app.get(f"{swagger_path}/json/{{tag}}", include_in_schema=False)
    async def get_tag_openapi_json(tag: str):
        try:
            openapi_schema = _get_openapi_schema(app)
            filtered_schema = filter_openapi_by_tag(openapi_schema, tag)
            return JSONResponse(content=filtered_schema)
        except Exception as e:
            logger.error(f"Error filtering OpenAPI by tag {tag}: {e}", exc_info=True)
            return JSONResponse(
                content={"error": f"Failed to filter schema for tag: {tag}"},
                status_code=500,
            )

    # Endpoint to list all available tags
    @app.get(f"{swagger_path}/tags", include_in_schema=False)
    async def get_all_tags_endpoint():
        try:
            openapi_schema = _get_openapi_schema(app)
            tags = get_all_tags(openapi_schema)
            return JSONResponse(content={"tags": tags})
        except Exception as e:
            logger.error(f"Error getting tags: {e}", exc_info=True)
            return JSONResponse(
                content={"error": "Failed to get tags", "tags": []},
                status_code=500,
            )

    logger.info(f"Custom Swagger UI setup complete. Available at {swagger_path}")
