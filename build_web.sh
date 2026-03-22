#!/bin/bash
cd frontend/packages/web
npm install
npm run build --if-present || npx vite build
