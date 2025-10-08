from typing import Any, List, Dict, Optional
import asyncio
import logging
import requests
from starlette.responses import JSONResponse
import base64

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize FastMCP server
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("surechembl")

# SureChEMBL API base URL
SURECHEMBL_API_BASE = "https://www.surechembl.org/api"
REQUEST_TIMEOUT = 30

# Add health check endpoint
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    """Health check endpoint for Docker healthcheck."""
    return JSONResponse({"status": "healthy", "service": "surechembl-mcp-server"})

def make_api_request(endpoint: str, params: Optional[Dict] = None, response_type: str = "json"):
    """Make a request to the SureChEMBL API."""
    url = f"{SURECHEMBL_API_BASE}/{endpoint}"
    headers = {
        'User-Agent': 'SureChEMBL-MCP-Server/1.0.0',
        'Accept': 'application/json',
    }
    
    try:
        if response_type == "binary":
            response = requests.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
        else:
            response = requests.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
        
        response.raise_for_status()
        
        if response_type == "binary":
            return response.content
        else:
            return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"API request failed for {url}: {str(e)}")
        raise Exception(f"API request failed: {str(e)}")

def categorize_frequency(frequency: int) -> str:
    """Categorize chemical frequency."""
    if frequency == 0:
        return "Not found"
    elif frequency == 1:
        return "Unique"
    elif frequency <= 10:
        return "Very rare"
    elif frequency <= 100:
        return "Rare"
    elif frequency <= 1000:
        return "Uncommon"
    elif frequency <= 10000:
        return "Common"
    else:
        return "Very common"

def calculate_rarity_score(frequency: int) -> float:
    """Calculate rarity score for a chemical."""
    import math
    if frequency == 0:
        return 0.0
    elif frequency == 1:
        return 1.0
    # Logarithmic scale for rarity (higher frequency = lower rarity)
    return max(0.0, 1.0 - math.log10(frequency) / 6.0)

# ===== Document & Patent Search Tools (4 tools) =====

