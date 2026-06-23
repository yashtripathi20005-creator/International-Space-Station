"""
Map visualization module for ISS tracker.
Creates interactive maps with Folium.
"""

import folium
from folium import plugins
from datetime import datetime
from typing import Dict, Optional, List
import os
from config import MAP_ZOOM_START, MAP_TILE, MAP_OUTPUT_FILE, ISS_MARKER_COLOR


class ISSMapVisualizer:
    """Creates and manages interactive maps for ISS tracking."""
    
    def __init__(self):
        self.map = None
        self.iss_marker = None
        self.trail_points = []
        self.trail_line = None
        self.current_position = None
    
    def create_base_map(self) -> folium.Map:
        """Create a base map centered on the world view."""
        self.map = folium.Map(
            location=[0, 0],
            zoom_start=MAP_ZOOM_START,
            tiles=MAP_TILE,
            control_scale=True
        )
        
        # Add layer control
        folium.LayerControl().add_to(self.map)
        
        return self.map
    
    def update_iss_position(self, position_data: Dict, 
                           astronaut_count: int = 0) -> folium.Map:
        """
        Update the ISS position on the map.
        
        Args:
            position_data: Dictionary with latitude and longitude
            astronaut_count: Number of astronauts on board
        """
        if not self.map:
            self.create_base_map()
        
        lat = position_data['latitude']
        lon = position_data['longitude']
        timestamp = position_data['timestamp']
        
        # Update current position
        self.current_position = (lat, lon)
        
        # Add or update trail
        self.trail_points.append([lat, lon])
        if len(self.trail_points) > 100:  # Keep last 100 points
            self.trail_points.pop(0)
        
        # Remove old trail line if exists
        if self.trail_line:
            self.trail_line.remove()
        
        # Add new trail line
        if len(self.trail_points) > 1:
            self.trail_line = folium.PolyLine(
                self.trail_points,
                color="blue",
                weight=2,
                opacity=0.5,
                popup="ISS Trail (last 100 positions)"
            )
            self.trail_line.add_to(self.map)
        
        # Remove old marker if exists
        if self.iss_marker:
            self.iss_marker.remove()
        
        # Create popup text
        popup_text = f"""
        <div style="font-family: Arial, sans-serif;">
            <h3 style="color: {ISS_MARKER_COLOR};">🚀 International Space Station</h3>
            <p><b>📍 Location:</b><br>
            Latitude: {lat:.4f}°<br>
            Longitude: {lon:.4f}°</p>
            <p><b>🕐 Time:</b><br>
            {timestamp.strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
            <p><b>👨‍🚀 Astronauts:</b> {astronaut_count}</p>
            <p><b>🔄 Speed:</b> ~28,000 km/h</p>
        </div>
        """
        
        # Create ISS icon with custom image
        iss_icon = folium.Icon(
            color="red",
            icon="rocket",
            prefix="fa"
        )
        
        # Add marker at ISS position
        self.iss_marker = folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_text, max_width=300),
            tooltip="Click for ISS Info",
            icon=iss_icon
        )
        self.iss_marker.add_to(self.map)
        
        # Add a circle to show approximate coverage area
        folium.Circle(
            location=[lat, lon],
            radius=500000,  # 500km radius
            color='red',
            fill=True,
            fillOpacity=0.1,
            popup='ISS Coverage Area'
        ).add_to(self.map)
        
        # Add fullscreen plugin
        plugins.Fullscreen().add_to(self.map)
        
        return self.map
    
    def add_ground_track(self, positions: List[Dict]) -> None:
        """Add a ground track for the ISS."""
        if not self.map:
            self.create_base_map()
        
        if not positions:
            return
        
        # Create a heatmap of positions
        heat_data = [[pos['latitude'], pos['longitude']] for pos in positions]
        if heat_data:
            plugins.HeatMap(
                heat_data,
                radius=15,
                blur=10,
                max_zoom=1,
                name='ISS Heatmap'
            ).add_to(self.map)
    
    def add_marker_for_location(self, latitude: float, longitude: float, 
                               label: str, color: str = 'blue') -> None:
        """Add a custom marker to the map."""
        if not self.map:
            self.create_base_map()
        
        folium.Marker(
            location=[latitude, longitude],
            popup=label,
            icon=folium.Icon(color=color)
        ).add_to(self.map)
    
    def save_map(self, filename: Optional[str] = None) -> str:
        """Save the map to an HTML file."""
        if not self.map:
            self.create_base_map()
        
        if not filename:
            filename = MAP_OUTPUT_FILE
        
        self.map.save(filename)
        return filename
    
    def get_map_html(self) -> str:
        """Get the map as HTML string."""
        if not self.map:
            self.create_base_map()
        
        return self.map.get_root().render()
