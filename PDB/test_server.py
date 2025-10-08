"""
Test script for the PDB MCP Server.
Run this to verify the server is working correctly.
"""

import asyncio
import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pdb_server import (
    search_structures,
    get_structure_info,
    validate_pdb_id
)

def test_validate_pdb_id():
    """Test PDB ID validation"""
    print("Testing PDB ID validation...")
    
    # Valid PDB IDs
    assert validate_pdb_id("1ABC") == True
    assert validate_pdb_id("1abc") == True
    assert validate_pdb_id("4HHB") == True
    
    # Invalid PDB IDs
    assert validate_pdb_id("ABC1") == False  # Wrong pattern
    assert validate_pdb_id("12345") == False  # Too long
    assert validate_pdb_id("1AB") == False  # Too short
    assert validate_pdb_id("") == False  # Empty
    
    print("✓ PDB ID validation tests passed")

async def test_search():
    """Test structure search"""
    print("\nTesting structure search...")
    
    result = await asyncio.to_thread(
        search_structures,
        query="hemoglobin",
        limit=5
    )
    
    assert "error" not in result, f"Search failed: {result.get('error')}"
    assert "result_set" in result or "total_count" in result, "Unexpected response format"
    
    print(f"✓ Search test passed - Found {result.get('total_count', 0)} structures")

async def test_structure_info():
    """Test getting structure information"""
    print("\nTesting structure info retrieval...")
    
    result = await asyncio.to_thread(
        get_structure_info,
        pdb_id="1HHO",
        format="json"
    )
    
    assert "error" not in result, f"Structure info failed: {result.get('error')}"
    
    print("✓ Structure info test passed")

async def test_invalid_pdb_id():
    """Test error handling for invalid PDB ID"""
    print("\nTesting error handling for invalid PDB ID...")
    
    result = await asyncio.to_thread(
        get_structure_info,
        pdb_id="INVALID",
        format="json"
    )
    
    assert "error" in result, "Should return error for invalid PDB ID"
    
    print("✓ Invalid PDB ID test passed")

async def run_tests():
    """Run all tests"""
    print("=" * 80)
    print("PDB MCP Server - Test Suite")
    print("=" * 80)
    
    try:
        # Run synchronous tests
        test_validate_pdb_id()
        
        # Run async tests
        await test_search()
        await test_structure_info()
        await test_invalid_pdb_id()
        
        print("\n" + "=" * 80)
        print("All tests passed! ✓")
        print("=" * 80)
        return True
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {str(e)}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)


