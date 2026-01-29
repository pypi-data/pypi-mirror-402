---
name: project-memory
description: Core knowledge about citation-graph-mcp (oignon), an MCP server for exploring academic literature and building citation networks using OpenAlex API.
---

# Project Memory: citation-graph-mcp 🧅

## Overview

**citation-graph-mcp** (nicknamed "oignon") is an MCP server that enables Claude agents to explore academic literature and build citation networks using the OpenAlex API.

## Current Status

✅ **Core functionality complete**:
- Full OpenAlex API integration with smart batching
- Graph building algorithm with dual ranking:
  - **Roots**: Historical lineage (papers this cites)
  - **Branches**: Future influence (papers citing this)
- In-memory storage with full-text search
- All 8 MCP tools implemented and working
- CLI with stdio/http transport options

## Key Technical Details

- **API**: OpenAlex for academic paper metadata
- **Storage**: In-memory with full-text search capabilities
- **Graph Structure**: Dual-direction citation tracking (backward/forward)
- **Transport**: Supports both stdio and HTTP

## Project Purpose

Enable AI agents to systematically explore academic research by:
1. Starting from a seed paper
2. Building citation networks in both directions
3. Ranking papers by historical importance and future influence
4. Providing search and navigation capabilities

## Installation & Usage

**For end users**:
1. Install: `pip install .` or `uv pip install .`
2. Configure Claude Desktop by adding to `~/Library/Application Support/Claude/claude_desktop_config.json`:
   ```json
   {
     "mcpServers": {
       "oignon": {
         "command": "mcp-oignon"
       }
     }
   }
   ```
3. Restart Claude Desktop

**CLI options**:
- Default: `mcp-oignon` (stdio transport)
- HTTP mode: `mcp-oignon --transport http --host 127.0.0.1 --port 8000`

## Package Distribution

**PyPI setup** ✅:
- pyproject.toml configured with full metadata (author: John P. McCrae <john@mccr.ae>)
- Build command: `uv build` (creates dist/ with .whl and .tar.gz)
- Publish command: `uv publish` (publishes to PyPI)
- Package name: `citation-graph-mcp`
- **NOT yet published** - awaiting GitHub setup first

**GitHub status**:
- No remote configured yet
- User plans to push to GitHub first, then will provide repo URL
- Once repo URL available: update pyproject.toml with project URLs, then proceed to PyPI

**Next Steps**:
1. User will push code to GitHub
2. User will provide GitHub repo URL
3. Update pyproject.toml with project URLs
4. Build and publish to PyPI

**Missing infrastructure**:
- Dockerfile / docker-compose
- Comprehensive README (currently just one-liner)
- CI/CD configuration
- systemd service files

## Status

Core functionality complete and usable. **Awaiting GitHub push before PyPI publication**. Production deployment infrastructure not yet implemented.
