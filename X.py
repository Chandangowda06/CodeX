import networkx as nx
from geopy.distance import geodesic
import requests
import polyline
import folium
from .models import Flight, Truck
from manufacture.models import Manufacture
from hospital.models import Hospital

def get_closest(origin, destination, points):
    closest_to_origin = None
    min_distance_to_origin = float('inf')
    
    for point in points:
        departure_coords = (point.departure_latitude, point.departure_longitude)
        manufacture_to_airport_distance = geodesic(origin, departure_coords).km
        
        if manufacture_to_airport_distance < min_distance_to_origin:
            min_distance_to_origin = manufacture_to_airport_distance
            closest_to_origin = point
    
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

def get_osrm_route(origin, destination):
    base_url = 'http://router.project-osrm.org/route/v1/driving/'
    origin_str = f"{origin[1]},{origin[0]}"  
    destination_str = f"{destination[1]},{destination[0]}"  
    url = f"{base_url}{origin_str};{destination_str}?overview=full"
    response = requests.get(url)
    data = response.json()
    if data['code'] == 'Ok':
        distance = data['routes'][0]['distance'] / 1000  # distance in km
        route_geometry = data['routes'][0]['geometry']
        return distance, route_geometry
    else:
        raise Exception(f"Error fetching route from OSRM: {data['code']}")

def route_optimization(manufacturing_site, destination_hospital):
    G = nx.DiGraph()
    direct_road_distance, direct_road_geometry = get_osrm_route(manufacturing_site, destination_hospital)
    print(f"distance {direct_road_distance} geometry {direct_road_geometry}" )
    if direct_road_distance < 200:
        print("less than 50s")
        G.add_edge(f'{manufacturing_site[2]}', f'{destination_hospital[2]}', weight=direct_road_distance, geometry=direct_road_geometry)
        print(G)
    else:
        closest_transport = get_closest((manufacturing_site[0], manufacturing_site[1]),(destination_hospital[0], destination_hospital[1]),  Flight.objects.all())
        road_distance_to_transport, road_geometry_to_transport = get_osrm_route(manufacturing_site, (closest_transport.departure_latitude, closest_transport.departure_longitude))
        G.add_edge(f'{manufacturing_site[2]}', closest_transport, weight=road_distance_to_transport, geometry=road_geometry_to_transport)
        
        # closest_transport_to_hospital = get_closest(destination_hospital, Flight.objects.all())
        air_distance = geodesic((closest_transport.departure_latitude, closest_transport.departure_longitude), (closest_transport.arrival_latitude, closest_transport.arrival_longitude)).km
        G.add_edge(closest_transport, closest_transport, weight=air_distance, geometry=None)
        
        road_distance_to_hospital, road_geometry_to_hospital = get_osrm_route((closest_transport.arrival_latitude, closest_transport.arrival_longitude), destination_hospital)
        G.add_edge(closest_transport, f'{destination_hospital[2]}', weight=road_distance_to_hospital, geometry=road_geometry_to_hospital)
    
    shortest_path = nx.shortest_path(G, source=f'{manufacturing_site[2]}', target=f'{destination_hospital[2]}', weight='weight', method='dijkstra')
    print(f"shortest path:{shortest_path}")
    total_distance = nx.shortest_path_length(G, source=f'{manufacturing_site[2]}', target=f'{destination_hospital[2]}', weight='weight', method='dijkstra')
    edge_geometries = nx.get_edge_attributes(G, 'geometry')
    print("total distance:", total_distance)
    print("total edge_geometries:", edge_geometries)
    return shortest_path, total_distance, edge_geometries


def plot_route(manufacturing_site, destination_hospital, shortest_path, edge_geometries, total_distance):
    mid_lat = (manufacturing_site[0] + destination_hospital[0]) / 2
    mid_lon = (manufacturing_site[1] + destination_hospital[1]) / 2
    m = folium.Map(location=[mid_lat, mid_lon], zoom_start=3)
    print("mid Lat", mid_lat)
    # Add markers for manufacturing site and hospital
    folium.Marker(location=(manufacturing_site[0], manufacturing_site[1]), popup=f'{manufacturing_site[2]}', icon=folium.Icon(color='blue')).add_to(m)
    folium.Marker(location=(destination_hospital[0], destination_hospital[1]), popup=f'{destination_hospital[2]}', icon=folium.Icon(color='red')).add_to(m)
    
    # Find transportation nodes along the route
    transportation_nodes = [node for node in shortest_path if isinstance(node, Flight)]
    print("nodes:",transportation_nodes)
    # Display flight ID only for the first and last transportation nodes (start and end of the route)
    if len(transportation_nodes) >= 1:
        start_transport = transportation_nodes[0]
        print("start node:",start_transport)
        # end_transport = transportation_nodes[-1]
        
        folium.Marker(location=(start_transport.departure_latitude, start_transport.departure_longitude), popup=f"Flight ID: {start_transport.flight_id}", icon=folium.Icon(color='green')).add_to(m)
        folium.Marker(location=(start_transport.arrival_latitude, start_transport.arrival_longitude), popup=f"Flight ID: {start_transport.flight_id}", icon=folium.Icon(color='green')).add_to(m)
        folium.PolyLine(locations=[(start_transport.departure_latitude, start_transport.departure_longitude),(start_transport.arrival_latitude, start_transport.arrival_longitude)], color='blue', weight=2.5, opacity=1, popup=f"{total_distance} km").add_to(m)

    # Plot polylines for the shortest path
    print("shortest Path:", shortest_path)
    for i in range(len(shortest_path) - 1):
        start = shortest_path[i]
        end = shortest_path[i + 1]
        
        if start == f'{manufacturing_site[2]}':
            start_coords = (manufacturing_site[0], manufacturing_site[1])
        elif start == f'{destination_hospital[2]}':
            start_coords = (destination_hospital[0], destination_hospital[1])
        else:
            start_coords = (start.departure_latitude, start.departure_longitude)
        
        if end == f'{manufacturing_site[2]}':
            end_coords =  (manufacturing_site[0], manufacturing_site[1])
        elif end == f'{destination_hospital[2]}':
            end_coords = (destination_hospital[0], destination_hospital[1])
        else:
            end_coords = (end.departure_latitude, end.departure_longitude)
        
        if (start, end) in edge_geometries and edge_geometries[(start, end)]:
            coordinates = polyline.decode(edge_geometries[(start, end)])
            folium.PolyLine(locations=coordinates, color='blue', weight=2.5, opacity=1, popup=f"{total_distance} km").add_to(m)
        else:
            coordinates = [(start_coords[0], start_coords[1]), (end_coords[0], end_coords[1])]
            folium.PolyLine(locations=coordinates, color='blue', weight=2.5, opacity=1, popup=f"{total_distance} km").add_to(m)
    
    return m._repr_html_()
