"""
Entry point for the ISS Tracker application.
"""

from iss_tracker import ISSTrackerApp


def main():
    """Main entry point."""
    print("🚀 Starting International Space Station Tracker...")
    print("📡 Fetching real-time data from NASA's Open Notify API")
    print("🗺️ Generating interactive maps with Folium")
    print("=" * 50)
    
    try:
        app = ISSTrackerApp()
        app.run()
    except KeyboardInterrupt:
        print("\n👋 Application closed by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
