"""
Data fetching module for ISS tracker.
Handles all API calls to get ISS data.
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from config import ISS_NOW_API, ISS_PEOPLE_API, ISS_PASS_API


class ISSDataFetcher:
    """Fetches real-time data about the International Space Station."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ISS-Tracker/1.0'
        })
    
    def get_current_position(self) -> Optional[Dict]:
        """
        Get the current position of the ISS.
        
        Returns:
            Dictionary with 'timestamp', 'latitude', 'longitude' or None if error.
        """
        try:
            response = self.session.get(ISS_NOW_API, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('message') != 'success':
                return None
            
            position = data['iss_position']
            return {
                'timestamp': datetime.fromtimestamp(data['timestamp']),
                'latitude': float(position['latitude']),
                'longitude': float(position['longitude']),
                'raw_data': data
            }
        except requests.RequestException as e:
            print(f"Error fetching ISS position: {e}")
            return None
        except (KeyError, ValueError) as e:
            print(f"Error parsing ISS position data: {e}")
            return None
    
    def get_astronauts(self) -> Optional[List[Dict]]:
        """
        Get the list of astronauts currently on the ISS.
        
        Returns:
            List of astronaut dictionaries or None if error.
        """
        try:
            response = self.session.get(ISS_PEOPLE_API, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('message') != 'success':
                return None
            
            astronauts = []
            for person in data.get('people', []):
                if person.get('craft', '').lower() == 'iss':
                    astronauts.append({
                        'name': person.get('name', 'Unknown'),
                        'craft': person.get('craft', 'ISS')
                    })
            
            return astronauts
        except requests.RequestException as e:
            print(f"Error fetching astronaut data: {e}")
            return None
    
    def get_next_passes(self, latitude: float, longitude: float, 
                       count: int = 5) -> Optional[List[Dict]]:
        """
        Get the next ISS passes for a given location.
        
        Args:
            latitude: Observer's latitude
            longitude: Observer's longitude
            count: Number of passes to return
            
        Returns:
            List of pass dictionaries or None if error.
        """
        try:
            params = {
                'lat': latitude,
                'lon': longitude,
                'n': count
            }
            response = self.session.get(ISS_PASS_API, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('message') != 'success':
                return None
            
            passes = []
            for pass_data in data.get('response', []):
                passes.append({
                    'risetime': datetime.fromtimestamp(pass_data['risetime']),
                    'duration': pass_data['duration']
                })
            
            return passes
        except requests.RequestException as e:
            print(f"Error fetching pass predictions: {e}")
            return None
    
    def format_position_message(self, position_data: Dict) -> str:
        """Format position data into a readable message."""
        return (
            f"📍 ISS Current Position\n"
            f"🕐 Time: {position_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            f"🌍 Latitude: {position_data['latitude']:.4f}°\n"
            f"🌍 Longitude: {position_data['longitude']:.4f}°\n"
            f"🌊 Status: {'Over water' if self.is_over_water(position_data) else 'Over land'}"
        )
    
    @staticmethod
    def is_over_water(position_data: Dict) -> bool:
        """
        Rough estimate if ISS is over water.
        This is a simplified check - a real implementation would use 
        land/water dataset.
        """
        # Simplified: if latitude is between -60 and 60, assume mostly water
        # This is not accurate but gives a rough idea
        lat = abs(position_data['latitude'])
        if lat < 60:
            # Rough water detection based on longitude
            lon = position_data['longitude'] % 360
            # Pacific Ocean approximation
            if 130 < lon < 290:
                return True
            # Atlantic Ocean approximation
            if 340 < lon < 360 or 0 < lon < 20:
                return True
            # Indian Ocean approximation
            if 40 < lon < 100:
                return True
        return False
