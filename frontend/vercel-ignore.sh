#!/bin/bash

# Only build if frontend files changed
# Exit 1 = Build, Exit 0 = Skip build

if git diff --quiet HEAD^ HEAD -- ../frontend; then
  # No frontend changes
  echo "🔵 No frontend changes detected - skipping build"
  exit 0
else
  # Frontend changed
  echo "🟢 Frontend changes detected - proceeding with build"
  exit 1
fi
