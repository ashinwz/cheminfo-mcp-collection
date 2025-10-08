from typing import Any, List, Dict, Optional
import asyncio
import logging
import httpx
from starlette.responses import JSONResponse
from mcp.server.fastmcp import FastMCP

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize FastMCP server
mcp = FastMCP("drugbank")

# Constants
API_BASE_URL = "https://api.drugbank.com/v1"
API_KEY = ""  # Replace with your DrugBank API key

# Add health check endpoint
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    """Health check endpoint for Docker healthcheck."""
    return JSONResponse({"status": "healthy", "service": "drugbank-mcp-server"})

async def make_api_request(endpoint: str, params: dict = None) -> Dict[str, Any]:
    """Make a request to the DrugBank API with proper error handling."""
    if not API_KEY:
        logging.error("DrugBank API key not configured")
        return {"error": "DrugBank API key not configured. Please set API_KEY in the script."}
    
    url = f"{API_BASE_URL}/{endpoint}"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logging.error(f"HTTP error for {endpoint}: {e.response.status_code} - {e.response.text}")
            return {"error": f"HTTP {e.response.status_code}: {e.response.text}"}
        except Exception as e:
            logging.error(f"Error making API request to {endpoint}: {str(e)}")
            return {"error": str(e)}

def format_drug_basic(drug: Dict[str, Any]) -> Dict[str, Any]:
    """Format basic drug information."""
    return {
        "drug_id": drug.get("id", "Unknown ID"),
        "name": drug.get("name", "No name"),
        "cas_number": drug.get("cas_number"),
        "synonyms": drug.get("synonyms", []),
        "groups": drug.get("groups", []),
    }

def format_drug_detailed(drug: Dict[str, Any], drug_id: str) -> Dict[str, Any]:
    """Format detailed drug information."""
    return {
        "drug_id": drug_id,
        "name": drug.get("name", "No name"),
        "description": drug.get("description"),
        "cas_number": drug.get("cas_number"),
        "groups": drug.get("groups", []),
        "indication": drug.get("indication"),
        "mechanism_of_action": drug.get("mechanism_of_action"),
        "pharmacodynamics": drug.get("pharmacodynamics"),
        "synonyms": drug.get("synonyms", []),
    }

def format_interaction(interaction: Dict[str, Any]) -> Dict[str, Any]:
    """Format drug interaction information."""
    interacting_drug = interaction.get("interacting_drug", {})
    return {
        "interacting_drug_name": interacting_drug.get("name", "Unknown drug"),
        "interacting_drug_id": interacting_drug.get("id", "Unknown ID"),
        "description": interaction.get("description", "No description available"),
    }

@mcp.tool()
async def search_drugs(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Search DrugBank for drugs matching the query.
    
    Args:
        query: Search query for drug names
        max_results: Maximum number of results to return (default: 10)
        
    Returns:
        List of dictionaries containing drug information
    """
    logging.info(f"Searching for drugs with query: {query}, max_results: {max_results}")
    
    params = {
        "q": query,
        "limit": max_results
    }
    
    results = await make_api_request("drugs", params)
    
    if "error" in results:
        return [{"error": f"Error searching DrugBank: {results['error']}"}]
    
    drugs = results.get("data", [])
    if not drugs:
        return [{"message": "No drugs found for your query"}]
    
    return [format_drug_basic(drug) for drug in drugs]

@mcp.tool()
async def get_drug_details(drug_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific drug by its DrugBank ID.
    
    Args:
        drug_id: DrugBank ID of the drug (e.g., "DB00001")
        
    Returns:
        Dictionary containing detailed drug information
    """
    logging.info(f"Fetching drug details for ID: {drug_id}")
    
    results = await make_api_request(f"drugs/{drug_id}")
    
    if "error" in results:
        return {"error": f"Error retrieving drug details: {results['error']}"}
    
    drug = results.get("data", {})
    if not drug:
        return {"error": f"No drug found with ID: {drug_id}"}
    
    return format_drug_detailed(drug, drug_id)

@mcp.tool()
async def find_drugs_by_indication(indication: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Search for drugs used to treat a specific medical condition.
    
    Args:
        indication: Medical condition or disease
        max_results: Maximum number of results to return (default: 10)
        
    Returns:
        List of dictionaries containing drug information
    """
    logging.info(f"Searching for drugs by indication: {indication}, max_results: {max_results}")
    
    params = {
        "q": f"indication:{indication}",
        "limit": max_results
    }
    
    results = await make_api_request("drugs", params)
    
    if "error" in results:
        return [{"error": f"Error searching by indication: {results['error']}"}]
    
    drugs = results.get("data", [])
    if not drugs:
        return [{"message": f"No drugs found for indication: {indication}"}]
    
    return [format_drug_basic(drug) for drug in drugs]

@mcp.tool()
async def find_drugs_by_category(category: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Search for drugs in a specific category.
    
    Args:
        category: Drug category (e.g., "antibiotic", "antidepressant")
        max_results: Maximum number of results to return (default: 10)
        
    Returns:
        List of dictionaries containing drug information
    """
    logging.info(f"Searching for drugs by category: {category}, max_results: {max_results}")
    
    params = {
        "q": f"category:{category}",
        "limit": max_results
    }
    
    results = await make_api_request("drugs", params)
    
    if "error" in results:
        return [{"error": f"Error searching by category: {results['error']}"}]
    
    drugs = results.get("data", [])
    if not drugs:
        return [{"message": f"No drugs found for category: {category}"}]
    
    return [format_drug_basic(drug) for drug in drugs]

@mcp.tool()
async def get_drug_interactions(drug_id: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Get drug interactions for a specific drug.
    
    Args:
        drug_id: DrugBank ID of the drug (e.g., "DB00001")
        max_results: Maximum number of interactions to return (default: 10)
        
    Returns:
        List of dictionaries containing drug interaction information
    """
    logging.info(f"Fetching drug interactions for ID: {drug_id}, max_results: {max_results}")
    
    results = await make_api_request(f"drugs/{drug_id}/interactions")
    
    if "error" in results:
        return [{"error": f"Error retrieving drug interactions: {results['error']}"}]
    
    interactions = results.get("data", [])[:max_results]
    if not interactions:
        return [{"message": f"No interactions found for drug with ID: {drug_id}"}]
    
    return [format_interaction(interaction) for interaction in interactions]

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