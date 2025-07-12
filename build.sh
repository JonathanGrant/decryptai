#!/bin/bash
cd ui
npm install
npm run build
cd ..
python server.py