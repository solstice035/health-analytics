#!/usr/bin/env python3
"""
Health Analytics Dashboard Server

Serves the dashboard via HTTP server and opens it in the browser.
Solves the CORS issue when opening dashboard/index.html directly.

Usage:
    python serve.py                    # Start on port 8080
    python serve.py --port 3000        # Start on custom port
    python serve.py --no-browser       # Don't open browser automatically
    python serve.py --help             # Show help
"""

import http.server
import socketserver
import webbrowser
import argparse
import sys
import signal
from pathlib import Path
from typing import Optional


class HealthDashboardHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP handler for serving the dashboard."""

    def __init__(self, *args, **kwargs):
        # Serve from dashboard directory
        dashboard_dir = Path(__file__).parent / "dashboard"
        super().__init__(*args, directory=str(dashboard_dir), **kwargs)

    def log_message(self, format, *args):
        """Custom log message format."""
        # Make logs more readable
        if '200' in str(args):
            status = '\033[92m✓\033[0m'  # Green checkmark
        elif '404' in str(args):
            status = '\033[91m✗\033[0m'  # Red X
        else:
            status = '\033[93m→\033[0m'  # Yellow arrow

        sys.stdout.write(f"{status} {self.address_string()} - {format % args}\n")


def find_available_port(preferred_port: int = 8080, max_attempts: int = 10) -> Optional[int]:
    """
    Find an available port starting from preferred_port.

    Args:
        preferred_port: Port to try first
        max_attempts: Maximum number of ports to try

    Returns:
        Available port number or None if all attempts failed
    """
    for port in range(preferred_port, preferred_port + max_attempts):
        try:
            with socketserver.TCPServer(("", port), HealthDashboardHandler) as test_server:
                return port
        except OSError:
            continue
    return None


def start_server(port: int = 8080, open_browser: bool = True) -> int:
    """
    Start the dashboard HTTP server.

    Args:
        port: Port to run server on
        open_browser: Whether to open browser automatically

    Returns:
        0 on success, 1 on failure
    """
    dashboard_dir = Path(__file__).parent / "dashboard"

    if not dashboard_dir.exists():
        print(f"\033[91m✗ Dashboard directory not found: {dashboard_dir}\033[0m")
        return 1

    index_file = dashboard_dir / "index.html"
    if not index_file.exists():
        print(f"\033[91m✗ Dashboard index.html not found: {index_file}\033[0m")
        return 1

    # Check if port is available
    original_port = port
    port = find_available_port(port)

    if port is None:
        print(f"\033[91m✗ Could not find available port (tried {original_port}-{original_port + 9})\033[0m")
        return 1

    if port != original_port:
        print(f"\033[93m⚠ Port {original_port} in use, using port {port} instead\033[0m")

    try:
        # Create server
        with socketserver.TCPServer(("", port), HealthDashboardHandler) as httpd:
            url = f"http://localhost:{port}"

            # Setup graceful shutdown
            def signal_handler(signum, frame):
                print(f"\n\033[93m→ Shutting down server...\033[0m")
                httpd.shutdown()
                sys.exit(0)

            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)

            # Print startup message
            print("\033[92m" + "=" * 70 + "\033[0m")
            print("\033[92m  🍎 Health Analytics Dashboard Server\033[0m")
            print("\033[92m" + "=" * 70 + "\033[0m")
            print(f"\n  \033[1mDashboard URL:\033[0m {url}")
            print(f"  \033[1mServing from:\033[0m {dashboard_dir}")
            print(f"\n  \033[90mPress Ctrl+C to stop the server\033[0m\n")
            print("\033[92m" + "=" * 70 + "\033[0m\n")

            # Open browser
            if open_browser:
                print(f"→ Opening dashboard in browser...\n")
                webbrowser.open(url)

            # Start serving
            print(f"→ Server running on {url}")
            print(f"→ Access logs:\n")
            httpd.serve_forever()

    except OSError as e:
        if "Address already in use" in str(e):
            print(f"\033[91m✗ Port {port} is already in use\033[0m")
            print(f"\033[93m💡 Try: python serve.py --port {port + 1}\033[0m")
        else:
            print(f"\033[91m✗ Error starting server: {e}\033[0m")
        return 1
    except KeyboardInterrupt:
        print(f"\n\033[93m→ Server stopped by user\033[0m")
        return 0
    except Exception as e:
        print(f"\033[91m✗ Unexpected error: {e}\033[0m")
        return 1

    return 0


def main():
    """Main entry point for the server."""
    parser = argparse.ArgumentParser(
        description="Start the Health Analytics Dashboard server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python serve.py                    Start server on port 8080
  python serve.py --port 3000        Start server on port 3000
  python serve.py --no-browser       Start without opening browser

The dashboard must be accessed via HTTP (not file://) to avoid CORS issues.
        """
    )

    parser.add_argument(
        '--port', '-p',
        type=int,
        default=8080,
        help='Port to run server on (default: 8080)'
    )

    parser.add_argument(
        '--no-browser',
        action='store_true',
        help='Do not open browser automatically'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='Health Analytics Dashboard Server 1.0.0'
    )

    args = parser.parse_args()

    # Check if dashboard data exists
    dashboard_data_dir = Path(__file__).parent / "dashboard" / "data"
    if not dashboard_data_dir.exists() or not any(dashboard_data_dir.glob("*.json")):
        print("\033[93m⚠ Warning: Dashboard data not found\033[0m")
        print(f"Run: \033[1mpython3 scripts/generate_dashboard_data.py\033[0m\n")

    return start_server(port=args.port, open_browser=not args.no_browser)


if __name__ == "__main__":
    sys.exit(main())
