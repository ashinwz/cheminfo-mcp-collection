from typing import Any, List, Dict, Optional
import asyncio
import logging
import httpx
from starlette.responses import JSONResponse

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize FastMCP server
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("opentargets-v2")

# Constants
GRAPHQL_API_URL = "https://api.platform.opentargets.org/api/v4/graphql"

# Add health check endpoint
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    """Health check endpoint for Docker healthcheck."""
    return JSONResponse({"status": "healthy", "service": "opentargets-mcp-server"})

async def make_graphql_request(query: str, variables: dict = None) -> Dict[str, Any]:
    """Make a GraphQL request to the Open Targets API with proper error handling."""
    
    async with httpx.AsyncClient() as client:
        try:
            payload = {"query": query}
            if variables:
                payload["variables"] = variables
            
            response = await client.post(GRAPHQL_API_URL, json=payload, timeout=30.0)
            response.raise_for_status()
            result = response.json()
            
            # Check for GraphQL errors
            if "errors" in result:
                logging.error(f"GraphQL errors: {result['errors']}")
                return {"error": f"GraphQL errors: {result['errors']}"}
            
            return result.get("data", {})
        except httpx.HTTPStatusError as e:
            logging.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            return {"error": f"HTTP {e.response.status_code}: {e.response.text}"}
        except Exception as e:
            logging.error(f"Error making GraphQL request: {str(e)}")
            return {"error": str(e)}

def format_target_basic(target: Dict[str, Any]) -> Dict[str, Any]:
    """Format basic target information from search results."""
    return {
        "target_id": target.get("id", "Unknown ID"),
        "name": target.get("name", "No name"),
        "entity": target.get("entity", "Unknown entity"),
    }

def format_target_detailed(target: Dict[str, Any], target_id: str) -> Dict[str, Any]:
    """Format detailed target information."""
    genomic_location = target.get("genomicLocation", {})
    functions = [f.get("label", "") for f in target.get("functionDescriptions", [])]
    
    return {
        "target_id": target_id,
        "name": target.get("approvedName", "No name"),
        "symbol": target.get("approvedSymbol", "Unknown symbol"),
        "biotype": target.get("biotype"),
        "chromosome": genomic_location.get("chromosome"),
        "gene_functions": functions,
    }

def format_disease(disease: Dict[str, Any]) -> Dict[str, Any]:
    """Format disease information."""
    return {
        "disease_id": disease.get("id", "Unknown ID"),
        "name": disease.get("name", "No name"),
    }

def format_drug(drug: Dict[str, Any]) -> Dict[str, Any]:
    """Format drug information."""
    return {
        "drug_id": drug.get("id", "Unknown ID"),
        "name": drug.get("name", "No name"),
    }

def format_target_disease_association(assoc: Dict[str, Any]) -> Dict[str, Any]:
    """Format target-disease association."""
    disease = assoc.get("disease", {})
    return {
        "disease_id": disease.get("id", "Unknown ID"),
        "disease_name": disease.get("name", "No name"),
        "association_score": assoc.get("score", 0),
    }

def format_disease_target_association(assoc: Dict[str, Any]) -> Dict[str, Any]:
    """Format disease-target association."""
    target = assoc.get("target", {})
    return {
        "target_id": target.get("id", "Unknown ID"),
        "target_symbol": target.get("approvedSymbol", "Unknown symbol"),
        "target_name": target.get("approvedName", "No name"),
        "association_score": assoc.get("score", 0),
    }

@mcp.tool()
async def search_targets(query: str, max_results: int = 10, **kwargs) -> List[Dict[str, Any]]:
    """
    Search Open Targets for gene targets matching the query.
    
    Args:
        query: Search query for target names or symbols
        max_results: Maximum number of results to return (default: 10)
        
    Returns:
        List of dictionaries containing target information
    """
    # Normalize camelCase to snake_case if needed
    if 'maxResults' in kwargs:
        max_results = kwargs['maxResults']
    
    logging.info(f"Searching for targets with query: {query}, max_results: {max_results}")
    
    graphql_query = """
    query SearchTargets($queryString: String!, $size: Int!, $index: Int!) {
      search(queryString: $queryString, entityNames: ["target"], page: {size: $size, index: $index}) {
        hits {
          id
          entity
          name
        }
      }
    }
    """
    
    variables = {
        "queryString": query,
        "size": max_results,
        "index": 0
    }
    
    try:
        results = await make_graphql_request(graphql_query, variables)
        
        if "error" in results:
            return [{"error": f"Error searching Open Targets: {results['error']}"}]
        
        hits = results.get("search", {}).get("hits", [])
        
        if not hits:
            return [{"message": "No targets found for your query"}]
        
        return [format_target_basic(hit) for hit in hits]
    except Exception as e:
        return [{"error": f"An error occurred while searching: {str(e)}"}]

