#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/frontend"
cp ../interfaces/automataeditor.jsx src/AutomataEditor.jsx
npm install
npm run build
