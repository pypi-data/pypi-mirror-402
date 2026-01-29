#!/usr/bin/env python3
"""Startup script for MANTA Benchmark UI.

This script starts both the FastAPI backend and Streamlit frontend.
"""

import subprocess
import sys
import time
import os
from pathlib import Path

# Get the directory containing this script
SCRIPT_DIR = Path(__file__).parent.resolve()
BACKEND_DIR = SCRIPT_DIR / "backend"
FRONTEND_DIR = SCRIPT_DIR / "frontend"


def check_requirements():
    """Check if required packages are installed."""
    required = ['fastapi', 'uvicorn', 'streamlit', 'sqlalchemy', 'plotly']
    missing = []

    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)

    if missing:
        print(f"Missing required packages: {', '.join(missing)}")
        print(f"\nInstall them with:")
        print(f"  pip install -r {SCRIPT_DIR}/requirements.txt")
        return False

    return True


def start_backend():
    """Start the FastAPI backend server."""
    print("Starting FastAPI backend on http://localhost:8000 ...")

    # Change to project root so manta imports work
    os.chdir(SCRIPT_DIR.parent)

    return subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn",
            "manta_benchmark.backend.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )


def start_frontend():
    """Start the Streamlit frontend."""
    print("Starting Streamlit frontend on http://localhost:8501 ...")

    return subprocess.Popen(
        [
            sys.executable, "-m", "streamlit",
            "run", str(FRONTEND_DIR / "app.py"),
            "--server.port", "8501",
            "--server.headless", "true"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )


def main():
    """Main entry point."""
    print("=" * 50)
    print("MANTA Benchmark UI")
    print("=" * 50)
    print()

    # Check requirements
    if not check_requirements():
        sys.exit(1)

    # Initialize database
    print("Initializing database...")
    from backend.database import init_db
    init_db()
    print("Database initialized.")
    print()

    # Start services
    backend_process = None
    frontend_process = None

    try:
        backend_process = start_backend()
        time.sleep(2)  # Wait for backend to start

        frontend_process = start_frontend()
        time.sleep(2)  # Wait for frontend to start

        print()
        print("=" * 50)
        print("Services started successfully!")
        print()
        print("Backend API:  http://localhost:8000")
        print("API Docs:     http://localhost:8000/docs")
        print("Frontend UI:  http://localhost:8501")
        print()
        print("Press Ctrl+C to stop all services")
        print("=" * 50)
        print()

        # Wait for processes
        while True:
            # Check if processes are still running
            if backend_process.poll() is not None:
                print("Backend process terminated unexpectedly!")
                break
            if frontend_process.poll() is not None:
                print("Frontend process terminated unexpectedly!")
                break
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nShutting down...")

    finally:
        # Cleanup
        if backend_process:
            backend_process.terminate()
            backend_process.wait()
        if frontend_process:
            frontend_process.terminate()
            frontend_process.wait()

        print("Services stopped.")


if __name__ == "__main__":
    main()
