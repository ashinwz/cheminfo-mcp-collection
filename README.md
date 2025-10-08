# ChemInfo MCP Servers

A collection of Model Context Protocol (MCP) servers for chemical and biological data access, including PubChem, OpenTargets, DrugBank, ChEMBL, and SureChEMBL integrations.

## 🚀 Services

### 1. **PubChem MCP Server** (Port 8000)
- Search compounds by name, SMILES, formula, or CID
- Retrieve detailed chemical compound information
- Access molecular properties and structures

### 2. **OpenTargets MCP Server** (Port 8001)
- Search gene targets and diseases
- Get target-disease associations
- Explore drug candidates and mechanisms

### 3. **DrugBank MCP Server** (Port 8002)
- Search drugs by name, category, or indication
- Get detailed drug information
- Query drug interactions

### 4. **ChEMBL MCP Server** (Port 8003)
- Search molecules, targets, and bioactivity data
- Access drug discovery and medicinal chemistry information
- Query biological activity assays

### 5. **SureChEMBL MCP Server** (Port 8004)
- Search patent chemistry database
- Extract chemical structures from patents
- Analyze patent chemical content and annotations

### 6. **PDB MCP Server** (Port 8005)
- Search Protein Data Bank structures by keyword or protein name
- Get detailed structure information and coordinates
- Download structures in various formats (PDB, mmCIF, MMTF, XML)
- Search by UniProt accession or protein sequence
- Access structure quality metrics and validation data
- Get ligand and binding site information

## 📋 Prerequisites

- Docker and Docker Compose installed
- Python 3.11+ (for local development)
- DrugBank API key (for DrugBank server)

## 🐳 Docker Deployment

### Option 1: Run All Services Together

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### Option 2: Run Individual Services

```bash
# PubChem only
cd PubChem
docker-compose up -d

# OpenTargets only
cd OpenTarget
docker-compose up -d

# DrugBank only (requires API key)
cd Drugbank
export DRUGBANK_API_KEY="your-api-key-here"
docker-compose up -d

# ChEMBL only
cd ChEMBL
docker-compose up -d

# SureChEMBL only
cd sureChEMBL
docker-compose up -d

# PDB only
cd PDB
docker-compose up -d
```

## 🔧 Local Development

### PubChem Server

```bash
cd PubChem
pip install -r requirements.txt

# Run in stdio mode (for Cursor/Claude)
python pubchem_server.py

# Run in HTTP mode
python pubchem_server.py --transport
```

### OpenTargets Server

```bash
cd OpenTarget
pip install -r requirements.txt

# Run in stdio mode (for Cursor/Claude)
python opentarget_server.py

# Run in HTTP mode
python opentarget_server.py --transport
```

### DrugBank Server

```bash
cd Drugbank
pip install -r requirements.txt

# Edit drugbank_server.py and add your API key
# API_KEY = "your-api-key-here"

# Run in stdio mode (for Cursor/Claude)
python drugbank_server.py

# Run in HTTP mode
python drugbank_server.py --transport
```

### ChEMBL Server

```bash
cd ChEMBL
pip install -r requirements.txt

# Run in stdio mode (for Cursor/Claude)
python chembl_server.py

# Run in HTTP mode
python chembl_server.py --transport
```

### SureChEMBL Server

```bash
cd sureChEMBL
pip install -r requirements.txt

# Run in stdio mode (for Cursor/Claude)
python surechembl_server.py

# Run in HTTP mode
python surechembl_server.py --transport
```

### PDB Server

```bash
cd PDB
pip install -r requirements.txt

# Run in stdio mode (for Cursor/Claude)
python pdb_server.py

# Run in HTTP mode
python pdb_server.py --transport
```

## 🌐 API Endpoints

Once running in HTTP mode, all servers expose the following endpoints:

- **Health Check**: `GET http://localhost:<port>/health`
- **MCP Tools**: Available via MCP protocol on the SSE endpoint

### Port Mapping

