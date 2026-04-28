import os
import openrouteservice
from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

ORS_API_KEY = os.getenv("ORS_API_KEY")

if not ORS_API_KEY:
    print("[Navigation] WARNING: ORS_API_KEY not found. Navigation endpoints will be unavailable.")
    client = None
else:
    client = openrouteservice.Client(key=ORS_API_KEY, timeout=10)


class VoiceCommand(BaseModel):
    current_lat: float
    current_lng: float
    voice_destination: str
    dest_lat: Optional[float] = None
    dest_lng: Optional[float] = None


@router.post("/navigate")
async def get_navigation_directions(command: VoiceCommand):
    if client is None:
        raise HTTPException(status_code=503, detail="Navigation service unavailable: ORS_API_KEY not configured")
    try:
        # Resolve destination coordinates
        if command.dest_lat is not None and command.dest_lng is not None:
            dest_lat = command.dest_lat
            dest_lng = command.dest_lng
            dest_name = command.voice_destination
        else:
            geocode_result = client.pelias_search(
                text=command.voice_destination,
                focus_point=[command.current_lng, command.current_lat],
                size=1
            )
            if not geocode_result['features']:
                raise HTTPException(status_code=404, detail="Destination not found")

            dest_coords = geocode_result['features'][0]['geometry']['coordinates']
            dest_name = geocode_result['features'][0]['properties']['label']
            dest_lng, dest_lat = dest_coords[0], dest_coords[1]

        # Build walking route
        route = client.directions(
            coordinates=[[command.current_lng, command.current_lat], [dest_lng, dest_lat]],
            profile='foot-walking',
            format='geojson',
            instructions=True
        )
        if not route['features']:
            raise HTTPException(status_code=404, detail="No route found")

        # Parse route geometry and step instructions
        feature = route['features'][0]
        properties = feature['properties']
        geometry_points = feature['geometry']['coordinates']

        steps = []
        segment = properties['segments'][0]

        for step in segment['steps']:
            start_idx = step['way_points'][0]
            end_idx = step['way_points'][1]

            start_loc = {"lat": geometry_points[start_idx][1], "lng": geometry_points[start_idx][0]}
            end_loc = {"lat": geometry_points[end_idx][1], "lng": geometry_points[end_idx][0]}

            steps.append({
                "instruction": step['instruction'],
                "distance_meters": step['distance'],
                "maneuver": step.get('type', 0),
                "start_location": start_loc,
                "end_location": end_loc
            })

        summary = properties['summary']
        dist_km = summary['distance'] / 1000
        duration_sec = summary['duration']

        hours = int(duration_sec // 3600)
        mins = int((duration_sec % 3600) // 60)
        duration_text = f"{hours}h {mins}m" if hours > 0 else f"{mins}m"

        return {
            "destination": dest_name,
            "total_distance": f"{dist_km:.2f} km",
            "total_duration": duration_text,
            "navigation_steps": steps
        }

    except HTTPException:
        raise  # Re-raise our own 404s as-is
    except openrouteservice.exceptions.ApiError as e:
        print(f"[Navigation] ORS API error: {e}")
        raise HTTPException(status_code=502, detail=f"Routing service error: {str(e)}")
    except Exception as e:
        print(f"[Navigation] Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
