import googlemaps
from typing import List, Dict, Any, Optional
from app.config import settings

class GoogleMapsClient:
    def __init__(self):
        self.client = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)

    def search_places(
        self,
        query: str,
        location: Optional[str] = None,
        radius: int = 5000,
        place_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for places using Google Places API

        Args:
            query: Search query (e.g., "restaurants near me")
            location: Location as string or lat/lng
            radius: Search radius in meters (default 5000m = 5km)
            place_type: Type of place (e.g., 'restaurant', 'cafe')

        Returns:
            List of place results
        """
        try:
            # Use text search for more flexible queries
            results = self.client.places(
                query=query,
                location=location,
                radius=radius,
                type=place_type
            )

            return results.get('results', [])
        except Exception as e:
            print(f"Error searching places: {e}")
            return []

    def get_place_details(self, place_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific place

        Args:
            place_id: Google Place ID

        Returns:
            Place details or None
        """
        try:
            result = self.client.place(place_id=place_id)
            return result.get('result')
        except Exception as e:
            print(f"Error getting place details: {e}")
            return None

    def get_directions(
        self,
        origin: str,
        destination: str,
        mode: str = "driving",
        alternatives: bool = True
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get directions between two locations

        Args:
            origin: Starting location (address or lat/lng)
            destination: Ending location (address or lat/lng)
            mode: Travel mode (driving, walking, bicycling, transit)
            alternatives: Whether to provide alternative routes

        Returns:
            List of route options or None
        """
        try:
            result = self.client.directions(
                origin=origin,
                destination=destination,
                mode=mode,
                alternatives=alternatives
            )
            return result
        except Exception as e:
            print(f"Error getting directions: {e}")
            return None

    def geocode(self, address: str) -> Optional[Dict[str, Any]]:
        """
        Convert address to coordinates

        Args:
            address: Address string

        Returns:
            Geocoding result or None
        """
        try:
            result = self.client.geocode(address)
            return result[0] if result else None
        except Exception as e:
            print(f"Error geocoding address: {e}")
            return None

    def reverse_geocode(self, lat: float, lng: float) -> Optional[str]:
        """
        Convert coordinates to address

        Args:
            lat: Latitude
            lng: Longitude

        Returns:
            Address string or None
        """
        try:
            result = self.client.reverse_geocode((lat, lng))
            return result[0]['formatted_address'] if result else None
        except Exception as e:
            print(f"Error reverse geocoding: {e}")
            return None

# Singleton instance
maps_client = GoogleMapsClient()
