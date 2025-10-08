"""
SureChEMBL MCP Server Example Usage

This script demonstrates how to use the SureChEMBL API functions
to search for patent chemistry data.
"""

import asyncio
import sys
sys.path.append('.')

from surechembl_server import (
    search_chemicals_by_name,
    get_chemical_by_id,
    get_document_content,
    analyze_patent_chemistry,
    get_patent_statistics,
    search_patents
)


async def main():
    print("=" * 80)
    print("SureChEMBL MCP Server Example Usage")
    print("=" * 80)
    
    # Example 1: Search chemicals by name
    print("\n1. Searching for 'aspirin'...")
    aspirin_results = await search_chemicals_by_name(name="aspirin", limit=3)
    print(f"Results: {aspirin_results}")
    
    # Example 2: Search patents
    print("\n2. Searching patents for 'cancer drug'...")
    patent_results = await search_patents(query="cancer drug", limit=2)
    print(f"Results: {patent_results}")
    
    # Example 3: Get chemical by ID (if we have one from previous search)
    if aspirin_results and not aspirin_results.get("error"):
        data = aspirin_results.get("data", [])
        if data and len(data) > 0:
            chem_id = data[0].get("chemical_id")
            if chem_id:
                print(f"\n3. Getting chemical details for ID: {chem_id}...")
                chem_details = await get_chemical_by_id(chemical_id=str(chem_id))
                print(f"Results: {chem_details}")
    
    # Example 4: Get document content (example patent ID)
    print("\n4. Getting document content for patent WO-2020096695-A1...")
    doc_content = await get_document_content(document_id="WO-2020096695-A1")
    if doc_content and not doc_content.get("error"):
        print(f"Document retrieved successfully!")
        print(f"Keys available: {list(doc_content.keys())}")
    else:
        print(f"Note: {doc_content.get('error', 'Unknown error')}")
    
    # Example 5: Analyze patent chemistry
    print("\n5. Analyzing patent chemistry for WO-2020096695-A1...")
    analysis = await analyze_patent_chemistry(document_id="WO-2020096695-A1")
    if analysis and not analysis.get("error"):
        print(f"Analysis complete!")
        print(f"Total chemical annotations: {analysis.get('total_chemical_annotations', 0)}")
        print(f"Unique chemicals: {len(analysis.get('unique_chemicals', []))}")
    else:
        print(f"Note: {analysis.get('error', 'Unknown error')}")
    
    # Example 6: Get patent statistics
    print("\n6. Getting patent statistics for WO-2020096695-A1...")
    stats = await get_patent_statistics(document_id="WO-2020096695-A1", include_annotations=False)
    if stats and not stats.get("error"):
        print(f"Statistics retrieved!")
        print(f"Document info: {stats.get('document_info', {})}")
        print(f"Chemical statistics: {stats.get('chemical_statistics', {})}")
    else:
        print(f"Note: {stats.get('error', 'Unknown error')}")
    
    print("\n" + "=" * 80)
    print("Example usage complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

