# TradeRamp Production Build Makefile
# This Makefile provides commands for building, testing, and deploying TradeRamp

# Variables
SHELL := /bin/bash
PROJECT_NAME := traderamp
AWS_REGION ?= us-east-1
AWS_PROFILE ?= default
ECR_REPO_NAME := $(PROJECT_NAME)-app
DOCKER_IMAGE := $(PROJECT_NAME):latest
DIST_DIR := dist
BUILD_DIR := build

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

# Default target
.DEFAULT_GOAL := help

# Help command
.PHONY: help
help: ## Show this help message
	@echo "TradeRamp Build System"
	@echo "====================="
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# Dependency checks
.PHONY: check-deps
check-deps: ## Check if required dependencies are installed
	@echo "$(YELLOW)Checking dependencies...$(NC)"
	@command -v node >/dev/null 2>&1 || { echo "$(RED)Node.js is required but not installed.$(NC)" >&2; exit 1; }
	@command -v npm >/dev/null 2>&1 || { echo "$(RED)npm is required but not installed.$(NC)" >&2; exit 1; }
	@command -v python3 >/dev/null 2>&1 || { echo "$(RED)Python 3 is required but not installed.$(NC)" >&2; exit 1; }
	@command -v docker >/dev/null 2>&1 || { echo "$(RED)Docker is required but not installed.$(NC)" >&2; exit 1; }
	@command -v aws >/dev/null 2>&1 || { echo "$(RED)AWS CLI is required but not installed.$(NC)" >&2; exit 1; }
	@echo "$(GREEN)All dependencies are installed!$(NC)"

# Install dependencies
.PHONY: install
install: check-deps ## Install project dependencies
	@echo "$(YELLOW)Installing dependencies...$(NC)"
	@if [ -f package.json ]; then npm install; fi
	@if [ -f requirements.txt ]; then pip3 install -r requirements.txt; fi
	@if [ -f pulumi/requirements.txt ]; then pip3 install -r pulumi/requirements.txt; fi
	@echo "$(GREEN)Dependencies installed!$(NC)"

# Clean build artifacts
.PHONY: clean
clean: ## Clean build artifacts and temporary files
	@echo "$(YELLOW)Cleaning build artifacts...$(NC)"
	@rm -rf $(DIST_DIR) $(BUILD_DIR) node_modules __pycache__ *.pyc .pytest_cache htmlcov .coverage
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)Clean complete!$(NC)"

# Build CSS
.PHONY: build-css
build-css: ## Build and minify CSS
	@echo "$(YELLOW)Building CSS...$(NC)"
	@mkdir -p $(DIST_DIR)/assets/css
	@./scripts/build-production.sh css-only
	@echo "$(GREEN)CSS build complete!$(NC)"

# Build JavaScript
.PHONY: build-js
build-js: ## Build and minify JavaScript
	@echo "$(YELLOW)Building JavaScript...$(NC)"
	@mkdir -p $(DIST_DIR)/assets/js
	@./scripts/build-production.sh js-only
	@echo "$(GREEN)JavaScript build complete!$(NC)"

