from config import API_KEY
import os
import webbrowser  # Import webbrowser
from tkinter import messagebox  # Import messagebox
from roadInfo import count_nearby_roads
from roadInfo import get_road_name_or_landmark
from roadInfo import ensure_unique_road_name
from trafficData import determine_traffic_intensities
import tkinter as tk
from trafficLightGUI import create_traffic_lights
import logging

# Set up logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

def submit(latitude_entry, longitude_entry, box_id_entry, range_entry, life_cycle_entry, max_snap_points_entry):
    latitude = float(latitude_entry.get())
    longitude = float(longitude_entry.get())

    radius = float(range_entry.get())

    print(f"Location: Latitude: {latitude}, Longitude: {longitude}, Radius: {radius} meters")

    # Create the URL for the HTML file with the necessary parameters for location and radius
    html_content = f"""
    <html>
    <head>
      <title>Google Maps - Draw Circle with Traffic</title>
      <script src="https://maps.googleapis.com/maps/api/js?key={API_KEY}"></script>
      <script>
        function initMap() {{
          var map = new google.maps.Map(document.getElementById('map'), {{
            zoom: 15,
            center: {{lat: {latitude}, lng: {longitude}}}
          }});

          var trafficLayer = new google.maps.TrafficLayer();
          trafficLayer.setMap(map); // Add traffic layer

          var circle = new google.maps.Circle({{
            strokeColor: '#FF0000',
            strokeOpacity: 0.8,
            strokeWeight: 2,
            fillColor: '#FF0000',
            fillOpacity: 0.35,
            map: map,
            center: {{lat: {latitude}, lng: {longitude}}},
            radius: {radius}
          }});
        }}
      </script>
    </head>
    <body onload="initMap()">
      <div id="map" style="height: 100vh; width: 100%;"></div>
    </body>
    </html>
    """

    # Save the HTML content to a file
    file_name = "map_with_circle_and_traffic.html"
    try:
        with open(file_name, "w") as file:
            file.write(html_content)
        # Open the HTML file in the default browser
        webbrowser.open_new_tab(f"file://{os.path.abspath(file_name)}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open the map file: {str(e)}")
    else:
        messagebox.showinfo("Success", f"Map file created and opened: {file_name}")

    traffic_box_id = box_id_entry.get()
    range_m = float(range_entry.get())
    life_cycle_seconds = int(life_cycle_entry.get())
    max_snap_points = int(max_snap_points_entry.get())

    print("Location (Latitude, Longitude):", latitude, longitude)
    print("Traffic Box ID:", traffic_box_id)
    print("Range of Device (in meters):", range_m)
    print("Total Life Cycle (in seconds):", life_cycle_seconds)

    google_maps_url = f"https://www.google.com/maps/@{latitude},{longitude},15z"
    webbrowser.open(google_maps_url)

    # Get the nearest roads
    try:
        snapped_points, num_roads = count_nearby_roads(latitude, longitude, API_KEY, range_m, max_snap_points=max_snap_points)
    except Exception as e:
        logging.error(f"Error fetching nearby roads: {str(e)}")
        messagebox.showerror("Error", f"Failed to fetch nearby roads: {str(e)}")
        return

    if num_roads > 0:
        road_names = []
        used_names = set()  # To keep track of used names

        for point in snapped_points:
            try:
                road_name = get_road_name_or_landmark(point['location']['latitude'], point['location']['longitude'], API_KEY)
            except Exception as e:
                logging.error(f"Error getting road name for point {point}: {str(e)}")
                road_name = f"Unknown Road {point['location']['latitude']}, {point['location']['longitude']}"

            # Ensure uniqueness
            road_name = ensure_unique_road_name(road_name, used_names)

            used_names.add(road_name)
            road_names.append(road_name)

        # Create UI labels for roads
        ui_labels = [f"Road {chr(65+i)}" for i in range(num_roads)]

        # Get traffic intensities for each road
        try:
            traffic_intensities = determine_traffic_intensities(snapped_points, API_KEY)
        except Exception as e:
            logging.error(f"Error determining traffic intensities: {str(e)}")
            traffic_intensities = ["Unknown"] * num_roads

        # Print road details (name, coordinates, intensity) in the console with UI labels
        print(f"\nFound {num_roads} roads near the specified location:")
        for i, point in enumerate(snapped_points):
            road_coords = (point['location']['latitude'], point['location']['longitude'])
            traffic_intensity = traffic_intensities[i]
            print(f"{ui_labels[i]} ({road_names[i]}): Coordinates: {road_coords} | Traffic Intensity: {traffic_intensity}")

        # Start the traffic light simulation (with generic labels for UI)
        root = tk.Tk()
        root.title("Traffic Light Simulation")
        create_traffic_lights(root, road_names, snapped_points, API_KEY, life_cycle_seconds)
        root.mainloop()
    else:
        print("No roads found near the specified location.")