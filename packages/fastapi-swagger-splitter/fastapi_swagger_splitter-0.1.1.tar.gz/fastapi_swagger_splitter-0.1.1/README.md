# FastAPI Swagger Splitter

Enhanced Swagger UI for FastAPI applications with tag-based filtering, download links, and search functionality.

## Features

- 🎨 **Custom Styled UI** - Beautiful, modern Swagger UI with custom CSS
- 📥 **Download Links** - Download complete or tag-specific OpenAPI JSON schemas
- 🔍 **Tag Search** - Search and filter tags in real-time
- 🏷️ **Tag-based Filtering** - Generate OpenAPI schemas filtered by specific tags
- 🚀 **Easy Integration** - Simple setup with just one function call

## Installation

```bash
pip install fastapi-swagger-splitter
```

## Quick Start

```python
from fastapi import FastAPI
from fastapi_swagger_splitter import setup_swagger_splitter

# Create your FastAPI app
app = FastAPI(
    title="My API",
    description="API documentation",
    version="1.0.0",
    docs_url=None,  # Disable default docs - we'll use custom one
    openapi_url="/openapi.json",
)

# Setup custom Swagger UI
setup_swagger_splitter(app, swagger_path="/docs")

@app.get("/")
async def root():
    return {"message": "Hello World"}
```

That's it! Now visit `http://localhost:8000/docs` to see your enhanced Swagger UI.

## Features in Detail

### Download Complete OpenAPI JSON

Click the "Complete OpenAPI JSON" link to download the full OpenAPI schema for your API.

### Download Tag-Specific OpenAPI JSON

Each tag in your API gets its own download link. Click any tag name to download an OpenAPI JSON file containing only endpoints and schemas related to that tag.

### Search Tags

Use the search input to quickly find tags by name. The search is case-insensitive and filters tags in real-time as you type.

## API Endpoints

The package automatically creates these endpoints:

- `GET /docs` - Custom Swagger UI (or your custom path)
- `GET /docs/json` - Complete OpenAPI JSON schema
- `GET /docs/json/{tag}` - Tag-specific OpenAPI JSON schema
- `GET /docs/tags` - List of all available tags

## Customization

### Custom Swagger Path

You can customize the Swagger UI path:

```python
setup_swagger_splitter(app, swagger_path="/api-docs")
```

Now your Swagger UI will be available at `/api-docs` instead of `/docs`.

## Requirements

- Python 3.8+
- FastAPI 0.68.0+
- Starlette 0.14.0+

## Development

```bash
# Clone the repository
git clone https://github.com/yourusername/fastapi-swagger-splitter.git
cd fastapi-swagger-splitter

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Changelog

### 0.1.0 (2024-01-XX)
- Initial release
- Custom Swagger UI with download links
- Tag-based filtering
- Search functionality
# fastapi-swagger-splitter
