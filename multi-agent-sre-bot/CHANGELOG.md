# Changelog

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

