# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python web scraping application that checks complaint status from the Pune Municipal Corporation (PMC) website. It's designed to run both locally and on AWS Lambda, using Selenium for web automation and MySQL for data persistence.

## Development Environment Setup

### Python Virtual Environment
Always use Python 3.13 with a virtual environment:

```bash
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Local Database
Start the MySQL container for local development:

```bash
docker-compose up -d
```

This starts a MySQL 8.0 container with the `pmc_complaints` database pre-configured.

## Key Commands

### Running the Application
```bash
# Local execution with token numbers
source venv/bin/activate && python pmc_complaint_checker_v2.py T60137 T60268

# Test Lambda function locally with Docker
docker-compose up lambda-app
```

### Docker Operations
```bash
# Build Lambda image for local testing
docker build -t pmc-complaint-checker -f Dockerfile.lambda .

# Start development environment
docker-compose up -d

# Stop containers
docker-compose down
```

## Architecture

### Core Components

- **pmc_complaint_checker_v2.py**: Main application with dual execution modes:
  - Local CLI mode (`main()` function)
  - AWS Lambda mode (`lambda_handler()` function)
- **repository.py**: Database abstraction layer with MySQL implementation
- **Dockerfile.lambda**: Multi-stage build for AWS Lambda deployment

### Data Flow
1. Input validation (token format: T + digits)
2. Chrome WebDriver setup with Lambda-optimized configuration
3. Web scraping of PMC complaint website using Selenium
4. Data extraction from dynamic tables and modals
5. Database persistence via repository pattern
6. JSON output generation (local mode only)

### Database Schema
- **complaints**: Primary complaint data (token, status, description, location, type, category, expected_date)
- **tracking_history**: Action history with foreign key to complaints table

## Environment Variables

Required for both local and Lambda execution:
- `DB_HOST`: MySQL host
- `DB_USER`: MySQL username  
- `DB_PASSWORD`: MySQL password
- `DB_NAME`: Database name (typically "pmc_complaints")

Lambda-specific:
- `CHROME_PATH`: Chrome binary location
- `CHROMEDRIVER_PATH`: ChromeDriver executable location

## AWS Lambda Considerations

### Chrome Configuration
The Lambda environment uses pre-installed Chrome with optimized flags:
- Headless mode with user data isolation
- Fontconfig cache management
- Temporary directory cleanup
- Custom user agent for reduced fingerprinting

### Resource Management
- User data directories use UUID for uniqueness
- Automatic cleanup of temporary Chrome files
- Memory-optimized Chrome options for Lambda constraints

## Deployment

### GitHub Actions CI/CD
Automated deployment to AWS Lambda via GitHub Actions on push to main branch:
- Builds Docker image using `Dockerfile.lambda`
- Pushes to Amazon ECR
- Updates Lambda function with new image

Required GitHub secrets/variables:
- `AWS_ROLE_TO_ASSUME`: IAM role for OIDC authentication
- `AWS_REGION`: Target AWS region
- `ECR_REPOSITORY`: ECR repository name
- `LAMBDA_FUNCTION_NAME`: Lambda function name

### Manual Testing
Use Docker Compose to test Lambda environment locally while connecting to local MySQL instance.

## Lambda Event Format

```json
{
  "tokens": ["T60137", "T60268"]
}
```