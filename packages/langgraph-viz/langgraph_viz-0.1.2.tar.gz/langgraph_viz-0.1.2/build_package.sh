#!/bin/bash
set -e

# Directories
PROJECT_ROOT=$(pwd)
FRONTEND_DIR="frontend"

echo "Building frontend..."
cd $FRONTEND_DIR
npm install
npm run build
cd $PROJECT_ROOT

echo "Building python package..."
python3 -m pip install --upgrade build || echo "Installing build failed, assuming already installed or user will manage"
python3 -m build

echo "Done! Package is in dist/"
