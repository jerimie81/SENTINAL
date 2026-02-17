#!/bin/bash
# This script sets up the development environment.

echo "Creating virtual environment..."
python3 -m venv venv

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing project in editable mode with dev dependencies..."
pip install -e .[dev]

echo "Setup complete. Run 'source venv/bin/activate' to use the environment."
