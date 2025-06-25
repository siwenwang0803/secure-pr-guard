# Secure-PR-Guard

**Objective**: Automatically review GitHub Pull Requests using multi-agent + LLM + OWASP LLM Top-10 rules and generate remediation patches.

**Today's Progress**: Completed repository initialization, LangGraph hello_graph, and state snapshot saving.

**Tomorrow's Plan**: Integrate GitHub API, fetch diff; implement Nitpicker v0.1.

## Project Structure

```
secure-pr-guard/
├── hello_graph.py      # LangGraph workflow example
├── requirements.txt    # Python dependencies
└── README.md          # Project documentation
```

## Getting Started

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run example
python hello_graph.py
```