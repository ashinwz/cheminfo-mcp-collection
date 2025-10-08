# PDB MCP Server

A Model Context Protocol (MCP) server for accessing Protein Data Bank (PDB) structures and data.

## Features

- **Structure Search**: Search PDB database by keywords, protein names, or PDB IDs
- **Structure Information**: Get detailed information about specific PDB structures
- **Structure Downloads**: Download structure coordinates in various formats (PDB, mmCIF, MMTF, XML)
- **UniProt Integration**: Find PDB structures associated with UniProt accessions
- **Quality Metrics**: Access structure quality and validation data
- **Ligand Information**: Get ligand and binding site information
- **Sequence Search**: Search structures by protein sequence similarity

## Installation

### Local Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run in stdio mode (for Cursor/Claude)
python pdb_server.py

# Run in HTTP/SSE mode
python pdb_server.py --transport
```

### Docker Installation

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the server
docker-compose down
```

## Available Tools

### 1. search_pdb_structures
Search PDB database for protein structures by keyword, protein name, or PDB ID.

**Parameters:**
- `query` (string, required): Search query (protein name, keyword, PDB ID, etc.)
- `limit` (integer, optional): Number of results to return (1-1000, default: 25)
- `sort_by` (string, optional): Sort results by (release_date, resolution, score, etc., default: score)
- `experimental_method` (string, optional): Filter by experimental method (X-RAY DIFFRACTION, SOLUTION NMR, ELECTRON MICROSCOPY)
- `resolution_range` (string, optional): Resolution range filter (e.g., "1.0-2.0")

**Example:**
```python
result = await search_pdb_structures(
    query="hemoglobin",
    limit=10,
    experimental_method="X-RAY DIFFRACTION",
    resolution_range="1.0-2.0"
)
```

### 2. get_pdb_structure_info
Get detailed information for a specific PDB structure.

**Parameters:**
- `pdb_id` (string, required): PDB ID (4-character code, e.g., 1ABC)
- `format` (string, optional): Output format (json, pdb, mmcif, xml, default: json)

**Example:**
```python
result = await get_pdb_structure_info(pdb_id="1ABC", format="json")
```

### 3. download_pdb_structure
Download structure coordinates in various formats.

**Parameters:**
- `pdb_id` (string, required): PDB ID (4-character code)
- `format` (string, optional): File format (pdb, mmcif, mmtf, xml, default: pdb)
- `assembly_id` (string, optional): Biological assembly ID (optional)

**Example:**
```python
result = await download_pdb_structure(
    pdb_id="1ABC",
    format="pdb",
    assembly_id="1"
)
```

### 4. search_pdb_by_uniprot
Find PDB structures associated with a UniProt accession.

**Parameters:**
- `uniprot_id` (string, required): UniProt accession number
- `limit` (integer, optional): Number of results to return (1-1000, default: 25)

**Example:**
```python
result = await search_pdb_by_uniprot(uniprot_id="P69905", limit=10)
```

### 5. get_pdb_structure_quality
Get structure quality metrics and validation data.

**Parameters:**
- `pdb_id` (string, required): PDB ID (4-character code)

**Example:**
```python
result = await get_pdb_structure_quality(pdb_id="1ABC")
```

### 6. get_pdb_ligands
Get ligand and binding site information for a structure.

**Parameters:**
- `pdb_id` (string, required): PDB ID (4-character code)

**Example:**
```python
result = await get_pdb_ligands(pdb_id="1ABC")
```

### 7. search_pdb_by_sequence
Search PDB structures by protein sequence similarity.

**Parameters:**
- `sequence` (string, required): Protein sequence (FASTA format or plain amino acid sequence)
- `limit` (integer, optional): Number of results to return (1-1000, default: 25)
- `identity_cutoff` (float, optional): Sequence identity cutoff (0.0-1.0, default: 0.9)

**Example:**
```python
result = await search_pdb_by_sequence(
    sequence="MVHLTPEEKSAVTALWGKVNVDEVGGEALGRLLVVYPWTQRFFESFGDLSTPDAVMGNPKVKAHGKKVLGAFSDGLAHLDNLKGTFATLSELHCDKLHVDPENFRLLGNVLVCVLAHHFGKEFTPPVQAAYQKVVAGVANALAHKYH",
    limit=10,
    identity_cutoff=0.95
)
```

## Configuration

The server runs on port 8003 by default when using Docker Compose. You can modify this in the `docker-compose.yml` file.

## API Endpoints

When running in HTTP/SSE mode:
- Base URL: `http://localhost:8003`
- Health Check: `http://localhost:8003/health`

## Data Sources

This server uses the following RCSB PDB APIs:
- **Search API**: https://search.rcsb.org/rcsbsearch/v2
- **Data API**: https://data.rcsb.org/rest/v1
- **Files API**: https://files.rcsb.org/download

## License

This project is open source and available under the MIT License.

## Support

For issues or questions, please refer to the RCSB PDB documentation:
- https://www.rcsb.org/
- https://search.rcsb.org/index.html
- https://data.rcsb.org/


