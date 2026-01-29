.PHONY: build publish clean install dev test

# Build package
build: clean
	uv build

# Publish to PyPI (requires UV_PUBLISH_TOKEN env var or --token flag)
publish: build
	uv publish

# Clean build artifacts
clean:
	rm -rf dist/ build/ *.egg-info

# Install dependencies
install:
	uv sync

# Install Playwright browsers
browsers:
	uv run python -m playwright install chromium

# Run CLI
run:
	uv run vobs $(ARGS)

# Run MCP server
mcp:
	uv run virtuals-tweepy-mcp

# Bump version (usage: make bump v=0.1.2)
bump:
	@if [ -z "$(v)" ]; then echo "Usage: make bump v=0.1.2"; exit 1; fi
	sed -i '' 's/version = ".*"/version = "$(v)"/' pyproject.toml
	@echo "Version bumped to $(v)"

# Release: bump, build, publish (usage: make release v=0.1.2)
release:
	@if [ -z "$(v)" ]; then echo "Usage: make release v=0.1.2"; exit 1; fi
	$(MAKE) bump v=$(v)
	$(MAKE) publish
