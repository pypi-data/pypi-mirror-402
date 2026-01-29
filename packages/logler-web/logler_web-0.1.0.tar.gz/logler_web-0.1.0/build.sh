#!/bin/bash
# Build logler-web package for PyPI
set -e

echo "Building frontend..."
pnpm build

echo "Copying frontend to package..."
rm -rf src/logler_web/static
cp -r dist src/logler_web/static

echo "Building Python package..."
uv build -o dist-pkg

echo "Done! Package at dist-pkg/"
