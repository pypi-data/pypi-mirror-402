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
1. Install: `pip install mcp-oignon`
2. Configure your AI client:

   **Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json`):
   ```json
   {
     "mcpServers": {
       "oignon": {
         "command": "mcp-oignon"
       }
     }
   }
   ```

   **ChatGPT Desktop** (`~/Library/Application Support/ChatGPT/mcp.json`):
   ```json
   {
     "mcpServers": {
       "oignon": {
         "command": "mcp-oignon"
       }
     }
   }
   ```

   **Codex** (`~/.codex/mcp.toml`):
   ```toml
   [[servers]]
   name = "oignon"
   command = "mcp-oignon"
   ```

3. Restart your AI client

**CLI options**:
- Default: `mcp-oignon` (stdio transport)
- HTTP mode: `mcp-oignon --transport http --host 127.0.0.1 --port 8000`

## Package Distribution

**PyPI** ⚠️ **PUBLISH PENDING**:
- Package name: `mcp-oignon`
- Current version on PyPI: `0.1.1`
- Local version: `0.1.2` (not yet published)
- PyPI URL: https://pypi.org/project/mcp-oignon/
- Installation: `pip install mcp-oignon`
- Build command: `uv build` (creates dist/ with .whl and .tar.gz)
- Publish command: `uv publish` (requires PyPI API token in `UV_PUBLISH_TOKEN` env var, loaded from `.env`)
- Note: PyPI pulls README at publish time, so version bumps are needed to update documentation
- **Status**: v0.1.2 built locally but publish failed/incomplete. Ready to retry: `source .env && rm -rf dist && uv build && uv publish`
- **Dependencies**: Optimized - moved `claude-agent-sdk` to optional `[dev]` dependency (only needed for benchmarks, not core MCP server functionality). Core install now has ~40 packages, mostly from `mcp[cli]` (unavoidable for MCP servers).

**GitHub** ✅ **PUBLISHED**:
- Repository: https://github.com/hballington12/mcp-oignon
- pyproject.toml updated with project URLs (homepage, repository, issues)
- All package metadata committed and published
- README includes setup instructions for Claude Desktop, ChatGPT, and Codex (with TOML format)

**Missing infrastructure**:
- Dockerfile / docker-compose
- CI/CD configuration
- systemd service files

## Status

✅ **Core functionality complete and published**. Package available on PyPI and GitHub. Production deployment infrastructure not yet implemented.
