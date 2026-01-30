"""
EMQX Message Tools Module

This module provides tools for publishing MQTT messages to an EMQX broker.
It registers these tools with the MCP server, making them available for clients
to use through the MCP protocol.
"""

import logging
from typing import Any
from ..emqx_client import EMQXClient

class EMQXMessageTools:
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.emqx_client = EMQXClient(logger)

    def register_tools(self, mcp: Any):
        """Register EMQX Publish tools."""
        
        @mcp.tool(name="publish_mqtt_message", 
                  description="Publish an MQTT Message to Your EMQX Cluster on EMQX Cloud or Self-Managed Deployment")
        async def publish(request):
            """Handle publish message request
            
            Args:
                request: MCP request containing message data
                    - topic: MQTT topic 
                    - payload: Message content
                    - qos: Quality of Service (0, 1, or 2)
                    - retain: Whether to retain the message (true or false)
            
            Returns:
                MCPResponse: Response object with publish result
            """
            self.logger.info("Handling publish request")
            
            # Extract parameters from the request
            topic = request.get("topic")
            payload = request.get("payload")
            qos = request.get("qos", 0)  # Default QoS level is 0
            retain = request.get("retain", False)  # Default is not to retain
            
            # Validate required parameters before proceeding
            if not topic:
                self.logger.error("Missing required parameter: topic")
                return f'"error": "Missing required parameter: topic"'
            
            if payload is None:
                self.logger.error("Missing required parameter: payload")
                return f'"error": "Missing required parameter: payload"'
            
            # Publish message to EMQX using the client
            result = await self.emqx_client.publish_message(
                topic=topic,
                payload=payload,
                qos=qos,
                retain=retain
            )
            
            self.logger.info(f"Message published successfully to topic: {topic}")
            return result