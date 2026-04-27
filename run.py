"""
Unified entry point for all services.

Usage:
    python run.py                     # Run both services
    python run.py --service vision    # Run only Vision Player
    python run.py --service filter    # Run only Asset Filter
    python run.py --help              # Show help
"""
import argparse
import multiprocessing
import uvicorn
import sys
import os

# Ensure project root is in Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_vision_player(host, port, reload):
    """Start the Vision Player service."""
    print(f"[VisionPlayer] Starting on {host}:{port}")
    uvicorn.run(
        "services.vision_player.app:app",
        host=host,
        port=port,
        reload=reload,
    )


def run_asset_filter(host, port, reload):
    """Start the Asset Filter service."""
    print(f"[AssetFilter] Starting on {host}:{port}")
    uvicorn.run(
        "services.asset_filter.app:app",
        host=host,
        port=port,
        reload=reload,
    )


def main():
    # Load settings for defaults
    from config.settings import get_settings
    settings = get_settings()

    parser = argparse.ArgumentParser(
        description="WRAMS Modular Service Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py                          # Both services (production)
  python run.py --reload                 # Both services (dev mode)
  python run.py --service vision         # Vision Player only
  python run.py --service filter         # Asset Filter only
  python run.py --service vision --port 9000  # Custom port
        """,
    )
    parser.add_argument(
        "--service",
        choices=["vision", "filter", "both"],
        default="both",
        help="Which service to run (default: both)",
    )
    parser.add_argument(
        "--host",
        default=settings.SERVER_HOST,
        help=f"Bind address (default: {settings.SERVER_HOST})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Override port (only for single service mode)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )

    args = parser.parse_args()

    profile = settings.load_profile()
    print("========================================")
    print(f"  Service Profile: {settings.SERVICE_PROFILE}")
    print(f"  Display Name:    {profile.get('display_name', 'N/A')}")
    print(f"  Database:        {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    print("========================================")

    if args.service == "vision":
        port = args.port or settings.VISION_PLAYER_PORT
        run_vision_player(args.host, port, args.reload)

    elif args.service == "filter":
        port = args.port or settings.ASSET_FILTER_PORT
        run_asset_filter(args.host, port, args.reload)

    else:
        # Run both services in parallel
        p1 = multiprocessing.Process(
            target=run_vision_player,
            args=(args.host, settings.VISION_PLAYER_PORT, args.reload),
        )
        p2 = multiprocessing.Process(
            target=run_asset_filter,
            args=(args.host, settings.ASSET_FILTER_PORT, args.reload),
        )
        p1.start()
        p2.start()

        try:
            p1.join()
            p2.join()
        except KeyboardInterrupt:
            print("\nShutting down services...")
            p1.terminate()
            p2.terminate()
            p1.join()
            p2.join()
            print("All services stopped.")


if __name__ == "__main__":
    main()
