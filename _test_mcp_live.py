import time
import os
from agent.kernel import KernelOS
from core.tools.mcp_client import MCPServerConfig, MCPTransport

def test_mcp_live():
    print("============================================================")
    print("BUDDY Live MCP Integration Test")
    print("============================================================")
    
    print("[1] Initializing KernelOS...")
    kernel = KernelOS()
    
    config = MCPServerConfig(
        name="memory_test",
        transport=MCPTransport.STDIO,
        command="npx.cmd" if os.name == 'nt' else "npx",
        args=["-y", "@modelcontextprotocol/server-memory"]
    )
    
    print(f"\n[2] Adding 'memory_test' MCP server to catalog...")
    kernel.mcp.add_to_catalog(config)
    
    print("\n[3] Starting MCP Server (this runs 'npx -y @modelcontextprotocol/server-memory')...")
    start_time = time.time()
    success = kernel.mcp.start_server("memory_test")
    
    if not success:
        print("\n[FAIL] Could not start MCP server.")
        return
        
    elapsed = time.time() - start_time
    print(f"[PASS] Server started in {elapsed:.2f} seconds.")
    
    status = kernel.mcp.get_server_info("memory_test")
    if not status:
        print("\n[FAIL] Server info not found, but start_server returned success?")
        return
        
    print(f"       Tools injected into registry: {status['tool_count']}")
    
    print("\n[4] Querying Tool Registry for dynamically injected tools...")
    injected_tools = [name for name in kernel.tools.list_tools() if "memory_test" in name]
    for name in injected_tools:
        print(f"    - {name}")
        
    if not injected_tools:
        print("\n[FAIL] No tools were injected into the registry.")
        kernel.mcp.stop_server("memory_test")
        return
        
    print("\n[5] Executing multi-step memory operations via MCP...")
    
    try:
        # Step A: Create Entities
        print("    A) Adding entities to knowledge graph...")
        res_create = kernel.tools.execute("mcp_memory_test_create_entities", {
            "entities": [
                {"name": "Buddy", "entityType": "AI Assistant", "observations": ["Is testing the MCP server"]},
                {"name": "Buddy MK-67", "entityType": "System", "observations": ["Runs Buddy"]}
            ]
        })
        print(f"       Result: {res_create}")
        
        # Step B: Read Graph
        print("    B) Reading knowledge graph...")
        res_read = kernel.tools.execute("mcp_memory_test_read_graph", {})
        print(f"       Result: {res_read}")
        
        # Simple validation
        if "Buddy" in str(res_read) and "Buddy MK-67" in str(res_read):
            print("\n[PASS] Multi-step execution verified successfully.")
        else:
            print("\n[FAIL] Data read did not match inserted data.")
            
    except Exception as e:
        print(f"\n[FAIL] Exception during tool execution: {e}")
        
    print("\n[6] Tearing down MCP Server...")
    kernel.mcp.stop_server("memory_test")
    
    print("\n[PASS] Live MCP test complete.")
    
if __name__ == "__main__":
    test_mcp_live()
