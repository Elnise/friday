#!/bin/bash
set -e

# Start the ollama service
/bin/ollama serve &

# Wait for the service to be fully initialized
sleep 5

# Create the model
/bin/ollama create friday -f /friday-llama3_1
/bin/ollama list
# Run the model
/bin/ollama run friday
tail -f /dev/null
