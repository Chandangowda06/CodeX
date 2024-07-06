from geopy.distance import geodesic

def get_closest(origin, destination, points):
    # Step 1: Find the closest flight to the origin
    closest_to_origin = None
    min_distance_to_origin = float('inf')
    
    for point in points:
        departure_coords = (point.departure_latitude, point.departure_longitude)
        manufacture_to_airport_distance = geodesic(origin, departure_coords).km
        
        if manufacture_to_airport_distance < min_distance_to_origin:
            min_distance_to_origin = manufacture_to_airport_distance
            closest_to_origin = point
    
    # Step 2: Find the closest flight to the destination among the closest flights to the origin
    closest_to_destination = None
    min_distance_to_destination = float('inf')
    
    for point in points:
        if point.departure_latitude == closest_to_origin.departure_latitude and point.departure_longitude == closest_to_origin.departure_longitude:
            arrival_coords = (point.arrival_latitude, point.arrival_longitude)
            airport_to_hospital_distance = geodesic(destination, arrival_coords).km
            
            if airport_to_hospital_distance < min_distance_to_destination:
                min_distance_to_destination = airport_to_hospital_distance
                closest_to_destination = point
    
    return closest_to_destination

# Example usage with dummy data
class Flight:
    def __init__(self, flight_id, departure_latitude, departure_longitude, arrival_latitude, arrival_longitude):
        self.flight_id = flight_id
        self.departure_latitude = departure_latitude
        self.departure_longitude = departure_longitude
        self.arrival_latitude = arrival_latitude
        self.arrival_longitude = arrival_longitude

origin = (12.9716, 77.5946)  # Example coordinates for origin
destination = (28.7041, 77.1025)  # Example coordinates for destination

points = [
    Flight(flight_id=1, departure_latitude=12.9644, departure_longitude=77.5838, arrival_latitude=28.5672, arrival_longitude=77.2273),
    Flight(flight_id=2, departure_latitude=13.1986, departure_longitude=77.7066, arrival_latitude=28.5562, arrival_longitude=77.1000),
    Flight(flight_id=3, departure_latitude=12.9000, departure_longitude=77.6000, arrival_latitude=28.6500, arrival_longitude=77.2000),
    # Add more flight details as needed
]

closest_flight = get_closest(origin, destination, points)
if closest_flight:
    print(f"The closest flight is: {closest_flight.flight_id}")
else:
    print("No suitable flight found.")
