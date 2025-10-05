import json
from typing import List, Dict, Any, Optional
from openai import OpenAI
from app.config import settings
from app.maps_client import maps_client

class LLMService:
    def __init__(self):
        self.client = OpenAI(
            base_url=settings.LLM_BASE_URL,
            api_key=settings.LLM_API_KEY or "not-needed"
        )
        self.model = settings.LLM_MODEL

    def get_function_definitions(self) -> List[Dict[str, Any]]:
        """Define available functions for the LLM to call"""
        return [
            {
                "name": "search_places",
                "description": "Search for places, restaurants, or points of interest based on user query. Use this when user asks for recommendations or locations.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query (e.g., 'Italian restaurants', 'coffee shops near me')"
                        },
                        "location": {
                            "type": "string",
                            "description": "The location to search near (address or 'current location')"
                        },
                        "radius": {
                            "type": "integer",
                            "description": "Search radius in meters (default 5000)",
                            "default": 5000
                        },
                        "place_type": {
                            "type": "string",
                            "description": "Type of place (restaurant, cafe, bar, etc.)",
                            "enum": ["restaurant", "cafe", "bar", "store", "park", "museum"]
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_directions",
                "description": "Get directions between two locations. Use when user asks for directions or route information.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "origin": {
                            "type": "string",
                            "description": "Starting location (address or 'current location')"
                        },
                        "destination": {
                            "type": "string",
                            "description": "Destination location or place name"
                        },
                        "mode": {
                            "type": "string",
                            "description": "Travel mode",
                            "enum": ["driving", "walking", "bicycling", "transit"],
                            "default": "driving"
                        }
                    },
                    "required": ["origin", "destination"]
                }
            }
        ]

    def execute_function(self, function_name: str, arguments: Dict[str, Any], user_location: Optional[str] = None) -> Dict[str, Any]:
        """Execute a function call from the LLM"""
        if function_name == "search_places":
            # Use user's actual location if not specified in arguments
            search_location = arguments.get("location")
            if not search_location or search_location == "current location":
                search_location = user_location

            places = maps_client.search_places(
                query=arguments.get("query"),
                location=search_location,
                radius=arguments.get("radius", 5000),
                place_type=arguments.get("place_type")
            )
            return {
                "success": True,
                "places": places[:5],  # Limit to top 5 results
                "count": len(places)
            }

        elif function_name == "get_directions":
            directions = maps_client.get_directions(
                origin=arguments.get("origin"),
                destination=arguments.get("destination"),
                mode=arguments.get("mode", "driving")
            )
            return {
                "success": True,
                "routes": directions
            }

        return {"success": False, "error": "Unknown function"}

    async def chat(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        user_location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process chat message with function calling support

        Returns:
            Dict containing response text, places data, and map data
        """
        if conversation_history is None:
            conversation_history = []

        # Build messages for the LLM
        messages = [
            {
                "role": "system",
                "content": f"""You are a helpful location assistant that helps users find places and get directions.
You have access to Google Maps data and can search for places and provide directions.

User's current location coordinates: {user_location or 'Not provided'}

CRITICAL INSTRUCTIONS:
1. When users ask for places "near me", "nearby", or any location recommendations, you MUST call the search_places function
2. ALWAYS set location parameter to "current location" when the user wants places near them
3. DO NOT make up or invent place names, addresses, or ratings
4. ONLY present actual results from the search_places function
5. If search_places returns no results, say so - don't fabricate data

When calling search_places:
- Set location to "current location" (this will use coordinates: {user_location})
- The function will return real places from Google Maps

When users ask for directions:
- Use the get_directions function with actual place names from search results"""
            }
        ]

        # Add conversation history
        for msg in conversation_history:
            messages.append({"role": msg["role"], "content": msg["content"]})

        # Add current user message
        messages.append({"role": "user", "content": message})

        # First LLM call with function calling
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            functions=self.get_function_definitions(),
            function_call="auto"
        )

        assistant_message = response.choices[0].message
        places_data = None
        map_data = None

        # Check if LLM wants to call a function
        if assistant_message.function_call:
            function_name = assistant_message.function_call.name
            function_args = json.loads(assistant_message.function_call.arguments)

            # Execute the function
            function_result = self.execute_function(function_name, function_args, user_location)

            # Add function call and result to messages
            messages.append({
                "role": "assistant",
                "content": None,
                "function_call": {
                    "name": function_name,
                    "arguments": assistant_message.function_call.arguments
                }
            })

            messages.append({
                "role": "function",
                "name": function_name,
                "content": json.dumps(function_result)
            })

            # Get final response from LLM with function results
            second_response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )

            final_response = second_response.choices[0].message.content

            # Extract places or directions data for frontend
            if function_name == "search_places" and function_result.get("success"):
                places_data = function_result.get("places", [])

            elif function_name == "get_directions" and function_result.get("success"):
                map_data = function_result.get("routes", [])

            return {
                "response": final_response,
                "places": places_data,
                "map_data": map_data
            }

        else:
            # No function call needed, return direct response
            return {
                "response": assistant_message.content,
                "places": None,
                "map_data": None
            }

# Singleton instance
llm_service = LLMService()
