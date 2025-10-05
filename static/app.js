// Global state
let conversationHistory = [];
let userLocation = null;
let googleMapsApiKey = '';

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    // Fetch Google Maps API key
    try {
        const configResponse = await fetch('/api/config');
        const config = await configResponse.json();
        googleMapsApiKey = config.google_maps_api_key;
    } catch (error) {
        console.error('Failed to load config:', error);
    }

    // Enable Enter key to send messages
    document.getElementById('user-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // Try to get user's location
    getUserLocation();

    // Add welcome message
    addMessage('assistant', 'Hi! I can help you find restaurants, cafes, parks, and other places nearby. I can also provide directions. What are you looking for?');
});

// Get user's current location
function getUserLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                userLocation = `${position.coords.latitude},${position.coords.longitude}`;
                console.log('User location obtained:', userLocation);
            },
            (error) => {
                console.log('Location access denied:', error);
            }
        );
    }
}

// Send message to API
async function sendMessage() {
    const input = document.getElementById('user-input');
    const message = input.value.trim();

    if (!message) return;

    // Add user message to chat
    addMessage('user', message);
    input.value = '';

    // Disable send button
    const sendBtn = document.getElementById('send-btn');
    sendBtn.disabled = true;

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                conversation_history: conversationHistory,
                user_location: userLocation
            })
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        const data = await response.json();

        // Add assistant response to chat
        addMessage('assistant', data.response);

        // Update conversation history
        conversationHistory.push({ role: 'user', content: message });
        conversationHistory.push({ role: 'assistant', content: data.response });

        // Display places if available
        if (data.places && data.places.length > 0) {
            displayPlaces(data.places);
            displayMap(data.places);
        }

        // Display map data if available
        if (data.map_data && data.map_data.length > 0) {
            displayDirections(data.map_data[0]);
        }

    } catch (error) {
        console.error('Error:', error);
        addMessage('assistant', 'Sorry, I encountered an error. Please try again.');
    } finally {
        sendBtn.disabled = false;
    }
}

// Quick message buttons
function quickMessage(message) {
    document.getElementById('user-input').value = message;
    sendMessage();
}

// Add message to chat
function addMessage(role, content) {
    const messagesContainer = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;
    messageDiv.textContent = content;

    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Display places in the UI
function displayPlaces(places) {
    const placesList = document.getElementById('places-list');
    placesList.innerHTML = '<h3 style="margin-bottom: 15px;">📍 Recommended Places</h3>';

    places.forEach(place => {
        const card = createPlaceCard(place);
        placesList.appendChild(card);
    });
}

// Create place card element
function createPlaceCard(place) {
    const card = document.createElement('div');
    card.className = 'place-card';

    const name = place.name || 'Unknown Place';
    const rating = place.rating || 'N/A';
    const address = place.formatted_address || place.vicinity || 'Address not available';
    const isOpen = place.opening_hours?.open_now;

    card.innerHTML = `
        <h3>${name}</h3>
        ${rating !== 'N/A' ? `<div class="place-rating">⭐ ${rating}</div>` : ''}
        <div class="place-address">📍 ${address}</div>
        ${isOpen !== undefined ? `
            <div class="place-status ${isOpen ? '' : 'closed'}">
                ${isOpen ? '🟢 Open now' : '🔴 Closed'}
            </div>
        ` : ''}
    `;

    // Add click handler to get directions
    card.addEventListener('click', () => {
        if (userLocation) {
            getDirections(userLocation, address);
        } else {
            alert('Please enable location access to get directions');
        }
    });

    return card;
}

// Display map with places
function displayMap(places) {
    const mapContainer = document.getElementById('map');

    if (places.length === 0) {
        mapContainer.innerHTML = '<div class="map-placeholder"><p>No locations to display</p></div>';
        return;
    }

    // Get first place coordinates
    const firstPlace = places[0];
    const lat = firstPlace.geometry?.location?.lat;
    const lng = firstPlace.geometry?.location?.lng;

    if (!lat || !lng) {
        console.error('No coordinates available for map');
        return;
    }

    // Create markers parameter for multiple places
    let markersParam = places
        .filter(p => p.geometry?.location?.lat && p.geometry?.location?.lng)
        .map(p => `${p.geometry.location.lat},${p.geometry.location.lng}`)
        .join('|');

    // Use Google Maps Embed API
    const embedUrl = `https://www.google.com/maps/embed/v1/place?key=${googleMapsApiKey}&q=${lat},${lng}&zoom=14`;

    mapContainer.innerHTML = `
        <iframe
            src="${embedUrl}"
            allowfullscreen
            loading="lazy">
        </iframe>
    `;
}

// Get directions
async function getDirections(origin, destination) {
    try {
        const response = await fetch('/api/directions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                origin: origin,
                destination: destination,
                mode: 'driving'
            })
        });

        const data = await response.json();

        if (data.success && data.routes.length > 0) {
            displayDirections(data.routes[0]);
        }

    } catch (error) {
        console.error('Directions error:', error);
    }
}

// Display directions on map
function displayDirections(route) {
    const mapContainer = document.getElementById('map');

    const startLat = route.legs[0].start_location.lat;
    const startLng = route.legs[0].start_location.lng;
    const endLat = route.legs[0].end_location.lat;
    const endLng = route.legs[0].end_location.lng;

    // Use Google Maps Embed Directions API
    const embedUrl = `https://www.google.com/maps/embed/v1/directions?key=${googleMapsApiKey}&origin=${startLat},${startLng}&destination=${endLat},${endLng}&mode=driving`;

    mapContainer.innerHTML = `
        <iframe
            src="${embedUrl}"
            allowfullscreen
            loading="lazy">
        </iframe>
    `;

    // Add directions summary to chat
    const duration = route.legs[0].duration.text;
    const distance = route.legs[0].distance.text;
    addMessage('assistant', `🚗 Route: ${distance}, approximately ${duration}`);
}
