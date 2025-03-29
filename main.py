from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import json
import uvicorn

app = FastAPI()

class VehicleRequest(BaseModel):
    length: int
    quantity: int

class Listing(BaseModel):
    id: str
    length: int
    width: int
    location_id: str
    price_in_cents: int

class SearchResult(BaseModel):
    location_id: str
    listing_ids: List[str]
    total_price_in_cents: int


@app.post("/", response_model=List[SearchResult])
async def search_listings(vehicle_requests: List[VehicleRequest]):
    listings = load_listings()
    vehicles = []

    for req in vehicle_requests:
        for _ in range(req.quantity):
            vehicles.append({"length": req.length, "width": 10})

    locations = {}
    for listing in listings:
        if listing.location_id not in locations:
            locations[listing.location_id] = []
        locations[listing.location_id].append(listing)

    results = []
    for location_id, location_listings in locations.items():
        result = find_cheapest_combination(location_id, location_listings, vehicles)
        if result:
            results.append(result)

    results.sort(key=lambda x: x.total_price_in_cents)

    return results

def load_listings():
    try:
        listings = []
        with open("listings.json", "r") as f:
            for item in json.load(f):
                listing = Listing(
                        id=item["id"],
                        length=item["length"],
                        width=item["width"],
                        location_id=item["location_id"],
                        price_in_cents=item["price_in_cents"]
                        )
                listings.append(listing)
        return listings
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load listings: {str(e)}")

def can_fit(vehicle_length, vehicle_width, listing_length, listing_width):
    return ((vehicle_length <= listing_length and vehicle_width <= listing_width) or 
            (vehicle_length <= listing_width and vehicle_width <= listing_length))

def find_cheapest_combination(location_id, listings, vehicles):
    sorted_listings = sorted(listings, key=lambda x: x.price_in_cents)
    total_cost, listing_ids = find_recursive_solution(vehicles, sorted_listings)

    if total_cost != float('inf'):
        return SearchResult(
                location_id=location_id,
                listing_ids=listing_ids,
                total_price_in_cents=total_cost
                )

    return None

def find_recursive_solution(vehicles_to_place, available_listings, current_cost=0, current_listings=None):
    if current_listings is None:
        current_listings = []

    if not vehicles_to_place:
        return current_cost, current_listings

    if not available_listings:
        return float('inf'), []

    best_cost = float('inf')
    best_listings = []

    vehicle = vehicles_to_place[0]
    remaining_vehicles = vehicles_to_place[1:]

    for i, listing in enumerate(available_listings):
        if can_fit(vehicle["length"], vehicle["width"], listing.length, listing.width):
            new_available = available_listings[:i] + available_listings[i+1:]
            new_cost = current_cost + listing.price_in_cents
            new_listings = current_listings + [listing.id]
            
            total_cost, total_listings = find_recursive_solution(
                remaining_vehicles, 
                new_available,
                new_cost,
                new_listings
                )

            if total_cost < best_cost:
                best_cost = total_cost
                best_listings = total_listings

    return best_cost, best_listings

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
