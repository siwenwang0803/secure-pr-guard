#!/bin/bash
set -e

echo "🛡️ Starting Secure PR Guard Analysis..."
echo "Repository: $GITHUB_REPOSITORY"
echo "PR Number: $PR_NUMBER"
echo "Analysis Depth: $ANALYSIS_DEPTH"
echo "Cost Limit: $COST_LIMIT USD"

# Validate required inputs
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ Error: OPENAI_API_KEY is required"
    exit 1
fi

if [ -z "$PR_NUMBER" ]; then
    echo "❌ Error: PR_NUMBER is required"
    exit 1
fi

# Set default values
ENABLE_BUDGET_GUARD=${ENABLE_BUDGET_GUARD:-true}
ENABLE_OWASP_SCANNING=${ENABLE_OWASP_SCANNING:-true}
ANALYSIS_DEPTH=${ANALYSIS_DEPTH:-standard}
COST_LIMIT=${COST_LIMIT:-0.50}

# Create GitHub Actions output file
GITHUB_OUTPUT=${GITHUB_OUTPUT:-/tmp/github_output}

# Build PR URL
PR_URL="https://github.com/${GITHUB_REPOSITORY}/pull/${PR_NUMBER}"

echo "📊 Analyzing PR: $PR_URL"

# Export environment variables for the Python script
export OPENAI_API_KEY
export GITHUB_TOKEN
export ENABLE_BUDGET_GUARD
export ENABLE_OWASP_SCANNING
export ANALYSIS_DEPTH
export COST_LIMIT
export SLACK_WEBHOOK
export EXCLUDE_FILES

# Run the analysis with error handling
echo "🤖 Starting AI analysis..."

# Create a temporary results file
RESULTS_FILE="/tmp/analysis_results.json"

# Run the main analysis script
python3 /app/github_action_runner.py \
    --pr-url "$PR_URL" \
    --cost-limit "$COST_LIMIT" \
    --analysis-depth "$ANALYSIS_DEPTH" \
    --output "$RESULTS_FILE" \
    --github-output "$GITHUB_OUTPUT"

# Check if analysis was successful
if [ $? -eq 0 ]; then
    echo "✅ Analysis completed successfully"
    
    # Extract results and set GitHub Actions outputs
    if [ -f "$RESULTS_FILE" ]; then
        # Parse JSON results and set outputs
        ANALYSIS_COST=$(python3 -c "import json; data=json.load(open('$RESULTS_FILE')); print(data.get('analysis_cost', '0.000'))")
        SECURITY_ISSUES=$(python3 -c "import json; data=json.load(open('$RESULTS_FILE')); print(data.get('security_issues_found', 0))")
        OWASP_SCORE=$(python3 -c "import json; data=json.load(open('$RESULTS_FILE')); print(data.get('owasp_compliance_score', 0))")
        SUMMARY=$(python3 -c "import json; data=json.load(open('$RESULTS_FILE')); print(data.get('analysis_summary', 'Analysis completed'))")
        
        # Set GitHub Actions outputs
        echo "analysis_cost=$ANALYSIS_COST" >> "$GITHUB_OUTPUT"
        echo "security_issues_found=$SECURITY_ISSUES" >> "$GITHUB_OUTPUT"
        echo "owasp_compliance_score=$OWASP_SCORE" >> "$GITHUB_OUTPUT"
        echo "analysis_summary=$SUMMARY" >> "$GITHUB_OUTPUT"
        
        echo "📊 Analysis Results:"
        echo "   💰 Cost: \$${ANALYSIS_COST}"
        echo "   🛡️ Security Issues: ${SECURITY_ISSUES}"
        echo "   📋 OWASP Score: ${OWASP_SCORE}%"
        echo "   📝 Summary: ${SUMMARY}"
    else
        echo "⚠️ Warning: Results file not found, using defaults"
        echo "analysis_cost=0.000" >> "$GITHUB_OUTPUT"
        echo "security_issues_found=0" >> "$GITHUB_OUTPUT"
        echo "owasp_compliance_score=0" >> "$GITHUB_OUTPUT"
        echo "analysis_summary=Analysis completed with warnings" >> "$GITHUB_OUTPUT"
    fi
else
    echo "❌ Analysis failed with exit code $?"
    echo "analysis_cost=0.000" >> "$GITHUB_OUTPUT"
    echo "security_issues_found=-1" >> "$GITHUB_OUTPUT"
    echo "owasp_compliance_score=0" >> "$GITHUB_OUTPUT"
    echo "analysis_summary=Analysis failed" >> "$GITHUB_OUTPUT"
    exit 1
fi

echo "🎉 Secure PR Guard analysis completed!"