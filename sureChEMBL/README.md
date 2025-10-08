# SureChEMBL MCP Server

A Model Context Protocol (MCP) server for accessing SureChEMBL patent chemistry database. SureChEMBL provides access to chemical structures extracted from patent documents.

## Features

### Document & Patent Search (4 tools)
- `search_patents`: Search patents by text, keywords, or identifiers
- `get_document_content`: Get complete patent document content with chemical annotations
- `get_patent_family`: Get patent family members and relationships
- `search_by_patent_number`: Search for patents by specific patent numbers

### Chemical Search & Retrieval (4 tools)
- `search_chemicals_by_name`: Search for chemicals by name, synonym, or common name
- `get_chemical_by_id`: Get detailed chemical information by SureChEMBL ID
- `search_by_smiles`: Search for chemicals by SMILES structure notation
- `search_by_inchi`: Search for chemicals by InChI or InChI key

### Structure & Visualization (2 tools)
- `get_chemical_image`: Generate chemical structure images
- `get_chemical_properties`: Get molecular properties and descriptors

### Data Export & Analysis (2 tools)
- `export_chemicals`: Bulk export chemical data in CSV or XML format
- `analyze_patent_chemistry`: Analyze chemical content and annotations in patents

### Advanced Analysis Tools (3 tools)
- `get_chemical_frequency`: Get frequency statistics for chemicals across the patent database
- `search_similar_structures`: Find structurally similar chemicals
- `get_patent_statistics`: Get statistical overview of chemical content in patents

## Installation

### Using Docker (Recommended)

1. Build and run the container:
```bash
cd sureChEMBL
docker-compose up -d
```

2. Check the service is running:
```bash
curl http://localhost:8004/health
```

### Manual Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the server:
```bash
# For stdio mode (Cursor/Claude integration)
python surechembl_server.py

# For HTTP/SSE mode
python surechembl_server.py --transport
```

## Usage Examples

### Searching for Chemicals by Name
```python
# Search for aspirin
results = await search_chemicals_by_name(name="aspirin", limit=10)
```

### Getting Patent Document Content
```python
# Get document with chemical annotations
document = await get_document_content(document_id="WO-2020096695-A1")
```

### Analyzing Patent Chemistry
```python
# Analyze chemical content in a patent
analysis = await analyze_patent_chemistry(document_id="WO-2020096695-A1")
```

### Getting Chemical Properties
```python
# Get detailed properties for a chemical
properties = await get_chemical_properties(chemical_id="12345")
```

### Exporting Chemical Data
```python
# Bulk export chemicals
export = await export_chemicals(
    chemical_ids=["12345", "67890"],
    output_type="csv"
)
```

## API Endpoints

When running in HTTP mode, the server exposes:
- Health check: `GET /health`
- MCP tools: Available via SSE connection

## Configuration

The server uses the following default configuration:
- **Base URL**: https://www.surechembl.org/api
- **Port**: 8000 (mapped to 8004 externally in docker-compose)
- **Timeout**: 30 seconds

## Notes

- SureChEMBL has some API limitations:
  - Direct SMILES and InChI searches are not available
  - Similarity search is not directly supported
  - Some features return helpful guidance on alternative approaches
  
- Chemical image generation requires valid structure notation
- Patent document IDs should follow the format: `COUNTRY-NUMBER-KIND` (e.g., `WO-2020096695-A1`)

## Health Check

The server includes a health check endpoint at `/health`:
```bash
curl http://localhost:8004/health
```

Response:
```json
{
  "status": "healthy",
  "service": "surechembl-mcp-server"
}
```

## Integration with Cursor/Claude

Add to your MCP configuration:
```json
{
  "mcpServers": {
    "surechembl": {
      "command": "python",
      "args": ["/path/to/surechembl_server.py"]
    }
  }
}
```

## Docker Commands

```bash
# Build the image
docker-compose build

# Start the service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down

# Restart the service
docker-compose restart
```

## Troubleshooting

1. **Connection timeout**: Increase the timeout in the API request configuration
2. **Invalid document ID**: Ensure the document ID follows the correct format
3. **Chemical not found**: Verify the chemical ID or try searching by name first
4. **Port conflict**: Change the external port in docker-compose.yml

## Resources

- SureChEMBL Website: https://www.surechembl.org
- SureChEMBL API Documentation: https://www.surechembl.org/search/help
- MCP Documentation: https://modelcontextprotocol.io

## License

This MCP server is provided as-is for accessing the SureChEMBL public API. Please refer to SureChEMBL's terms of service for API usage guidelines.

