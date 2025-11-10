#!/bin/bash
# run.sh - FastAPI production setup script with Hypercorn

set -e  # Exit on error

# Configuration
APP_MODULE="src.main:app"
PORT=8000
WORKERS=1
MAX_REQUESTS=10000
GRACEFUL_TIMEOUT=60
VENV_DIR="venv"
REQUIREMENTS_FILE="requirements.txt"

# Function to print colored messages
print_message() {
    echo -e "\033[1;34m$1\033[0m"
}

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install it first."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    print_message "Creating Python virtual environment..."
    python3 -m venv $VENV_DIR
fi

# Activate virtual environment
print_message "Activating virtual environment..."
source $VENV_DIR/bin/activate

# Upgrade pip
print_message "Upgrading pip..."
pip install --upgrade pip

# Install requirements if the file exists
if [ -f "$REQUIREMENTS_FILE" ]; then
    print_message "Installing requirements..."
    pip install -r $REQUIREMENTS_FILE
    pip install hypercorn uvloop
    # pip install hypercorn fastapi uvloop fastapi-async-sqlalchemy aiosqlite aio-pika aiohttp aiormq
else
    print_message "No requirements.txt found...."
fi

# Validate the app module exists
# if ! python3 -c "from src.main import app" &> /dev/null; then
#     echo "Error: Could not find $APP_MODULE. Please ensure your app structure is correct."
#     exit 1
# fi

# Run the application with Hypercorn
print_message "Starting Hypercorn server with production settings..."
exec hypercorn $APP_MODULE \
    --workers $WORKERS \
    --bind 0.0.0.0:$PORT \
    --worker-class uvloop \
    --max-requests $MAX_REQUESTS \
    --graceful-timeout $GRACEFUL_TIMEOUT \
    --access-logfile - \
    --error-logfile -

# Deactivate virtual environment when done
deactivate