# Build static assets
.PHONY: build-static
build-static: ## Copy static assets to dist
	@echo "$(YELLOW)Copying static assets...$(NC)"
	@mkdir -p $(DIST_DIR)/assets/{images,fonts}
	@cp -r assets/images/* $(DIST_DIR)/assets/images/
	@cp -r assets/fonts/* $(DIST_DIR)/assets/fonts/
	@cp -f index.html 404.html robots.txt sitemap.xml $(DIST_DIR)/ 2>/dev/null || true
	@echo "$(GREEN)Static assets copied!$(NC)"

# Build for production
.PHONY: build
build: clean install build-css build-js build-static ## Build the project for production
	@echo "$(YELLOW)Processing HTML files...$(NC)"
	@./scripts/build-production.sh html-only
	@echo "$(GREEN)Production build complete!$(NC)"
	@echo "Output directory: $(DIST_DIR)/"

# Run linting
.PHONY: lint
lint: ## Run linting on JavaScript and Python files
	@echo "$(YELLOW)Running linters...$(NC)"
	@if [ -f .eslintrc.json ]; then npx eslint assets/js/*.js --fix; else echo "No ESLint config found, skipping JS lint"; fi
	@if command -v black >/dev/null 2>&1; then black pulumi/ lambda/; fi
	@if command -v pylint >/dev/null 2>&1; then pylint pulumi/ lambda/ || true; fi
	@echo "$(GREEN)Linting complete!$(NC)"

# Run tests
.PHONY: test
test: ## Run all tests
	@echo "$(YELLOW)Running tests...$(NC)"
	@if [ -d tests ]; then python3 -m pytest tests/; else echo "No tests directory found"; fi
	@echo "$(GREEN)Tests complete!$(NC)"

# Validate HTML
.PHONY: validate-html
validate-html: ## Validate HTML files
	@echo "$(YELLOW)Validating HTML...$(NC)"
	@if command -v html5validator >/dev/null 2>&1; then \
		html5validator --root . --match "*.html" --ignore-re "node_modules|dist|build"; \
	else \
		echo "$(YELLOW)html5validator not installed. Install with: pip install html5validator$(NC)"; \
	fi

# Local development server
.PHONY: serve
serve: ## Start local development server
	@echo "$(GREEN)Starting development server on http://localhost:8000$(NC)"
	@cd $(DIST_DIR) && python3 -m http.server 8000

# Docker build
.PHONY: docker-build
docker-build: build ## Build Docker image
	@echo "$(YELLOW)Building Docker image...$(NC)"
	@docker build -t $(DOCKER_IMAGE) .
	@echo "$(GREEN)Docker image built: $(DOCKER_IMAGE)$(NC)"

# Docker run
.PHONY: docker-run
docker-run: ## Run Docker container locally
	@echo "$(YELLOW)Running Docker container...$(NC)"
	@docker run -d -p 8080:80 --name $(PROJECT_NAME) $(DOCKER_IMAGE)
	@echo "$(GREEN)Container running at http://localhost:8080$(NC)"

# Docker stop
.PHONY: docker-stop
docker-stop: ## Stop and remove Docker container
	@echo "$(YELLOW)Stopping Docker container...$(NC)"
	@docker stop $(PROJECT_NAME) 2>/dev/null || true
	@docker rm $(PROJECT_NAME) 2>/dev/null || true
	@echo "$(GREEN)Container stopped$(NC)"

# ECR login
.PHONY: ecr-login
ecr-login: ## Login to AWS ECR
	@echo "$(YELLOW)Logging into AWS ECR...$(NC)"
	@aws ecr get-login-password --region $(AWS_REGION) --profile $(AWS_PROFILE) | \
		docker login --username AWS --password-stdin $$(aws sts get-caller-identity --query Account --output text --profile $(AWS_PROFILE)).dkr.ecr.$(AWS_REGION).amazonaws.com
	@echo "$(GREEN)ECR login successful$(NC)"

# Push to ECR
.PHONY: ecr-push
ecr-push: docker-build ecr-login ## Push Docker image to ECR
	@echo "$(YELLOW)Pushing to ECR...$(NC)"
	@$(eval ACCOUNT_ID := $(shell aws sts get-caller-identity --query Account --output text --profile $(AWS_PROFILE)))
	@$(eval ECR_URI := $(ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/$(ECR_REPO_NAME))
	@docker tag $(DOCKER_IMAGE) $(ECR_URI):latest
	@docker tag $(DOCKER_IMAGE) $(ECR_URI):$$(date +%Y%m%d%H%M%S)
	@docker push $(ECR_URI):latest
	@docker push $(ECR_URI):$$(date +%Y%m%d%H%M%S)
	@echo "$(GREEN)Image pushed to ECR$(NC)"

# Pulumi preview
.PHONY: pulumi-preview
pulumi-preview: ## Preview Pulumi infrastructure changes
	@echo "$(YELLOW)Previewing infrastructure changes...$(NC)"
	@cd pulumi && pulumi preview
	@echo "$(GREEN)Preview complete$(NC)"

# Pulumi deploy
.PHONY: pulumi-deploy
pulumi-deploy: ## Deploy infrastructure with Pulumi
	@echo "$(YELLOW)Deploying infrastructure...$(NC)"
	@cd pulumi && pulumi up --yes
	@echo "$(GREEN)Infrastructure deployed$(NC)"

# Full deployment
.PHONY: deploy
deploy: test build ecr-push pulumi-deploy ## Full deployment (test, build, push, deploy)
	@echo "$(GREEN)Full deployment complete!$(NC)"

# Security scan
.PHONY: security-scan
security-scan: ## Run security scans
	@echo "$(YELLOW)Running security scans...$(NC)"
	@if command -v safety >/dev/null 2>&1; then safety check; else echo "Safety not installed"; fi
	@if command -v bandit >/dev/null 2>&1; then bandit -r pulumi/ lambda/; else echo "Bandit not installed"; fi
	@echo "$(GREEN)Security scan complete$(NC)"

# Performance check
.PHONY: perf-check
perf-check: build ## Check build size and performance metrics
	@echo "$(YELLOW)Checking performance metrics...$(NC)"
	@echo "Build sizes:"
	@du -sh $(DIST_DIR)/assets/css/*.css | sort -h
	@du -sh $(DIST_DIR)/assets/js/*.js | sort -h
	@echo ""
	@echo "Total dist size: $$(du -sh $(DIST_DIR) | cut -f1)"
	@echo "$(GREEN)Performance check complete$(NC)"

# Create environment file template
.PHONY: env-template
env-template: ## Create .env.example file
	@echo "$(YELLOW)Creating .env.example...$(NC)"
	@cat > .env.example <<EOF
# AWS Configuration
AWS_REGION=us-east-1
AWS_PROFILE=default

# Domain Configuration (optional)
DOMAIN_NAME=traderamp.com
CERTIFICATE_ARN=

# Application Configuration
ENVIRONMENT=production
PROJECT_NAME=traderamp

# API Keys (obtain from respective services)
GOOGLE_ANALYTICS_ID=
FACEBOOK_PIXEL_ID=
MAILCHIMP_API_KEY=
MAILCHIMP_LIST_ID=

# Email Configuration
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASS=
FROM_EMAIL=hello@traderamp.com
ADMIN_EMAIL=admin@traderamp.com
EOF
	@echo "$(GREEN).env.example created$(NC)"

# Quick commands
.PHONY: dev
dev: install serve ## Quick development setup

.PHONY: prod
prod: build perf-check ## Production build with checks

.PHONY: clean-all
clean-all: clean docker-stop ## Clean everything including Docker

# Catch-all target
%:
	@echo "$(RED)Unknown target: $@$(NC)"
	@echo "Run 'make help' to see available commands"