| Service | HTTP Port | Docker Internal Port |
|---------|-----------|---------------------|
| PubChem | 8000 | 8000 |
| OpenTargets | 8001 | 8000 |
| DrugBank | 8002 | 8000 |
| ChEMBL | 8003 | 8000 |
| SureChEMBL | 8004 | 8000 |
| PDB | 8005 | 8000 |

## 🔑 Environment Variables

### DrugBank Server

Create a `.env` file in the root directory:

```env
DRUGBANK_API_KEY=your-drugbank-api-key-here
```

## 🧪 Testing

Test health endpoints:

```bash
# PubChem
curl http://localhost:8000/health

# OpenTargets
curl http://localhost:8001/health

# DrugBank
curl http://localhost:8002/health

# ChEMBL
curl http://localhost:8003/health

# SureChEMBL
curl http://localhost:8004/health

# PDB
curl http://localhost:8005/health
```

## 📚 Available Tools

### PubChem Tools
- `search_pubchem_by_name` - Search compounds by name
- `search_pubchem_by_smiles` - Search compounds by SMILES
- `get_pubchem_compound_by_cid` - Get compound by CID
- `search_pubchem_advanced` - Advanced search with multiple parameters

### OpenTargets Tools
- `search_targets` - Search gene targets
- `get_target_details` - Get detailed target information
- `search_diseases` - Search diseases
- `get_target_associated_diseases` - Get diseases for a target
- `get_disease_associated_targets` - Get targets for a disease
- `search_drugs` - Search drugs in OpenTargets

### DrugBank Tools
- `search_drugs` - Search drugs by name
- `get_drug_details` - Get detailed drug information
- `find_drugs_by_indication` - Find drugs for a medical condition
- `find_drugs_by_category` - Find drugs in a category
- `get_drug_interactions` - Get drug interaction information

### ChEMBL Tools
- `search_molecule_by_name` - Search molecules by name
- `search_molecule_by_similarity` - Find similar molecules
- `search_molecule_by_substructure` - Search by substructure
- `search_approved_drugs` - Find approved drugs
- `search_target_by_gene_name` - Search targets by gene name
- `search_activities_by_target` - Get bioactivity data for targets
- And many more molecular and target search tools

### SureChEMBL Tools
- `search_patents` - Search patents by text or keywords
- `get_document_content` - Get patent document with chemical annotations
- `search_chemicals_by_name` - Search chemicals by name
- `get_chemical_by_id` - Get chemical details by ID
- `get_chemical_image` - Generate chemical structure images
- `export_chemicals` - Bulk export chemical data
- `analyze_patent_chemistry` - Analyze chemical content in patents
- `get_patent_statistics` - Get patent chemical statistics

### PDB Tools
- `search_pdb_structures` - Search PDB structures by keyword or protein name
- `get_pdb_structure_info` - Get detailed structure information
- `download_pdb_structure` - Download structure coordinates in various formats
- `search_pdb_by_uniprot` - Find structures by UniProt accession
- `get_pdb_structure_quality` - Get quality metrics and validation data
- `get_pdb_ligands` - Get ligand and binding site information
- `search_pdb_by_sequence` - Search structures by protein sequence similarity

## 🛠️ Technology Stack

- **FastMCP**: Model Context Protocol server framework
- **httpx**: Async HTTP client
- **uvicorn**: ASGI server
- **Docker**: Containerization
- **Python 3.11**: Runtime

## 📝 License

Please ensure compliance with the respective API terms of service:
- [PubChem Terms](https://pubchem.ncbi.nlm.nih.gov/)
- [OpenTargets Terms](https://platform.opentargets.org/)
- [DrugBank Terms](https://www.drugbank.com/)
- [ChEMBL Terms](https://www.ebi.ac.uk/chembl/)
- [SureChEMBL Terms](https://www.surechembl.org/)
- [PDB Terms](https://www.rcsb.org/)

## 🤝 Contributing

Contributions are welcome! Please follow the existing code patterns and ensure all servers follow the same structure.

## 📧 Support

For issues and questions, please check the individual server logs or health endpoints for debugging information.

