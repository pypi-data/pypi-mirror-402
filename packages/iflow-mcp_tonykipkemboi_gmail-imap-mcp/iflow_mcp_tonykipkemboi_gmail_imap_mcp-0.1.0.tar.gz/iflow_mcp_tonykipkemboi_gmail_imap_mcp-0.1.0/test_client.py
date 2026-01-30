#!/usr/bin/env python3
import asyncio
import json
import subprocess
import sys

async def main():
    # Start the Gmail IMAP MCP server as a subprocess
    process = subprocess.Popen(
        ["gmail-imap-mcp"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    
    # Initialize the server
    init_message = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "client_name": "test_client",
            "client_version": "0.1.0"
        }
    }
    
    # Send the initialization message
    process.stdin.write(json.dumps(init_message) + "\n")
    process.stdin.flush()
    
    # Read the response
    response = json.loads(await asyncio.get_event_loop().run_in_executor(None, process.stdout.readline))
    print("Initialization response:", json.dumps(response, indent=2))
    
    # List available tools
    list_tools_message = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "listTools",
        "params": {}
    }
    
    # Send the list tools message
    process.stdin.write(json.dumps(list_tools_message) + "\n")
    process.stdin.flush()
    
    # Read the response
    response = json.loads(await asyncio.get_event_loop().run_in_executor(None, process.stdout.readline))
    print("Available tools:", json.dumps(response, indent=2))
    
    # Authenticate Gmail (you'll need to replace with your actual email)
    auth_message = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "callTool",
        "params": {
            "name": "authenticate-gmail",
            "arguments": {
                "email": "iamtonykipkemboi@gmail.com"  # Replace with your email
            }
        }
    }
    
    # Send the authenticate message
    process.stdin.write(json.dumps(auth_message) + "\n")
    process.stdin.flush()
    
    # Read the response
    response = json.loads(await asyncio.get_event_loop().run_in_executor(None, process.stdout.readline))
    print("Authentication response:", json.dumps(response, indent=2))
    
    # Clean up
    process.terminate()
    process.wait()

if __name__ == "__main__":
    asyncio.run(main())
