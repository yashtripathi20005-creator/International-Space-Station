"""
Configuration settings for the ISS Tracker application.
"""

# API Endpoints
ISS_NOW_API = "http://api.open-notify.org/iss-now.json"
ISS_PEOPLE_API = "http://api.open-notify.org/astros.json"
ISS_PASS_API = "http://api.open-notify.org/iss-pass.json"

# Map settings
MAP_ZOOM_START = 2
MAP_TILE = "OpenStreetMap"

# Update interval in milliseconds
UPDATE_INTERVAL = 5000  # 5 seconds

# Color settings
ISS_MARKER_COLOR = "red"
ISS_POPUP_COLOR = "#ff0000"

# File paths
MAP_OUTPUT_FILE = "iss_location.html"
