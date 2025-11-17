# Changelog

# [1.1.0] - 2024-11-17

### Added
- Runtime LLM selection with support for Nebius, OpenAI (ChatGPT), Anthropic (Claude), and Qwen models
- Shared `llm.factory` utilities for building provider-specific model instances
- Anthropic client dependency and configuration fields (`ANTHROPIC_API_KEY`, `LLM_PROVIDER`, `LLM_MODEL`)
- Streamlit sidebar controls to pick providers/models and upload Anthropic keys
- Streamlit Cloud docs/quick start updates covering new secrets
- Natural language → `kubectl` translation that executes commands via the Kubernetes MCP server (with local kubectl fallback)

### Changed
- All agents (troubleshooting, monitoring, automation, knowledge, coordinator) now consume the shared LLM factory
- API and daemon flows honor `LLM_PROVIDER`/`LLM_MODEL` environment overrides

## [1.0.0] - 2024-11-16

### Added
- **Natural Language Operations**: Execute cluster operations using plain English
- **Chaos Scenario Management**: Detect and remove chaos scenarios from namespaces
- **Action Summaries**: Detailed summaries of all cluster operations
- **Streamlit UI with API Key Management**: Configure API keys directly in UI
- **Kubernetes Configuration Selection**: Choose kubeconfig source in UI
- **Independent Lifecycles**: Cluster and bot managed separately
- **Kind Cluster Support**: Auto-detect and connect to Kind clusters
- **Multi-Agent Coordination**: Enhanced routing for cluster operations

### Enhanced
- **Automation Agent**: Added chaos detection and removal capabilities
- **Coordinator Agent**: Improved natural language command parsing
- **Kubernetes Connector**: Added chaos scenario listing and removal methods
- **UI**: Added Kubernetes configuration section with auto-detection

### Fixed
- Import errors for MCP and agent modules
- Relative import issues in Streamlit UI
- Agent initialization with optional dependencies
- Package structure for proper module loading

### Documentation
- Added NATURAL_LANGUAGE_OPS.md
- Added STREAMLIT_WORKFLOW.md
- Added UI_GUIDE.md
- Updated README.md with new features
- Added comprehensive setup guides

