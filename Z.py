def plot_route(manufacturing_site, destination_hospital, shortest_path, edge_geometries, total_distance):
    mid_lat = (manufacturing_site[0] + destination_hospital[0]) / 2
    mid_lon = (manufacturing_site[1] + destination_hospital[1]) / 2
    m = folium.Map(location=[mid_lat, mid_lon], zoom_start=3)
    print("mid Lat", mid_lat)
   
    folium.Marker(location=(manufacturing_site[0], manufacturing_site[1]), popup=f'{manufacturing_site[2]}', icon=folium.Icon(color='blue')).add_to(m)
    folium.Marker(location=(destination_hospital[0], destination_hospital[1]), popup=f'{destination_hospital[2]}', icon=folium.Icon(color='red')).add_to(m)
    
   
    transportation_nodes = [node for node in shortest_path if isinstance(node, Flight)]
    print("nodes:",transportation_nodes)
   
    if len(transportation_nodes) >= 1:
        start_transport = transportation_nodes[0]
        print("start node:",start_transport)
        
        
        folium.Marker(location=(start_transport.departure_latitude, start_transport.departure_longitude), popup=f"Flight ID: {start_transport.flight_id}", icon=folium.Icon(color='green')).add_to(m)
        folium.Marker(location=(start_transport.arrival_latitude, start_transport.arrival_longitude), popup=f"Flight ID: {start_transport.flight_id}", icon=folium.Icon(color='green')).add_to(m)
        folium.PolyLine(locations=[(start_transport.departure_latitude, start_transport.departure_longitude),(start_transport.arrival_latitude, start_transport.arrival_longitude)], color='blue', weight=2.5, opacity=1, popup=f"{total_distance} km").add_to(m)

    
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
