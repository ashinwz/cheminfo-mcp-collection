# SureChEMBL MCP Server - Quick Start Guide

## Quick Test (5 minutes)

### 1. Start the Service

```bash
# From the sureChEMBL directory
cd /Users/ashinwz/Desktop/cheminfo-mcp/sureChEMBL
docker-compose up -d
```

### 2. Verify Health

```bash
# Wait a few seconds for the service to start, then:
curl http://localhost:8004/health
```

Expected output:
```json
{"status": "healthy", "service": "surechembl-mcp-server"}
```

### 3. Test with Example Script

```bash
# Install dependencies (if not already installed)
pip install requests mcp uvicorn sse-starlette

# Run the example usage script
python example_usage.py
```

### 4. View Logs

```bash
# View live logs
docker-compose logs -f

# View recent logs
docker-compose logs --tail=50
```

## Testing Individual Tools

### Test 1: Search Chemicals by Name

```python
import asyncio
from surechembl_server import search_chemicals_by_name

async def test():
    result = await search_chemicals_by_name(name="aspirin", limit=5)
    print(result)

asyncio.run(test())
```

### Test 2: Get Patent Document

```python
import asyncio
from surechembl_server import get_document_content

async def test():
    result = await get_document_content(document_id="WO-2020096695-A1")
    print(result)

asyncio.run(test())
```

### Test 3: Analyze Patent Chemistry

```python
import asyncio
from surechembl_server import analyze_patent_chemistry

async def test():
    result = await analyze_patent_chemistry(document_id="WO-2020096695-A1")
    print(f"Total annotations: {result.get('total_chemical_annotations', 0)}")
    print(f"Unique chemicals: {len(result.get('unique_chemicals', []))}")

asyncio.run(test())
```

## Running All Services Together

To run all ChemInfo MCP services (including SureChEMBL):

```bash
# From the root directory
cd /Users/ashinwz/Desktop/cheminfo-mcp
docker-compose up -d

# Check all services
curl http://localhost:8000/health  # PubChem
curl http://localhost:8001/health  # OpenTargets
curl http://localhost:8002/health  # DrugBank
curl http://localhost:8003/health  # ChEMBL
curl http://localhost:8004/health  # SureChEMBL
```

## Stopping the Service

```bash
# Stop SureChEMBL only
cd sureChEMBL
docker-compose down

# Or stop all services
cd ..
docker-compose down
```

## Troubleshooting

### Service Won't Start
1. Check if port 8004 is already in use:
   ```bash
   lsof -i :8004
   ```
2. Check Docker logs:
   ```bash
   docker-compose logs surechembl-mcp
   ```

### API Errors
1. Verify internet connectivity to https://www.surechembl.org
2. Check if the SureChEMBL API is accessible:
   ```bash
   curl https://www.surechembl.org/api/chemical/name/aspirin
   ```

### Import Errors
1. Ensure all dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```

## Integration with Cursor/Claude

To use with Cursor or Claude Desktop, add to your MCP configuration file:

**macOS/Linux**: `~/.config/cursor/mcp.json`

```json
{
  "mcpServers": {
    "surechembl": {
      "command": "python",
      "args": ["/Users/ashinwz/Desktop/cheminfo-mcp/sureChEMBL/surechembl_server.py"]
    }
  }
}
```

Then restart Cursor to load the new MCP server.

## Available Tools Summary

| Tool | Description |
|------|-------------|
| `search_patents` | Search patents by keywords |
| `get_document_content` | Get full patent document |
| `get_patent_family` | Get patent family members |
| `search_by_patent_number` | Search by patent number |
| `search_chemicals_by_name` | Search chemicals by name |
| `get_chemical_by_id` | Get chemical details |
| `search_by_smiles` | Search by SMILES (limited) |
| `search_by_inchi` | Search by InChI (limited) |
| `get_chemical_image` | Generate structure images |
| `get_chemical_properties` | Get molecular properties |
| `export_chemicals` | Bulk export chemical data |
| `analyze_patent_chemistry` | Analyze patent chemicals |
| `get_chemical_frequency` | Get frequency statistics |
| `search_similar_structures` | Find similar structures |
| `get_patent_statistics` | Get patent statistics |

## Next Steps

1. Read the full [README.md](README.md) for detailed documentation
2. Explore the [example_usage.py](example_usage.py) script
3. Check the SureChEMBL API documentation: https://www.surechembl.org/search/help

## Support

For issues specific to this MCP server, check:
- Docker logs: `docker-compose logs`
- Python errors in the server output
- API connectivity to SureChEMBL

For SureChEMBL API issues, visit: https://www.surechembl.org

