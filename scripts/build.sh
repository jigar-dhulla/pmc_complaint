#!/bin/bash

# Exit on any error
set -e

# --- Configuration ---
BUILD_DIR="build"
LAMBDA_FUNCTION_ZIP="lambda_function.zip"
PYTHON_FILES=("pmc_complaint_checker_v2.py" "repository.py")
REQUIREMENTS_FILE="requirements.txt"

# --- Main Script ---

# 1. Cleanup previous build artifacts
echo "--- Cleaning up previous build artifacts ---"
rm -rf "$BUILD_DIR" "$LAMBDA_FUNCTION_ZIP"
mkdir -p "$BUILD_DIR"

# 2. Prepare the Lambda function package (for .zip deployment)
echo "--- Creating Lambda function package for non-container deployment ---"
echo "NOTE: This requires a separate Lambda Layer for the browser binaries (Chromium/Chromedriver)."

# Copy Python source files
echo "Copying Python files..."
for file in "${PYTHON_FILES[@]}"; do
    cp "$file" "$BUILD_DIR/"
done

# Copy requirements.txt
echo "Copying $REQUIREMENTS_FILE..."
cp "$REQUIREMENTS_FILE" "$BUILD_DIR/"

# Install dependencies
echo "Installing dependencies..."
python3 -m pip install --implementation cp --python-version 3.13 --only-binary=:all: -t "$BUILD_DIR" -r "$BUILD_DIR/$REQUIREMENTS_FILE"

# Create the Lambda function zip file
echo "Creating $LAMBDA_FUNCTION_ZIP..."
(cd "$BUILD_DIR" && zip -r "../$LAMBDA_FUNCTION_ZIP" .)

echo "--- Lambda function package created successfully ---"
echo "Please ensure you have configured your lambda with the required layers for selenium and chrome"
# 3. Final cleanup
echo "--- Cleaning up build directory ---"
rm -rf "$BUILD_DIR"

echo "--- Build complete! ---"
echo "File created:"
echo "- $LAMBDA_FUNCTION_ZIP"
