from typing import Any, List, Dict, Optional
import asyncio
import logging
import requests
from starlette.responses import JSONResponse
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize FastMCP server
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("pdb")

# Add health check endpoint
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    """Health check endpoint for Docker healthcheck."""
    return JSONResponse({"status": "healthy", "service": "pdb-mcp-server"})

# PDB API base URLs
PDB_DATA_API = "https://data.rcsb.org/rest/v1"
PDB_SEARCH_API = "https://search.rcsb.org/rcsbsearch/v2"
PDB_FILES_BASE = "https://files.rcsb.org/download"

def validate_pdb_id(pdb_id: str) -> bool:
    """Validate PDB ID format (4 characters: digit followed by 3 alphanumeric)."""
    return bool(re.match(r'^[0-9][a-zA-Z0-9]{3}$', pdb_id, re.IGNORECASE))

def get_structure_info(pdb_id: str, format: str = 'json') -> Dict[str, Any]:
    """Get detailed information for a specific PDB structure."""
    pdb_id = pdb_id.lower()
    
    if not validate_pdb_id(pdb_id):
        return {"error": f"Invalid PDB ID format: {pdb_id}. Must be 4 characters (digit + 3 alphanumeric)."}
    
    try:
        if format == 'json':
            response = requests.get(f"{PDB_DATA_API}/core/entry/{pdb_id}", timeout=30)
            response.raise_for_status()
            return response.json()
        else:
            # Handle file format downloads
            extension = 'cif' if format == 'mmcif' else format
            url = f"{PDB_FILES_BASE}/{pdb_id}.{extension}"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return {"pdb_id": pdb_id, "format": format, "data": response.text}
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching structure info for {pdb_id}: {str(e)}")
        return {"error": f"Failed to fetch structure info: {str(e)}"}

