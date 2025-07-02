#!/bin/bash
set -e

echo "🛡️ Secure PR Guard - Enterprise AI Code Review"
echo "Repository: $GITHUB_REPOSITORY"
echo "Cost Limit: ${INPUT_COST_LIMIT:-0.50}"
echo "Analysis Depth: ${INPUT_ANALYSIS_DEPTH:-standard}"

# Validate required inputs
if [ -z "${INPUT_OPENAI_API_KEY}" ]; then
    echo "❌ Error: openai_api_key is required"
    exit 1
fi

# Set up environment for analysis
export OPENAI_API_KEY="${INPUT_OPENAI_API_KEY}"
export GITHUB_TOKEN="${INPUT_GITHUB_TOKEN}"

# Run the real analysis
echo "🤖 Starting AI-powered security analysis..."
python3 /app/action_runner.py \
    --cost-limit "${INPUT_COST_LIMIT:-0.50}" \
    --analysis-depth "${INPUT_ANALYSIS_DEPTH:-standard}" \
    --output-file "/tmp/results.json"

echo "📊 Analysis results have been set in GitHub Actions outputs"
echo "🎉 Secure PR Guard completed successfully!"