@mcp.tool()
async def get_target_details(target_id: str, **kwargs) -> Dict[str, Any]:
    """
    Get detailed information about a specific target by ID.
    
    Args:
        target_id: Open Targets ID for the target (e.g., "ENSG00000157764")
        
    Returns:
        Dictionary containing detailed target information
    """
    # Normalize camelCase to snake_case if needed
    if 'targetId' in kwargs:
        target_id = kwargs['targetId']
    
    logging.info(f"Fetching target details for ID: {target_id}")
    
    graphql_query = """
    query TargetDetails($ensemblId: String!) {
      target(ensemblId: $ensemblId) {
        id
        approvedSymbol
        approvedName
        biotype
        genomicLocation {
          chromosome
          start
          end
        }
        functionDescriptions
      }
    }
    """
    
    variables = {"ensemblId": target_id}
    
    try:
        results = await make_graphql_request(graphql_query, variables)
        
        if "error" in results:
            return {"error": f"Error retrieving target details: {results['error']}"}
        
        target = results.get("target")
        if not target:
            return {"error": f"No target found with ID: {target_id}"}
        
        return format_target_detailed(target, target_id)
    except Exception as e:
        return {"error": f"An error occurred while fetching target details: {str(e)}"}

@mcp.tool()
async def search_diseases(query: str, max_results: int = 10, **kwargs) -> List[Dict[str, Any]]:
    """
    Search for diseases in Open Targets.
    
    Args:
        query: Search query for disease names
        max_results: Maximum number of results to return (default: 10)
        
    Returns:
        List of dictionaries containing disease information
    """
    # Normalize camelCase to snake_case if needed
    if 'maxResults' in kwargs:
        max_results = kwargs['maxResults']
    
    logging.info(f"Searching for diseases with query: {query}, max_results: {max_results}")
    
    graphql_query = """
    query SearchDiseases($queryString: String!, $size: Int!, $index: Int!) {
      search(queryString: $queryString, entityNames: ["disease"], page: {size: $size, index: $index}) {
        hits {
          id
          entity
          name
        }
      }
    }
    """
    
    variables = {
        "queryString": query,
        "size": max_results,
        "index": 0
    }
    
    try:
        results = await make_graphql_request(graphql_query, variables)
        
        if "error" in results:
            return [{"error": f"Error searching diseases: {results['error']}"}]
        
        hits = results.get("search", {}).get("hits", [])
        
        if not hits:
            return [{"message": "No diseases found for your query"}]
        
        return [format_disease(hit) for hit in hits]
    except Exception as e:
        return [{"error": f"An error occurred while searching diseases: {str(e)}"}]