def search_structures(
    query: str,
    limit: int = 25,
    sort_by: str = "score",
    experimental_method: Optional[str] = None,
    resolution_range: Optional[str] = None
) -> Dict[str, Any]:
    """Search PDB database for protein structures."""
    try:
        search_query = {
            "query": {
                "type": "terminal",
                "service": "full_text",
                "parameters": {
                    "value": query
                }
            },
            "return_type": "entry",
            "request_options": {
                "paginate": {
                    "start": 0,
                    "rows": min(limit, 1000)
                },
                "results_content_type": ["experimental"],
                "sort": [
                    {
                        "sort_by": sort_by,
                        "direction": "desc"
                    }
                ]
            }
        }

        # Add filters if provided
        filters = []
        if experimental_method:
            filters.append({
                "type": "terminal",
                "service": "text",
                "parameters": {
                    "attribute": "exptl.method",
                    "operator": "exact_match",
                    "value": experimental_method
                }
            })

        if resolution_range:
            parts = resolution_range.split('-')
            if len(parts) == 2:
                try:
                    min_res, max_res = float(parts[0]), float(parts[1])
                    filters.append({
                        "type": "terminal",
                        "service": "text",
                        "parameters": {
                            "attribute": "rcsb_entry_info.resolution_combined",
                            "operator": "range",
                            "value": {
                                "from": min_res,
                                "to": max_res,
                                "include_lower": True,
                                "include_upper": True
                            }
                        }
                    })
                except ValueError:
                    logging.warning(f"Invalid resolution range format: {resolution_range}")

        if filters:
            search_query["query"] = {
                "type": "group",
                "logical_operator": "and",
                "nodes": [search_query["query"]] + filters
            }

        response = requests.post(f"{PDB_SEARCH_API}/query", json=search_query, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error searching structures: {str(e)}")
        return {"error": f"Failed to search structures: {str(e)}"}

def download_structure(
    pdb_id: str,
    format: str = 'pdb',
    assembly_id: Optional[str] = None
) -> Dict[str, Any]:
    """Download structure coordinates in various formats."""
    pdb_id = pdb_id.lower()
    
    if not validate_pdb_id(pdb_id):
        return {"error": f"Invalid PDB ID format: {pdb_id}"}
    
    try:
        extension = 'cif' if format == 'mmcif' else format
        if assembly_id:
            url = f"{PDB_FILES_BASE}/{pdb_id}-assembly{assembly_id}.{extension}"
        else:
            url = f"{PDB_FILES_BASE}/{pdb_id}.{extension}"
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        return {
            "pdb_id": pdb_id,
            "format": format.upper(),
            "assembly_id": assembly_id,
            "data": response.text
        }
    except requests.exceptions.RequestException as e:
        logging.error(f"Error downloading structure {pdb_id}: {str(e)}")
        return {"error": f"Failed to download structure: {str(e)}"}

def search_by_uniprot(uniprot_id: str, limit: int = 25) -> Dict[str, Any]:
    """Find PDB structures associated with a UniProt accession."""
    try:
        search_query = {
            "query": {
                "type": "terminal",
                "service": "text",
                "parameters": {
                    "attribute": "rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers.database_accession",
                    "operator": "exact_match",
                    "value": uniprot_id
                }
            },
            "return_type": "entry",
            "request_options": {
                "paginate": {
                    "start": 0,
                    "rows": min(limit, 1000)
                },
                "results_content_type": ["experimental"]
            }
        }

        response = requests.post(f"{PDB_SEARCH_API}/query", json=search_query, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error searching by UniProt {uniprot_id}: {str(e)}")
        return {"error": f"Failed to search by UniProt: {str(e)}"}

def get_structure_quality(pdb_id: str) -> Dict[str, Any]:
    """Get structure quality metrics and validation data."""
    pdb_id = pdb_id.lower()
    
    if not validate_pdb_id(pdb_id):
        return {"error": f"Invalid PDB ID format: {pdb_id}"}
    
    try:
        # Get entry data
        entry_response = requests.get(f"{PDB_DATA_API}/core/entry/{pdb_id}", timeout=30)
        entry_response.raise_for_status()
        entry_data = entry_response.json()
        
        # Try to get validation data
        validation_url = f"{PDB_DATA_API}/validation/residual_summary/{pdb_id}"
        validation_response = requests.get(validation_url, timeout=30)
        
        quality_data = {
            "pdb_id": pdb_id,
            "resolution": entry_data.get("resolution"),
            "r_work": entry_data.get("r_work"),
            "r_free": entry_data.get("r_free"),
            "experimental_method": entry_data.get("experimental_method"),
            "validation_available": validation_response.status_code == 200
        }
        
        if validation_response.status_code == 200:
            validation_data = validation_response.json()
            quality_data["validation_data"] = validation_data
        
        return quality_data
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching structure quality for {pdb_id}: {str(e)}")
        return {"error": f"Failed to fetch structure quality: {str(e)}"}

def get_ligands(pdb_id: str) -> Dict[str, Any]:
    """Get ligand and binding site information for a structure."""
    pdb_id = pdb_id.lower()
    
    if not validate_pdb_id(pdb_id):
        return {"error": f"Invalid PDB ID format: {pdb_id}"}
    
    try:
        # Get non-polymer entities (ligands)
        response = requests.get(f"{PDB_DATA_API}/core/nonpolymer_entity/{pdb_id}", timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching ligands for {pdb_id}: {str(e)}")
        return {"error": f"Failed to fetch ligands: {str(e)}"}

def search_by_sequence(sequence: str, limit: int = 25, identity_cutoff: float = 0.9) -> Dict[str, Any]:
    """Search PDB structures by protein sequence similarity."""
    try:
        search_query = {
            "query": {
                "type": "terminal",
                "service": "sequence",
                "parameters": {
                    "evalue_cutoff": 0.1,
                    "identity_cutoff": identity_cutoff,
                    "target": "pdb_protein_sequence",
                    "value": sequence
                }
            },
            "return_type": "entry",
            "request_options": {
                "paginate": {
                    "start": 0,
                    "rows": min(limit, 1000)
                },
                "results_content_type": ["experimental"]
            }
        }

        response = requests.post(f"{PDB_SEARCH_API}/query", json=search_query, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error searching by sequence: {str(e)}")
        return {"error": f"Failed to search by sequence: {str(e)}"}

# MCP Tool Definitions

@mcp.tool()
async def search_pdb_structures(
    query: str,
    limit: int = 25,
    sort_by: str = "score",
    experimental_method: Optional[str] = None,
    resolution_range: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search PDB database for protein structures by keyword, protein name, or PDB ID.
    
    Args:
        query: Search query (protein name, keyword, PDB ID, etc.)
        limit: Number of results to return (1-1000, default: 25)
        sort_by: Sort results by (release_date, resolution, score, etc., default: score)
        experimental_method: Filter by experimental method (X-RAY DIFFRACTION, SOLUTION NMR, ELECTRON MICROSCOPY)
        resolution_range: Resolution range filter (e.g., "1.0-2.0")
    
    Returns:
        Dictionary containing search results with structure information
    """
    logging.info(f"Searching PDB structures with query: {query}")
    try:
        result = await asyncio.to_thread(
            search_structures,
            query,
            limit,
            sort_by,
            experimental_method,
            resolution_range
        )
        return result
    except Exception as e:
        return {"error": f"An error occurred while searching: {str(e)}"}

@mcp.tool()
async def get_pdb_structure_info(pdb_id: str, format: str = 'json') -> Dict[str, Any]:
    """
    Get detailed information for a specific PDB structure.
    
    Args:
        pdb_id: PDB ID (4-character code, e.g., 1ABC)
        format: Output format (json, pdb, mmcif, xml, default: json)
    
    Returns:
        Dictionary containing structure information
    """
    logging.info(f"Fetching structure info for PDB ID: {pdb_id}")
    try:
        result = await asyncio.to_thread(get_structure_info, pdb_id, format)
        return result
    except Exception as e:
        return {"error": f"An error occurred while fetching structure info: {str(e)}"}

@mcp.tool()
async def download_pdb_structure(
    pdb_id: str,
    format: str = 'pdb',
    assembly_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Download structure coordinates in various formats.
    
    Args:
        pdb_id: PDB ID (4-character code)
        format: File format (pdb, mmcif, mmtf, xml, default: pdb)
        assembly_id: Biological assembly ID (optional)
    
    Returns:
        Dictionary containing structure file data
    """
    logging.info(f"Downloading structure {pdb_id} in {format} format")
    try:
        result = await asyncio.to_thread(download_structure, pdb_id, format, assembly_id)
        return result
    except Exception as e:
        return {"error": f"An error occurred while downloading structure: {str(e)}"}

@mcp.tool()
async def search_pdb_by_uniprot(uniprot_id: str, limit: int = 25) -> Dict[str, Any]:
    """
    Find PDB structures associated with a UniProt accession.
    
    Args:
        uniprot_id: UniProt accession number
        limit: Number of results to return (1-1000, default: 25)
    
    Returns:
        Dictionary containing search results
    """
    logging.info(f"Searching PDB by UniProt ID: {uniprot_id}")
    try:
        result = await asyncio.to_thread(search_by_uniprot, uniprot_id, limit)
        return result
    except Exception as e:
        return {"error": f"An error occurred while searching by UniProt: {str(e)}"}

@mcp.tool()
async def get_pdb_structure_quality(pdb_id: str) -> Dict[str, Any]:
    """
    Get structure quality metrics and validation data.
    
    Args:
        pdb_id: PDB ID (4-character code)
    
    Returns:
        Dictionary containing quality metrics
    """
    logging.info(f"Fetching structure quality for PDB ID: {pdb_id}")
    try:
        result = await asyncio.to_thread(get_structure_quality, pdb_id)
        return result
    except Exception as e:
        return {"error": f"An error occurred while fetching structure quality: {str(e)}"}

@mcp.tool()
async def get_pdb_ligands(pdb_id: str) -> Dict[str, Any]:
    """
    Get ligand and binding site information for a structure.
    
    Args:
        pdb_id: PDB ID (4-character code)
    
    Returns:
        Dictionary containing ligand information
    """
    logging.info(f"Fetching ligands for PDB ID: {pdb_id}")
    try:
        result = await asyncio.to_thread(get_ligands, pdb_id)
        return result
    except Exception as e:
        return {"error": f"An error occurred while fetching ligands: {str(e)}"}

@mcp.tool()
async def search_pdb_by_sequence(
    sequence: str,
    limit: int = 25,
    identity_cutoff: float = 0.9
) -> Dict[str, Any]:
    """
    Search PDB structures by protein sequence similarity.
    
    Args:
        sequence: Protein sequence (FASTA format or plain amino acid sequence)
        limit: Number of results to return (1-1000, default: 25)
        identity_cutoff: Sequence identity cutoff (0.0-1.0, default: 0.9)
    
    Returns:
        Dictionary containing search results
    """
    logging.info(f"Searching PDB by sequence (length: {len(sequence)})")
    try:
        result = await asyncio.to_thread(search_by_sequence, sequence, limit, identity_cutoff)
        return result
    except Exception as e:
        return {"error": f"An error occurred while searching by sequence: {str(e)}"}

if __name__ == "__main__":
    import sys
    
    # Check if --transport flag is provided
    if "--transport" in sys.argv:
        # Run in HTTP/SSE server mode
        # Use uvicorn directly with the SSE app to bind to 0.0.0.0 for external access
        import uvicorn
        
        # Get the SSE app from FastMCP and run with custom host/port
        app = mcp.sse_app
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        # Default: stdio mode (for Cursor/Claude)
        mcp.run()


