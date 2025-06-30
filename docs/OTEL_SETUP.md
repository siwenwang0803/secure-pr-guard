# OpenTelemetry Setup Guide

## Configuration

Set these environment variables:

```bash
export OTLP_ENDPOINT="your-grafana-endpoint"
export OTLP_API_KEY="your-api-key"
export OTLP_USERNAME="your-username"
```

## Usage

```python
from otel_helpers import create_otel_instrumentor

instrumentor = create_otel_instrumentor(pr_url)
with instrumentor.instrument_operation("my.operation") as op:
    # Your code here
    op.set_cost_info(cost_data)
```

## Testing

```bash
python -m pytest tests/test_otel_helpers.py -v
coverage run -m pytest tests/
coverage report
```
