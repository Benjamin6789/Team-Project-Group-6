#!/usr/bin/env python3
# run_system.py - Script to run both the Django server and data collector

import os
import sys
import subprocess
import time
import signal
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("system.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("system_runner")

# Global variables
processes = []
running = True

def signal_handler(sig, frame):
    """Handle Ctrl+C for graceful shutdown"""
    global running
    logger.info("Shutdown signal received. Stopping all processes...")
    running = False
    stop_all_processes()

# Register the signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def start_django_server():
    """Start the Django web server"""
    logger.info("Starting Django server...")
    # Start Django development server
    django_process = subprocess.Popen(
        [sys.executable, "-u", "manage.py", "runserver", "0.0.0.0:8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    
    logger.info(f"Django server started with PID: {django_process.pid}")
    return django_process

def start_data_collector():
    """Start the data collector script"""
    logger.info("Starting data collector...")
    # Path to the collector script
    collector_path = os.path.join("Get-Data", "collector.py")
    
    # Start collector process
    collector_process = subprocess.Popen(
        [sys.executable, "-u", collector_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    
    logger.info(f"Data collector started with PID: {collector_process.pid}")
    return collector_process

def monitor_process_output(process, process_name):
    """Read and log process output without blocking"""
    output = process.stdout.readline()
    if output:
        logger.info(f"{process_name}: {output.strip()}")
        return True
    return False

def check_process_status(process, process_name):
    """Check if a process is still running"""
    if process.poll() is not None:
        logger.error(f"{process_name} died with return code: {process.returncode}")
        return False
    return True

def stop_all_processes():
    """Stop all running processes"""
    global processes
    
    for process, name in processes:
        if process.poll() is None:  # Process is still running
            logger.info(f"Stopping {name}...")
            process.terminate()
            try:
                # Wait for process to terminate gracefully
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't terminate in time
                logger.warning(f"{name} didn't terminate gracefully, killing...")
                process.kill()

def main():
    """Main function to start and monitor the system components"""
    global processes, running
    
    # Start Django server
    django_process = start_django_server()
    processes.append((django_process, "Django server"))
    
    # Give Django server time to start
    time.sleep(2)
    
    # Start data collector
    collector_process = start_data_collector()
    processes.append((collector_process, "Data collector"))
    
    logger.info("All system components started!")
    print(f"Django server is running at http://localhost:8000/")
    print(f"Access the dashboard at http://localhost:8000/dashboard/")
    print("Press Ctrl+C to stop all components")
    
    # Monitor running processes
    while running:
        for i, (process, name) in enumerate(processes):
            # Check if the process is still running
            if not check_process_status(process, name):
                running = False
                break
            
            # Read process output
            monitor_process_output(process, name)
        
        time.sleep(0.1)  # Short sleep to avoid high CPU usage
    
    # Stop all processes when exiting
    stop_all_processes()
    logger.info("System shutdown complete")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"Fatal error: {str(e)}")
        stop_all_processes()
        sys.exit(1) 