@mcp.tool()
async def get_target_associated_diseases(target_id: str, max_results: int = 10, **kwargs) -> List[Dict[str, Any]]:
    """
    Get diseases associated with a specific target.
    
    Args:
        target_id: Open Targets ID for the target (e.g., "ENSG00000112164" for GLP1R)
        max_results: Maximum number of results to return (default: 10)
        
    Returns:
        List of dictionaries containing target-disease association information
    """
    # Normalize camelCase to snake_case if needed
    if 'targetId' in kwargs:
        target_id = kwargs['targetId']
    if 'maxResults' in kwargs:
        max_results = kwargs['maxResults']
    
    logging.info(f"Fetching diseases associated with target: {target_id}, max_results: {max_results}")
    
    graphql_query = """
    query TargetAssociatedDiseases($ensemblId: String!, $size: Int!, $index: Int!) {
      target(ensemblId: $ensemblId) {
        id
        approvedSymbol
        approvedName
        associatedDiseases(page: {size: $size, index: $index}) {
          rows {
            disease {
              id
              name
            }
            score
          }
        }
      }
    }
    """
    
    variables = {
        "ensemblId": target_id,
        "size": max_results,
        "index": 0
    }
    
    try:
        results = await make_graphql_request(graphql_query, variables)
        
        if "error" in results:
            return [{"error": f"Error retrieving associated diseases: {results['error']}"}]
        
        target = results.get("target")
        if not target:
            return [{"error": f"No target found with ID: {target_id}"}]
        
        associations = target.get("associatedDiseases", {}).get("rows", [])
        if not associations:
            return [{"message": f"No diseases associated with target ID: {target_id}"}]
        
        return [format_target_disease_association(assoc) for assoc in associations]
    except Exception as e:
        return [{"error": f"An error occurred while fetching associated diseases: {str(e)}"}]

@mcp.tool()
async def get_disease_associated_targets(disease_id: str, max_results: int = 10, **kwargs) -> List[Dict[str, Any]]:
    """
    Get targets associated with a specific disease.
    
    Args:
        disease_id: Open Targets disease ID (e.g., "MONDO_0005148" for type 2 diabetes)
        max_results: Maximum number of results to return (default: 10)
        
    Returns:
        List of dictionaries containing disease-target association information
    """
    # Normalize camelCase to snake_case if needed
    if 'diseaseId' in kwargs:
        disease_id = kwargs['diseaseId']
    if 'maxResults' in kwargs:
        max_results = kwargs['maxResults']
    
    logging.info(f"Fetching targets associated with disease: {disease_id}, max_results: {max_results}")
    
    graphql_query = """
    query DiseaseAssociatedTargets($efoId: String!, $size: Int!, $index: Int!) {
      disease(efoId: $efoId) {
        id
        name
        associatedTargets(page: {size: $size, index: $index}) {
          rows {
            target {
              id
              approvedSymbol
              approvedName
            }
            score
          }
        }
      }
    }
    """
    
    variables = {
        "efoId": disease_id,
        "size": max_results,
        "index": 0
    }
    
    try:
        results = await make_graphql_request(graphql_query, variables)
        
        if "error" in results:
            return [{"error": f"Error retrieving associated targets: {results['error']}"}]
        
        disease = results.get("disease")
        if not disease:
            return [{"error": f"No disease found with ID: {disease_id}"}]
        
        associations = disease.get("associatedTargets", {}).get("rows", [])
        if not associations:
            return [{"message": f"No targets associated with disease ID: {disease_id}"}]
        
        return [format_disease_target_association(assoc) for assoc in associations]
    except Exception as e:
        return [{"error": f"An error occurred while fetching associated targets: {str(e)}"}]

@mcp.tool()
async def search_drugs(query: str, max_results: int = 10, **kwargs) -> List[Dict[str, Any]]:
    """
    Search for drugs in Open Targets.
    
    Args:
        query: Search query for drug names
        max_results: Maximum number of results to return (default: 10)
        
    Returns:
        List of dictionaries containing drug information
    """
    # Normalize camelCase to snake_case if needed
    if 'maxResults' in kwargs:
        max_results = kwargs['maxResults']
    
    logging.info(f"Searching for drugs with query: {query}, max_results: {max_results}")
    
    graphql_query = """
    query SearchDrugs($queryString: String!, $size: Int!, $index: Int!) {
      search(queryString: $queryString, entityNames: ["drug"], page: {size: $size, index: $index}) {
        hits {
          id
          entity
          name
        }
      }
    }
    """
    
    variables = {
        "queryString": query,
        "size": max_results,
        "index": 0
    }
    
    try:
        results = await make_graphql_request(graphql_query, variables)
        
        if "error" in results:
            return [{"error": f"Error searching drugs: {results['error']}"}]
        
        hits = results.get("search", {}).get("hits", [])
        
        if not hits:
            return [{"message": "No drugs found for your query"}]
        
        return [format_drug(hit) for hit in hits]
    except Exception as e:
        return [{"error": f"An error occurred while searching drugs: {str(e)}"}]

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