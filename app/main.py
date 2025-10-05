from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from typing import Dict, Any
import logging

from app.config import settings
from app.models import ChatRequest, ChatResponse, PlaceSearchRequest, DirectionsRequest
from app.llm_service import llm_service
from app.maps_client import maps_client

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="LLM Location Assistant",
    description="AI-powered location recommendations with Google Maps integration",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Serve the frontend HTML"""
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return {"message": "LLM Location Assistant API", "docs": "/docs"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """
    Main chat endpoint with LLM integration

    Processes user messages and returns AI responses with location data
    """
    try:
        logger.info(f"Chat request: {request.message}")

        # Convert Pydantic models to dicts for LLM service
        conversation_history = [
            {"role": msg.role, "content": msg.content}
            for msg in request.conversation_history
        ]

        result = await llm_service.chat(
            message=request.message,
            conversation_history=conversation_history,
            user_location=request.user_location
        )

        return ChatResponse(
            response=result["response"],
            places=result.get("places"),
            map_data=result.get("map_data")
        )

    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat processing error: {str(e)}")

@app.post("/api/places/search")
async def search_places_endpoint(request: PlaceSearchRequest) -> Dict[str, Any]:
    """
    Direct place search endpoint

    Search for places without going through the LLM
    """
    try:
        logger.info(f"Place search: {request.query}")

        places = maps_client.search_places(
            query=request.query,
            location=request.location,
            radius=request.radius,
            place_type=request.place_type
        )

        return {
            "success": True,
            "count": len(places),
            "results": places[:10]  # Limit to 10 results
        }

    except Exception as e:
        logger.error(f"Place search error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Place search error: {str(e)}")

@app.get("/api/places/{place_id}")
async def get_place_details_endpoint(place_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific place
    """
    try:
        logger.info(f"Place details request: {place_id}")

        details = maps_client.get_place_details(place_id)

        if not details:
            raise HTTPException(status_code=404, detail="Place not found")

        return {
            "success": True,
            "result": details
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Place details error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Place details error: {str(e)}")

@app.post("/api/directions")
async def get_directions_endpoint(request: DirectionsRequest) -> Dict[str, Any]:
    """
    Get directions between two locations
    """
    try:
        logger.info(f"Directions request: {request.origin} -> {request.destination}")

        directions = maps_client.get_directions(
            origin=request.origin,
            destination=request.destination,
            mode=request.mode,
            alternatives=request.alternatives
        )

        if not directions:
            raise HTTPException(status_code=404, detail="No route found")

        return {
            "success": True,
            "routes": directions
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Directions error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Directions error: {str(e)}")

@app.get("/api/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "google_maps_configured": bool(settings.GOOGLE_MAPS_API_KEY),
        "llm_configured": bool(settings.LLM_BASE_URL)
    }

@app.get("/api/config")
async def get_config() -> Dict[str, str]:
    """Get frontend configuration"""
    return {
        "google_maps_api_key": settings.GOOGLE_MAPS_API_KEY
    }

# Mount static files directory
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except RuntimeError:
    logger.warning("Static directory not found, skipping static file mounting")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG
    )
