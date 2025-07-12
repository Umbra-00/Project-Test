# CI/CD Pipeline Documentation

## Overview

This project uses GitLab CI/CD to automatically build, test, and deploy the Umbra Educational Data Platform to Render. The pipeline ensures code quality, runs comprehensive tests, and deploys only when all checks pass.

## Pipeline Stages

### 1. Build Stage
- **Purpose**: Install dependencies and prepare the application
- **Actions**:
  - Sets up Python 3.11.4 environment
  - Creates virtual environment
  - Installs requirements from `requirements.txt`
  - Caches dependencies for faster subsequent builds

### 2. Test Stage
- **Purpose**: Ensure code quality and functionality
- **Actions**:
  - Runs unit tests with pytest
  - Generates test coverage reports
  - Performs code style checks with Black
  - Runs linting with Flake8
  - Generates JUnit XML for test reporting
  - Produces coverage reports in XML format

### 3. Deploy Stage
- **Purpose**: Deploy to Render when tests pass
- **Actions**:
  - Triggers Render deployment via webhook
  - Only runs on main branch
  - Requires all tests to pass

## Required Environment Variables

Set these variables in your GitLab CI/CD settings:

```bash
RENDER_DEPLOY_HOOK=https://api.render.com/deploy/srv-xxxxx?key=xxxxx
```

## Test Configuration

### pytest.ini
- Configured to run tests from `tests/` directory
- Generates coverage reports automatically
- Excludes non-source directories from coverage
- Produces JUnit XML for CI integration

### .flake8
- Sets maximum line length to 88 characters (Black compatible)
- Excludes common non-source directories
- Configures appropriate ignore rules for common patterns

## Code Quality Standards

### Formatting
- **Black**: Python code formatter with line length of 88
- **isort**: Import sorting with Black profile

### Linting
- **Flake8**: Style guide enforcement
- **Bandit**: Security vulnerability scanning

### Testing
- **pytest**: Test framework with coverage reporting
- **pytest-cov**: Coverage plugin for pytest
- **pytest-mock**: Mocking utilities

## Pre-commit Hooks

Install pre-commit hooks to ensure code quality before committing:

```bash
pip install pre-commit
pre-commit install
```

This will run the following checks automatically:
- Trailing whitespace removal
- End-of-file fixing
- YAML validation
- Large file checks
- Merge conflict detection
- Debug statement detection
- Black formatting
- Flake8 linting
- Import sorting with isort
- Security scanning with Bandit

## Local Development

### Running Tests
```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_api_endpoints.py

# Run tests with verbose output
pytest -v
```

### Code Formatting
```bash
# Format code with Black
black src/

# Sort imports
isort src/

# Check code style
flake8 src/
```

### Security Scanning
```bash
# Run security checks
bandit -r src/
```

## Troubleshooting

### Common Issues

1. **Missing Dependencies**: Ensure all required packages are in `requirements.txt`
2. **Test Failures**: Check that all mocks are properly configured
3. **Coverage Issues**: Verify test coverage meets minimum requirements
4. **Deployment Failures**: Check that `RENDER_DEPLOY_HOOK` is correctly set

### Debugging CI/CD

- Check GitLab CI/CD pipeline logs for detailed error messages
- Verify that all environment variables are set correctly
- Ensure that the Render webhook URL is valid and accessible

## Best Practices

1. **Always run tests locally** before pushing changes
2. **Use pre-commit hooks** to catch issues early
3. **Write comprehensive tests** for new features
4. **Keep dependencies updated** and compatible
5. **Monitor pipeline performance** and optimize as needed

## Deployment Process

1. **Push to main branch** triggers the pipeline
2. **Build stage** installs dependencies
3. **Test stage** runs all quality checks
4. **Deploy stage** triggers Render deployment (if tests pass)
5. **Render** automatically deploys the new version

The entire process typically takes 3-5 minutes for a successful deployment.
