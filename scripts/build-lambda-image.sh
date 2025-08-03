# This script is for local development and testing only.
# It is not used in the automated GitHub Actions deployment pipeline.
docker build -t pmc-complaint-checker -f Dockerfile.lambda .