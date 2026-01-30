"""
EMQX Client Tools Module

This module provides tools for managing MQTT clients connected to an EMQX broker.
It registers these tools with the MCP server, making them available for clients
to use through the MCP protocol.
"""

import logging
from typing import Any
from ..emqx_client import EMQXClient

class EMQXClientTools:
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.emqx_client = EMQXClient(logger)

    def register_tools(self, mcp: Any):
        """Register EMQX Client management tools."""
        
        @mcp.tool(name="list_mqtt_clients", 
                  description="List MQTT clients connected to your EMQX Cluster")
        async def list_clients(request):
            """Handle list clients request
            
            Args:
                request: MCP request containing filter parameters
                    - page: Page number (default: 1)
                    - limit: Results per page, max 10000 (default: 10)
                    - node: Node name
                    - clientid: Client ID
                    - username: Username
                    - ip_address: Client IP address
                    - conn_state: Connection state
                    - clean_start: Clean start flag
                    - proto_ver: Protocol version
                    - like_clientid: Fuzzy search by client ID pattern
                    - like_username: Fuzzy search by username pattern
                    - like_ip_address: Fuzzy search by IP address pattern
            
            Returns:
                MCPResponse: Response object with list of clients
            """
            self.logger.info("Handling list clients request")
            
            # Extract optional parameters from the request with defaults
            params = {
                "page": request.get("page", 1),
                "limit": request.get("limit", 100)
            }
            
            # Optional parameters to include if present
            optional_params = [
                "node", "clientid", "username", "ip_address", "conn_state", 
                "clean_start", "proto_ver", "like_clientid", "like_username", 
                "like_ip_address"
            ]
            
            for param in optional_params:
                if param in request:
                    params[param] = request.get(param)
            
            # Get list of clients from EMQX
            result = await self.emqx_client.list_clients(params)
            
            self.logger.info("Client list retrieved successfully")
            return result 

        @mcp.tool(name="get_mqtt_client", 
                  description="Get detailed information about a specific MQTT client by client ID")
        async def get_client_info(request):
            """Handle get client info request
            
            Args:
                request: MCP request containing client identifier
                    - clientid: Client ID (required) - The unique identifier of the client to retrieve

            Returns:
                MCPResponse: Response object with detailed client information
            """
            self.logger.info("Handling get client info request")
            
            # Extract required client ID parameter
            clientid = request.get("clientid")
            if not clientid:
                self.logger.error("Client ID is required but was not provided")
                return {"error": "Client ID is required"}
            
            # Get client information from EMQX
            result = await self.emqx_client.get_client_info(clientid)
            
            self.logger.info(f"Client info for '{clientid}' retrieved successfully")
            return result 

        @mcp.tool(name="kick_mqtt_client", 
                  description="Disconnect a client from the MQTT broker by client ID")
        async def kick_client(request):
            """Handle kick client request
            
            Args:
                request: MCP request containing client identifier
                    - clientid: Client ID (required) - The unique identifier of the client to disconnect

            Returns:
                MCPResponse: Response object with the result of the disconnect operation
            """
            self.logger.info("Handling kick client request")
            
            # Extract required client ID parameter
            clientid = request.get("clientid")
            if not clientid:
                self.logger.error("Client ID is required but was not provided")
                return {"error": "Client ID is required"}
            
            # Kick client from EMQX
            result = await self.emqx_client.kick_client(clientid)
            
            self.logger.info(f"Client '{clientid}' disconnect request processed")
            return result 