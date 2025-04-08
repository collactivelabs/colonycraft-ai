#!/bin/bash

# Build functions
npm run build

# Deploy functions with environment variables
firebase deploy --only functions --env-file .env.yaml
