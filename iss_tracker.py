"""
Main ISS Tracker application with GUI.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import webbrowser
import os
from datetime import datetime
from typing import Optional

from data_fetcher import ISSDataFetcher
from map_visualizer import ISSMapVisualizer
from config import UPDATE_INTERVAL, MAP_OUTPUT_FILE


class ISSTrackerApp:
    """Main GUI application for tracking the ISS."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🚀 International Space Station Tracker")
        self.root.geometry("1200x700")
        self.root.minsize(900, 600)
        
        # Initialize components
        self.fetcher = ISSDataFetcher()
        self.map_visualizer = ISSMapVisualizer()
        self.update_running = False
        self.update_thread = None
        self.current_position = None
        self.astronauts = []
        self.pass_predictions = []
        
        # Setup GUI
        self.setup_gui()
        
        # Initial data fetch
        self.update_data()
        
        # Bind close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_gui(self):
        """Create the GUI layout."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=3)
        main_frame.rowconfigure(0, weight=1)
        
        # Left panel - Information
        info_frame = ttk.LabelFrame(main_frame, text="📊 ISS Information", padding="10")
        info_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        info_frame.columnconfigure(0, weight=1)
        
        # Position info
        self.position_text = scrolledtext.ScrolledText(
            info_frame, 
            height=8, 
            width=35,
            font=("Courier", 10),
            wrap=tk.WORD
        )
        self.position_text.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Astronaut list
        ttk.Label(info_frame, text="👨‍🚀 Astronauts On Board:", font=("Arial", 10, "bold")).grid(
            row=1, column=0, sticky=tk.W, pady=(0, 5)
        )
        self.astronaut_listbox = tk.Listbox(
            info_frame,
            height=6,
            width=35,
            font=("Arial", 9)
        )
        self.astronaut_listbox.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Pass predictions
        ttk.Label(info_frame, text="🔭 Next Passes (Your Location):", font=("Arial", 10, "bold")).grid(
            row=3, column=0, sticky=tk.W, pady=(0, 5)
        )
        self.pass_listbox = tk.Listbox(
            info_frame,
            height=4,
            width=35,
            font=("Arial", 9)
        )
        self.pass_listbox.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Controls
        control_frame = ttk.LabelFrame(info_frame, text="🎮 Controls", padding="10")
        control_frame.grid(row=5, column=0, sticky=(tk.W, tk.E))
        control_frame.columnconfigure(0, weight=1)
        control_frame.columnconfigure(1, weight=1)
        
        self.update_btn = ttk.Button(
            control_frame,
            text="🔄 Update Now",
            command=self.manual_update,
            width=15
        )
        self.update_btn.grid(row=0, column=0, padx=(0, 5), pady=5)
        
        self.auto_update_btn = ttk.Button(
            control_frame,
            text="⏸️ Pause Auto-Update",
            command=self.toggle_auto_update,
            width=15
        )
        self.auto_update_btn.grid(row=0, column=1, padx=(5, 0), pady=5)
        
        self.view_map_btn = ttk.Button(
            control_frame,
            text="🗺️ View Full Map",
            command=self.open_map,
            width=15
        )
        self.view_map_btn.grid(row=1, column=0, padx=(0, 5), pady=5)
        
        self.refresh_astros_btn = ttk.Button(
            control_frame,
            text="👥 Refresh Astronauts",
            command=self.update_astronauts,
            width=15
        )
        self.refresh_astros_btn.grid(row=1, column=1, padx=(5, 0), pady=5)
        
        # Status
        self.status_label = ttk.Label(
            info_frame,
            text="🟢 Ready",
            font=("Arial", 9)
        )
        self.status_label.grid(row=6, column=0, sticky=tk.W, pady=(10, 0))
        
        # Right panel - Map (using a Frame for the map)
        map_frame = ttk.LabelFrame(main_frame, text="🗺️ ISS Location Map", padding="10")
        map_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        map_frame.columnconfigure(0, weight=1)
        map_frame.rowconfigure(0, weight=1)
        
        # Use a Tkinter Frame for the map (WebView would need additional integration)
        # For simplicity, we'll display a map as HTML in a text area
        self.map_display_frame = ttk.Frame(map_frame)
        self.map_display_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.map_display_frame.columnconfigure(0, weight=1)
        self.map_display_frame.rowconfigure(0, weight=1)
        
        # Text widget to display map info (or we could embed a browser)
        self.map_info_text = scrolledtext.ScrolledText(
            self.map_display_frame,
            height=10,
            width=60,
            font=("Courier", 10),
            wrap=tk.WORD
        )
        self.map_info_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.map_info_text.insert(tk.END, "Map will be generated and displayed in your browser.\n")
        self.map_info_text.insert(tk.END, "Click 'View Full Map' to open the interactive map.")
        self.map_info_text.config(state=tk.DISABLED)
    
    def update_data(self):
        """Update all data in the background."""
        if self.update_running:
            return
        
        self.update_running = True
        self.status_label.config(text="🔄 Updating data...")
        
        # Fetch data in thread
        thread = threading.Thread(target=self._fetch_and_update, daemon=True)
        thread.start()
    
    def _fetch_and_update(self):
        """Fetch data and update GUI (runs in separate thread)."""
        try:
            # Get position
            position = self.fetcher.get_current_position()
            if position:
                self.current_position = position
                self.root.after(0, self.update_position_display, position)
            
            # Get astronauts
            astronauts = self.fetcher.get_astronauts()
            if astronauts:
                self.astronauts = astronauts
                self.root.after(0, self.update_astronaut_display, astronauts)
            
            # Get pass predictions (default location: Kennedy Space Center)
            # You can change these coordinates
            lat, lon = 28.5729, -80.6489  # Kennedy Space Center
            if position:
                lat, lon = position['latitude'], position['longitude']
            
            passes = self.fetcher.get_next_passes(lat, lon, count=5)
            if passes:
                self.pass_predictions = passes
                self.root.after(0, self.update_passes_display, passes)
            
            # Update map
            if position:
                astronaut_count = len(astronauts) if astronauts else 0
                self.root.after(0, self.update_map, position, astronaut_count)
            
            self.root.after(0, self.update_status, f"✅ Updated at {datetime.now().strftime('%H:%M:%S')}")
            
        except Exception as e:
            self.root.after(0, self.update_status, f"❌ Error: {str(e)}")
        finally:
            self.update_running = False
    
    def update_position_display(self, position):
        """Update the position text widget."""
        message = self.fetcher.format_position_message(position)
        self.position_text.config(state=tk.NORMAL)
        self.position_text.delete(1.0, tk.END)
        self.position_text.insert(1.0, message)
        self.position_text.config(state=tk.DISABLED)
    
    def update_astronaut_display(self, astronauts):
        """Update the astronaut listbox."""
        self.astronaut_listbox.delete(0, tk.END)
        for astronaut in astronauts:
            self.astronaut_listbox.insert(tk.END, f"👨‍🚀 {astronaut['name']}")
    
    def update_passes_display(self, passes):
        """Update the pass predictions listbox."""
        self.pass_listbox.delete(0, tk.END)
        for i, pass_data in enumerate(passes[:4], 1):
            time_str = pass_data['risetime'].strftime('%H:%M:%S UTC')
            duration = pass_data['duration']
            self.pass_listbox.insert(tk.END, f"#{i}: {time_str} ({duration}s)")
    
    def update_map(self, position, astronaut_count):
        """Update the map visualization."""
        try:
            self.map_visualizer.update_iss_position(position, astronaut_count)
            map_file = self.map_visualizer.save_map()
            
            # Update map info text
            self.map_info_text.config(state=tk.NORMAL)
            self.map_info_text.delete(1.0, tk.END)
            self.map_info_text.insert(tk.END, f"🗺️ Map updated at {datetime.now().strftime('%H:%M:%S')}\n")
            self.map_info_text.insert(tk.END, f"📍 Position: {position['latitude']:.4f}°, {position['longitude']:.4f}°\n")
            self.map_info_text.insert(tk.END, f"👨‍🚀 Astronauts: {astronaut_count}\n\n")
            self.map_info_text.insert(tk.END, "💡 Click 'View Full Map' to open interactive map.")
            self.map_info_text.insert(tk.END, "\n\n🔄 Map saved to: " + map_file)
            self.map_info_text.config(state=tk.DISABLED)
            
        except Exception as e:
            self.map_info_text.config(state=tk.NORMAL)
            self.map_info_text.delete(1.0, tk.END)
            self.map_info_text.insert(tk.END, f"❌ Error updating map: {str(e)}")
            self.map_info_text.config(state=tk.DISABLED)
    
    def update_status(self, message):
        """Update the status label."""
        self.status_label.config(text=message)
    
    def manual_update(self):
        """Manually trigger an update."""
        if not self.update_running:
            self.update_data()
        else:
            messagebox.showinfo("Info", "Update already in progress")
    
    def toggle_auto_update(self):
        """Toggle automatic updates."""
        if self.update_thread and self.update_thread.is_alive():
            self.update_running = False
            self.auto_update_btn.config(text="▶️ Start Auto-Update")
            self.status_label.config(text="⏸️ Auto-update paused")
        else:
            self.auto_update_btn.config(text="⏸️ Pause Auto-Update")
            self.start_auto_update()
    
    def start_auto_update(self):
        """Start automatic updates in the background."""
        def auto_update_loop():
            while self.update_running:
                self._fetch_and_update()
                # Wait for next update
                import time
                time.sleep(UPDATE_INTERVAL / 1000)
        
        self.update_running = True
        self.update_thread = threading.Thread(target=auto_update_loop, daemon=True)
        self.update_thread.start()
    
    def update_astronauts(self):
        """Refresh astronaut list."""
        self.status_label.config(text="🔄 Fetching astronauts...")
        thread = threading.Thread(target=self._fetch_astronauts_only, daemon=True)
        thread.start()
    
    def _fetch_astronauts_only(self):
        """Fetch only astronaut data."""
        try:
            astronauts = self.fetcher.get_astronauts()
            if astronauts:
                self.astronauts = astronauts
                self.root.after(0, self.update_astronaut_display, astronauts)
                self.root.after(0, self.update_status, f"👥 Astronauts updated ({len(astronauts)} on board)")
            else:
                self.root.after(0, self.update_status, "❌ Failed to fetch astronaut data")
        except Exception as e:
            self.root.after(0, self.update_status, f"❌ Error: {str(e)}")
    
    def open_map(self):
        """Open the map in a web browser."""
        try:
            if os.path.exists(MAP_OUTPUT_FILE):
                webbrowser.open(MAP_OUTPUT_FILE)
                self.status_label.config(text=f"🌐 Map opened in browser")
            else:
                messagebox.showwarning("No Map", "Map not found. Please update data first.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open map: {str(e)}")
    
    def on_closing(self):
        """Handle application closing."""
        self.update_running = False
        self.root.destroy()
    
    def run(self):
        """Run the application."""
        # Start auto-update by default
        self.start_auto_update()
        self.root.mainloop()


if __name__ == "__main__":
    app = ISSTrackerApp()
    app.run()
