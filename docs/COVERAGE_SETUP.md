# Coverage Setup Guide

## Local Testing

```bash
# Run tests with coverage
coverage run -m pytest tests/
coverage report --show-missing
coverage html

# View HTML report
open htmlcov/index.html
```

## Codecov Integration

1. Sign up at codecov.io
2. Connect your GitHub repository
3. Add CODECOV_TOKEN to GitHub secrets
4. Coverage reports will be automatic on CI

## Coverage Targets

- Overall: 85%
- OTEL Helpers: 95%
- Security Rules: 100%
- Agents: 90%