@mcp.tool()
async def search_patents(query: str, limit: int = 25, offset: int = 0, patent_offices: str = "US OR EP OR WO OR JP OR CN") -> Dict[str, Any]:
    """
    Search patents by text, keywords, or identifiers in SureChEMBL database.
    
    Args:
        query: Search query (keywords, patent numbers, or text like "KRAS", "cancer drug", etc.)
        limit: Number of results to return (1-1000, default: 25)
        offset: Number of results to skip (default: 0)
        patent_offices: Patent offices to search (default: "US OR EP OR WO OR JP OR CN")
    
    Returns:
        Dictionary containing search results with patent information
    """
    logging.info(f"Searching patents with query: {query}, limit: {limit}, offset: {offset}")
    
    try:
        # Calculate page number from offset and limit
        page = (offset // limit) + 1
        
        # Build the search query with patent office filter
        full_query = f"{query} AND ((pnctry:({patent_offices})))"
        
        # Use the search/content endpoint for text-based patent searches
        params = {
            "query": full_query,
            "page": page,
            "itemsPerPage": min(limit, 1000)  # API may have max limit
        }
        
        results = await asyncio.to_thread(
            make_api_request,
            "search/content",
            params=params
        )
        
        # Extract relevant information
        if results.get("status") == "OK" and "data" in results:
            data = results["data"]
            search_results = data.get("results", {})
            documents = search_results.get("documents", [])
            total_hits = search_results.get("total_hits", 0)
            
            return {
                "status": "OK",
                "query": query,
                "full_query": full_query,
                "total_hits": total_hits,
                "page": page,
                "items_per_page": limit,
                "documents": documents,
                "message": f"Found {total_hits} patents matching '{query}'"
            }
        else:
            return results
            
    except Exception as e:
        logging.error(f"Error searching patents: {str(e)}")
        return {"error": f"Failed to search patents: {str(e)}"}

@mcp.tool()
async def get_document_content(document_id: str) -> Dict[str, Any]:
    """
    Get complete patent document content with chemical annotations by document ID.
    
    Args:
        document_id: Patent document ID (e.g., WO-2020096695-A1)
    
    Returns:
        Dictionary containing document content
    """
    logging.info(f"Fetching document content for: {document_id}")
    
    try:
        result = await asyncio.to_thread(
            make_api_request,
            f"document/{document_id}/contents"
        )
        return result
    except Exception as e:
        logging.error(f"Error fetching document content: {str(e)}")
        return {"error": f"Failed to get document content: {str(e)}"}

@mcp.tool()
async def get_patent_family(patent_id: str) -> Dict[str, Any]:
    """
    Get patent family members and relationships for a patent.
    
    Args:
        patent_id: Patent ID to find family members for
    
    Returns:
        Dictionary containing patent family information
    """
    logging.info(f"Fetching patent family for: {patent_id}")
    
    try:
        result = await asyncio.to_thread(
            make_api_request,
            f"document/{patent_id}/family/members"
        )
        return result
    except Exception as e:
        logging.error(f"Error fetching patent family: {str(e)}")
        return {"error": f"Failed to get patent family: {str(e)}"}

@mcp.tool()
async def search_by_patent_number(patent_number: str) -> Dict[str, Any]:
    """
    Search for patents by specific patent numbers or publication numbers.
    
    Args:
        patent_number: Patent or publication number
    
    Returns:
        Dictionary containing patent information
    """
    logging.info(f"Searching by patent number: {patent_number}")
    
    try:
        result = await asyncio.to_thread(
            make_api_request,
            f"document/{patent_number}/contents"
        )
        
        return {
            "patent_number": patent_number,
            "document": result
        }
    except Exception as e:
        logging.error(f"Error searching by patent number: {str(e)}")
        return {"error": f"Failed to find patent: {str(e)}"}

# ===== Chemical Search & Retrieval Tools (4 tools) =====

@mcp.tool()
async def search_chemicals_by_name(name: str, limit: int = 25) -> Dict[str, Any]:
    """
    Search for chemicals by name, synonym, or common name.
    
    Args:
        name: Chemical name or synonym to search for
        limit: Number of results to return (1-1000, default: 25)
    
    Returns:
        Dictionary containing search results
    """
    logging.info(f"Searching chemicals by name: {name}, limit: {limit}")
    
    try:
        result = await asyncio.to_thread(
            make_api_request,
            f"chemical/name/{requests.utils.quote(name)}"
        )
        return result
    except Exception as e:
        logging.error(f"Error searching chemicals by name: {str(e)}")
        return {"error": f"Failed to search chemicals: {str(e)}"}

@mcp.tool()
async def get_chemical_by_id(chemical_id: str) -> Dict[str, Any]:
    """
    Get detailed chemical information by SureChEMBL chemical ID.
    
    Args:
        chemical_id: SureChEMBL chemical ID (numeric)
    
    Returns:
        Dictionary containing chemical information
    """
    logging.info(f"Fetching chemical by ID: {chemical_id}")
    
    try:
        result = await asyncio.to_thread(
            make_api_request,
            f"chemical/id/{chemical_id}"
        )
        return result
    except Exception as e:
        logging.error(f"Error fetching chemical by ID: {str(e)}")
        return {"error": f"Failed to get chemical: {str(e)}"}

@mcp.tool()
async def search_by_smiles(smiles: str, limit: int = 25) -> Dict[str, Any]:
    """
    Search for chemicals by SMILES structure notation.
    
    Args:
        smiles: SMILES string of the chemical structure
        limit: Number of results to return (1-1000, default: 25)
    
    Returns:
        Dictionary containing search results
    """
    logging.info(f"Searching by SMILES: {smiles}, limit: {limit}")
    
    # SureChEMBL doesn't have direct SMILES search
    return {
        "message": "SMILES search not directly supported by SureChEMBL API",
        "smiles": smiles,
        "suggestion": "Try converting SMILES to chemical name or use structure-based search tools"
    }

@mcp.tool()
async def search_by_inchi(inchi: str, limit: int = 25) -> Dict[str, Any]:
    """
    Search for chemicals by InChI or InChI key.
    
    Args:
        inchi: InChI string or InChI key
        limit: Number of results to return (1-1000, default: 25)
    
    Returns:
        Dictionary containing search results
    """
    logging.info(f"Searching by InChI: {inchi}, limit: {limit}")
    
    # SureChEMBL doesn't have direct InChI search
    return {
        "message": "InChI search not directly supported by SureChEMBL API",
        "inchi": inchi,
        "suggestion": "Try converting InChI to chemical name or use chemical ID lookup"
    }

# ===== Structure & Visualization Tools (2 tools) =====

@mcp.tool()
async def get_chemical_image(structure: str, height: int = 200, width: int = 200) -> Dict[str, Any]:
    """
    Generate chemical structure image from SMILES or other structure notation.
    
    Args:
        structure: SMILES string or other structure notation
        height: Image height in pixels (default: 200)
        width: Image width in pixels (default: 200)
    
    Returns:
        Dictionary containing image data
    """
    logging.info(f"Generating chemical image for structure: {structure}")
    
    try:
        image_data = await asyncio.to_thread(
            make_api_request,
            "service/chemical/image",
            params={"structure": structure, "height": height, "width": width},
            response_type="binary"
        )
        
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        return {
            "structure": structure,
            "image_data": f"data:image/png;base64,{base64_image}",
            "dimensions": {"width": width, "height": height},
            "message": "Chemical structure image generated successfully"
        }
    except Exception as e:
        logging.error(f"Error generating chemical image: {str(e)}")
        return {"error": f"Failed to generate chemical image: {str(e)}"}

@mcp.tool()
async def get_chemical_properties(chemical_id: str) -> Dict[str, Any]:
    """
    Get molecular properties and descriptors for a chemical by ID.
    
    Args:
        chemical_id: SureChEMBL chemical ID
    
    Returns:
        Dictionary containing chemical properties
    """
    logging.info(f"Fetching chemical properties for ID: {chemical_id}")
    
    try:
        result = await asyncio.to_thread(
            make_api_request,
            f"chemical/id/{chemical_id}"
        )
        
        # Extract and format properties
        chemical = result.get("data", [{}])[0] if result.get("data") else {}
        
        if not chemical:
            return {"error": "Chemical not found"}
        
        properties = {
            "chemical_id": chemical.get("chemical_id"),
            "name": chemical.get("name"),
            "molecular_weight": chemical.get("mol_weight"),
            "smiles": chemical.get("smiles"),
            "inchi": chemical.get("inchi"),
            "inchi_key": chemical.get("inchi_key"),
            "is_element": chemical.get("is_element") == "1",
            "global_frequency": chemical.get("global_frequency"),
            "structural_alerts": chemical.get("mchem_struct_alert") == "1",
            "log_p": chemical.get("log_p"),
            "donor_count": chemical.get("donor_count"),
            "acceptor_count": chemical.get("accept_count"),
            "ring_count": chemical.get("ring_count"),
            "rotatable_bonds": chemical.get("rotatable_bond_count")
        }
        
        return {
            "chemical_id": chemical_id,
            "properties": properties
        }
    except Exception as e:
        logging.error(f"Error fetching chemical properties: {str(e)}")
        return {"error": f"Failed to get chemical properties: {str(e)}"}

# ===== Data Export & Analysis Tools (2 tools) =====

@mcp.tool()
async def export_chemicals(chemical_ids: List[str], output_type: str = "csv", kind: str = "cid") -> Dict[str, Any]:
    """
    Bulk export chemical data in CSV or XML format.
    
    Args:
        chemical_ids: Array of SureChEMBL chemical IDs (1-100)
        output_type: Export format (default: csv)
        kind: ID type for export (default: cid)
    
    Returns:
        Dictionary containing export data
    """
    logging.info(f"Exporting {len(chemical_ids)} chemicals in {output_type} format")
    
    try:
        if len(chemical_ids) > 100:
            return {"error": "Maximum 100 chemical IDs allowed per export"}
        
        chem_ids_str = ",".join(chemical_ids)
        
        export_data = await asyncio.to_thread(
            make_api_request,
            "export/chemistry",
            params={"chemIDs": chem_ids_str, "output_type": output_type, "kind": kind},
            response_type="binary"
        )
        
        base64_data = base64.b64encode(export_data).decode('utf-8')
        
        return {
            "chemical_ids": chemical_ids,
            "output_type": output_type,
            "kind": kind,
            "export_data": f"data:application/zip;base64,{base64_data}",
            "message": f"Successfully exported {len(chemical_ids)} chemicals in {output_type} format"
        }
    except Exception as e:
        logging.error(f"Error exporting chemicals: {str(e)}")
        return {"error": f"Failed to export chemicals: {str(e)}"}

@mcp.tool()
async def analyze_patent_chemistry(document_id: str) -> Dict[str, Any]:
    """
    Analyze chemical content and annotations in a patent document.
    
    Args:
        document_id: Patent document ID to analyze
    
    Returns:
        Dictionary containing analysis results
    """
    logging.info(f"Analyzing patent chemistry for document: {document_id}")
    
    try:
        result = await asyncio.to_thread(
            make_api_request,
            f"document/{document_id}/contents"
        )
        
        document = result.get("data", {})
        
        if not document:
            return {"error": "Document not found"}
        
        # Extract chemical annotations from abstracts and descriptions
        chemical_annotations = []
        
        # Process abstracts
        abstracts = document.get("contents", {}).get("patentDocument", {}).get("abstracts", [])
        for abstract in abstracts:
            annotations = abstract.get("section", {}).get("annotations", [])
            for annotation in annotations:
                chemical_annotations.append({
                    "source": "abstract",
                    "language": abstract.get("lang"),
                    "annotation": annotation
                })
        
        # Process descriptions
        descriptions = document.get("contents", {}).get("patentDocument", {}).get("descriptions", [])
        for description in descriptions:
            annotations = description.get("section", {}).get("annotations", [])
            for annotation in annotations:
                chemical_annotations.append({
                    "source": "description",
                    "language": description.get("lang"),
                    "annotation": annotation
                })
        
        # Analyze chemical content
        unique_chemicals = list(set([a["annotation"].get("name") for a in chemical_annotations if a["annotation"].get("name")]))
        annotation_categories = list(set([a["annotation"].get("category") for a in chemical_annotations if a["annotation"].get("category")]))
        
        analysis = {
            "document_id": document_id,
            "total_chemical_annotations": len(chemical_annotations),
            "unique_chemicals": unique_chemicals,
            "annotation_categories": annotation_categories,
            "chemical_annotations": chemical_annotations,
            "summary": {
                "has_chemical_content": len(chemical_annotations) > 0,
                "languages": list(set([a["language"] for a in chemical_annotations if a.get("language")])),
                "sources": list(set([a["source"] for a in chemical_annotations]))
            }
        }
        
        return analysis
    except Exception as e:
        logging.error(f"Error analyzing patent chemistry: {str(e)}")
        return {"error": f"Failed to analyze patent chemistry: {str(e)}"}

# ===== Advanced Analysis Tools (3 tools) =====

@mcp.tool()
async def get_chemical_frequency(chemical_id: str) -> Dict[str, Any]:
    """
    Get frequency statistics for chemicals across the patent database.
    
    Args:
        chemical_id: SureChEMBL chemical ID
    
    Returns:
        Dictionary containing frequency statistics
    """
    logging.info(f"Getting chemical frequency for ID: {chemical_id}")
    
    try:
        result = await asyncio.to_thread(
            make_api_request,
            f"chemical/id/{chemical_id}"
        )
        
        chemical = result.get("data", [{}])[0] if result.get("data") else {}
        
        if not chemical:
            return {"error": "Chemical not found"}
        
        global_frequency = chemical.get("global_frequency", 0)
        
        frequency_stats = {
            "chemical_id": chemical_id,
            "name": chemical.get("name"),
            "global_frequency": global_frequency,
            "frequency_analysis": {
                "total_occurrences": global_frequency,
                "frequency_category": categorize_frequency(global_frequency),
                "rarity_score": calculate_rarity_score(global_frequency)
            },
            "chemical_info": {
                "smiles": chemical.get("smiles"),
                "molecular_weight": chemical.get("mol_weight"),
                "inchi_key": chemical.get("inchi_key")
            }
        }
        
        return frequency_stats
    except Exception as e:
        logging.error(f"Error getting chemical frequency: {str(e)}")
        return {"error": f"Failed to get chemical frequency: {str(e)}"}

@mcp.tool()
async def search_similar_structures(reference_id: str, threshold: float = 0.7, limit: int = 25) -> Dict[str, Any]:
    """
    Find structurally similar chemicals using similarity search.
    
    Args:
        reference_id: Reference chemical ID for similarity search
        threshold: Similarity threshold (0.0-1.0, default: 0.7)
        limit: Number of results to return (1-100, default: 25)
    
    Returns:
        Dictionary containing similar structures
    """
    logging.info(f"Searching similar structures for ID: {reference_id}, threshold: {threshold}")
    
    try:
        # Get the reference chemical first
        ref_result = await asyncio.to_thread(
            make_api_request,
            f"chemical/id/{reference_id}"
        )
        
        ref_chemical = ref_result.get("data", [{}])[0] if ref_result.get("data") else {}
        
        if not ref_chemical:
            return {"error": "Reference chemical not found"}
        
        # SureChEMBL doesn't have direct similarity search
        similarity_result = {
            "reference_chemical": {
                "id": reference_id,
                "name": ref_chemical.get("name"),
                "smiles": ref_chemical.get("smiles"),
                "molecular_weight": ref_chemical.get("mol_weight")
            },
            "search_parameters": {
                "threshold": threshold,
                "limit": limit
            },
            "message": "Direct similarity search not available in SureChEMBL API",
            "suggestions": [
                "Use chemical name variations to find related compounds",
                "Search by molecular weight ranges",
                "Use external cheminformatics tools for similarity search",
                "Try searching by chemical class or functional groups"
            ],
            "alternative_searches": {
                "by_name_fragments": f"Try searching for fragments of \"{ref_chemical.get('name')}\"",
                "by_molecular_weight": f"Search for compounds with molecular weight around {ref_chemical.get('mol_weight')}",
                "by_chemical_class": "Search for compounds in the same chemical class"
            }
        }
        
        return similarity_result
    except Exception as e:
        logging.error(f"Error searching similar structures: {str(e)}")
        return {"error": f"Failed to search similar structures: {str(e)}"}

@mcp.tool()
async def get_patent_statistics(document_id: str, include_annotations: bool = True) -> Dict[str, Any]:
    """
    Get statistical overview of chemical content in patents.
    
    Args:
        document_id: Patent document ID for statistics
        include_annotations: Include detailed annotation statistics (default: true)
    
    Returns:
        Dictionary containing patent statistics
    """
    logging.info(f"Getting patent statistics for document: {document_id}")
    
    try:
        result = await asyncio.to_thread(
            make_api_request,
            f"document/{document_id}/contents"
        )
        
        document = result.get("data", {})
        
        if not document:
            return {"error": "Document not found"}
        
        # Extract basic document information
        doc_info = document.get("contents", {}).get("patentDocument", {}).get("bibliographicData", {})
        abstracts = document.get("contents", {}).get("patentDocument", {}).get("abstracts", [])
        descriptions = document.get("contents", {}).get("patentDocument", {}).get("descriptions", [])
        
        # Collect all chemical annotations
        all_annotations = []
        
        for abstract in abstracts:
            annotations = abstract.get("section", {}).get("annotations", [])
            for annotation in annotations:
                all_annotations.append({
                    **annotation,
                    "source": "abstract",
                    "language": abstract.get("lang")
                })
        
        for description in descriptions:
            annotations = description.get("section", {}).get("annotations", [])
            for annotation in annotations:
                all_annotations.append({
                    **annotation,
                    "source": "description",
                    "language": description.get("lang")
                })
        
        # Calculate statistics
        chemical_annotations = [a for a in all_annotations if a.get("category") == "chemical"]
        unique_chemicals = list(set([a.get("name") for a in chemical_annotations if a.get("name")]))
        
        chemical_frequencies = {}
        for annotation in chemical_annotations:
            name = annotation.get("name")
            if name:
                chemical_frequencies[name] = chemical_frequencies.get(name, 0) + 1
        
        # Get invention titles
        invention_titles = doc_info.get("inventionTitles", [])
        title = next((t.get("title") for t in invention_titles if t.get("lang") == "EN"), "N/A")
        
        # Get publication info
        pub_ref = doc_info.get("publicationReference", [{}])[0]
        ucid = pub_ref.get("ucid", "N/A")
        doc_ids = pub_ref.get("documentId", [{}])
        pub_date = doc_ids[0].get("date", "N/A") if doc_ids else "N/A"
        
        statistics = {
            "document_id": document_id,
            "document_info": {
                "title": title,
                "publication_number": ucid,
                "publication_date": pub_date
            },
            "content_statistics": {
                "total_sections": len(abstracts) + len(descriptions),
                "abstract_sections": len(abstracts),
                "description_sections": len(descriptions),
                "languages": list(set([s.get("lang") for s in abstracts + descriptions if s.get("lang")]))
            },
            "chemical_statistics": {
                "total_chemical_annotations": len(chemical_annotations),
                "unique_chemicals_count": len(unique_chemicals),
                "most_frequent_chemicals": sorted(
                    [{"name": name, "count": count} for name, count in chemical_frequencies.items()],
                    key=lambda x: x["count"],
                    reverse=True
                )[:10],
                "annotation_sources": {
                    "abstract": len([a for a in chemical_annotations if a.get("source") == "abstract"]),
                    "description": len([a for a in chemical_annotations if a.get("source") == "description"])
                }
            },
            "annotation_categories": {
                "chemical": len(chemical_annotations),
                "other": len(all_annotations) - len(chemical_annotations),
                "total": len(all_annotations)
            }
        }
        
        if include_annotations:
            statistics["detailed_annotations"] = {
                "chemical_annotations": chemical_annotations,
                "unique_chemicals": unique_chemicals,
                "chemical_frequencies": chemical_frequencies
            }
        
        return statistics
    except Exception as e:
        logging.error(f"Error getting patent statistics: {str(e)}")
        return {"error": f"Failed to get patent statistics: {str(e)}"}

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

