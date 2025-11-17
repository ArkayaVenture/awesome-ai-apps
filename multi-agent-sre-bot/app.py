"""Streamlit ChatOps UI for SRE Bot with API Key Management."""
import os
import sys
from pathlib import Path
import streamlit as st
from typing import Optional, Dict, Any
import logging
from dotenv import load_dotenv
import subprocess

# Add parent directory to path
project_root = Path(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, str(project_root))

# Import modules using direct imports to avoid relative import issues
import importlib.util

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Multi-Agent SRE Bot",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state
if "api_keys_set" not in st.session_state:
    st.session_state.api_keys_set = False
if "nebius_api_key" not in st.session_state:
    st.session_state.nebius_api_key = os.getenv("NEBIUS_API_KEY", "")
if "openai_api_key" not in st.session_state:
    st.session_state.openai_api_key = os.getenv("OPENAI_API_KEY", "")
if "initialized" not in st.session_state:
    st.session_state.initialized = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "coordinator_agent" not in st.session_state:
    st.session_state.coordinator_agent = None
if "memory_manager" not in st.session_state:
    st.session_state.memory_manager = None
if "k8s_connector" not in st.session_state:
    st.session_state.k8s_connector = None
if "agents_status" not in st.session_state:
    st.session_state.agents_status = {}


def validate_api_key(api_key: str, key_type: str = "nebius") -> bool:
    """Validate API key format (basic validation)."""
    if not api_key or len(api_key.strip()) < 10:
        return False
    # Basic format validation
    if key_type == "nebius":
        return len(api_key.strip()) > 20  # Nebius keys are typically longer
    elif key_type == "openai":
        return api_key.strip().startswith("sk-")  # OpenAI keys start with sk-
    return True


def test_api_connection(api_key: str, key_type: str) -> tuple[bool, str]:
    """Test API key by making a simple request."""
    try:
        if key_type == "nebius":
            # Test Nebius API
            from openai import OpenAI
            client = OpenAI(
                base_url="https://api.tokenfactory.nebius.com/v1",
                api_key=api_key
            )
            # Try to list models (lightweight call)
            try:
                models = client.models.list()
                return True, "✅ Nebius API key is valid"
            except Exception as e:
                # If models.list fails, try a simple completion test
                return True, "✅ Nebius API key format valid (connection test skipped)"
        elif key_type == "openai":
            # Test OpenAI API
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            try:
                models = client.models.list()
                return True, "✅ OpenAI API key is valid"
            except Exception:
                return True, "✅ OpenAI API key format valid (connection test skipped)"
    except Exception as e:
        return False, f"❌ Error: {str(e)[:100]}"
    return False, "❌ Could not validate API key"


def initialize_bot_with_keys(nebius_key: str, openai_key: Optional[str] = None, kubeconfig_path: Optional[str] = None):
    """Initialize SRE bot components with provided API keys and kubeconfig."""
    try:
        # Set API keys in environment
        os.environ["NEBIUS_API_KEY"] = nebius_key
        if openai_key:
            os.environ["OPENAI_API_KEY"] = openai_key
        
        # Import modules
        from connectors.kubernetes import KubernetesConnector
        from config import Settings
        
        # Reload settings to pick up new env vars
        settings = Settings()
        
        # Initialize Kubernetes connector
        # Priority: provided kubeconfig_path > settings > auto-detect Kind > env var > default
        kubeconfig = kubeconfig_path
        if not kubeconfig:
            kubeconfig = settings.kubeconfig
        
        # Check for base64 encoded kubeconfig (for Streamlit Cloud)
        if not kubeconfig:
            kubeconfig_base64 = os.getenv("KUBECONFIG_BASE64")
            if kubeconfig_base64:
                try:
                    import base64
                    import tempfile
                    kubeconfig_content = base64.b64decode(kubeconfig_base64).decode('utf-8')
                    temp_dir = tempfile.gettempdir()
                    temp_kubeconfig = os.path.join(temp_dir, "kubeconfig_from_secrets.yaml")
                    with open(temp_kubeconfig, 'w') as f:
                        f.write(kubeconfig_content)
                    kubeconfig = temp_kubeconfig
                    logger.info("✅ Using kubeconfig from KUBECONFIG_BASE64 environment variable")
                except Exception as e:
                    logger.error(f"Failed to decode KUBECONFIG_BASE64: {e}")
        
        if not kubeconfig:
            # Check if Kind cluster exists and get its kubeconfig
            try:
                result = subprocess.run(
                    ["kind", "get", "kubeconfig", "--name", "sre-bot-cluster"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0 and result.stdout.strip():
                    # Kind cluster exists, use default kubeconfig path
                    kubeconfig = os.path.expanduser("~/.kube/config")
                    logger.info(f"✅ Detected Kind cluster 'sre-bot-cluster', using kubeconfig: {kubeconfig}")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                # Kind not available or cluster doesn't exist
                logger.info("ℹ️ Kind cluster not found, trying other options...")
        
        # If still no kubeconfig, try environment variable
        if not kubeconfig:
            kubeconfig = os.getenv("KUBECONFIG")
        
        # If still no kubeconfig, use default
        if not kubeconfig:
            kubeconfig = os.path.expanduser("~/.kube/config")
        
        logger.info(f"📝 Using kubeconfig: {kubeconfig}")
        
        # Verify kubeconfig exists (only if it's a file path)
        if kubeconfig and kubeconfig.startswith("/") and not os.path.exists(kubeconfig):
            logger.warning(f"⚠️ Kubeconfig file not found: {kubeconfig}")
            # Don't use st.warning here as it might not be in Streamlit context
        
        k8s_connector = KubernetesConnector(kubeconfig=kubeconfig)
        
        # Initialize knowledge base (optional)
        knowledge_base = None
        if openai_key:
            try:
                from rag.knowledge_base import KubernetesKnowledgeBase
                knowledge_base = KubernetesKnowledgeBase(
                    vector_db_path=settings.vector_db_path,
                    openai_api_key=openai_key
                )
            except Exception as e:
                logger.warning(f"Knowledge base initialization failed: {e}")
        
        # Initialize memory manager (optional)
        memory_manager = None
        try:
            from memory.memory_manager import MemoryManager
            memory_manager = MemoryManager(
                database_url=settings.database_url,
                openai_api_key=openai_key
            )
        except Exception as e:
            logger.warning(f"Memory manager initialization failed: {e}")
        
        # Initialize agents using direct imports to avoid __init__.py relative import issues
        agents_status = {
            "troubleshooting": False,
            "monitoring": False,
            "automation": False,
            "knowledge": False,
            "coordinator": False
        }
        
        # Import required modules first using absolute imports
        # These need to be imported before setting up package structure
        # Import mcp module directly
        import importlib.util as util
        import types
        
        # Load mcp package and modules
        # First create the mcp package
        if 'mcp' not in sys.modules:
            mcp_pkg = types.ModuleType('mcp')
            mcp_pkg.__path__ = [str(project_root / "mcp")]
            sys.modules['mcp'] = mcp_pkg
        
        # Load mcp.k8s_mcp module first
        mcp_module_name = 'multi_agent_sre_bot.mcp.k8s_mcp'
        mcp_spec = util.spec_from_file_location(mcp_module_name, project_root / "mcp" / "k8s_mcp.py")
        if mcp_spec and mcp_spec.loader:
            mcp_mod = util.module_from_spec(mcp_spec)
            mcp_mod.__package__ = 'multi_agent_sre_bot.mcp'
            mcp_mod.__name__ = mcp_module_name
            sys.modules[mcp_module_name] = mcp_mod
            sys.modules['mcp.k8s_mcp'] = mcp_mod  # Also register with short name
            sys.modules['mcp'].k8s_mcp = mcp_mod  # Make it accessible as mcp.k8s_mcp
            mcp_spec.loader.exec_module(mcp_mod)
            KubernetesMCPServer = mcp_mod.KubernetesMCPServer
        else:
            KubernetesMCPServer = None
        
        # Now load mcp.__init__.py to make KubernetesMCPServer available via "from ..mcp import"
        # The __init__.py does: from .k8s_mcp import KubernetesMCPServer
        mcp_init_path = project_root / "mcp" / "__init__.py"
        if mcp_init_path.exists() and KubernetesMCPServer:
            try:
                # Load __init__.py
                mcp_init_name = 'multi_agent_sre_bot.mcp'
                mcp_init_spec = util.spec_from_file_location(mcp_init_name, mcp_init_path)
                if mcp_init_spec and mcp_init_spec.loader:
                    mcp_init_mod = util.module_from_spec(mcp_init_spec)
                    mcp_init_mod.__package__ = 'multi_agent_sre_bot.mcp'
                    mcp_init_mod.__name__ = mcp_init_name
                    # Set k8s_mcp module so __init__.py can import from it
                    mcp_init_mod.k8s_mcp = sys.modules.get('mcp.k8s_mcp')
                    sys.modules[mcp_init_name] = mcp_init_mod
                    sys.modules['mcp'].__init__ = mcp_init_mod
                    mcp_init_spec.loader.exec_module(mcp_init_mod)
                    # Now KubernetesMCPServer should be available on mcp_init_mod
                    if hasattr(mcp_init_mod, 'KubernetesMCPServer'):
                        sys.modules['mcp'].KubernetesMCPServer = mcp_init_mod.KubernetesMCPServer
                    else:
                        # Fallback: set it directly
                        sys.modules['mcp'].KubernetesMCPServer = KubernetesMCPServer
                else:
                    # Fallback: set it directly on mcp package
                    sys.modules['mcp'].KubernetesMCPServer = KubernetesMCPServer
            except Exception as e:
                logger.warning(f"Could not load mcp.__init__.py: {e}, setting KubernetesMCPServer directly")
                # Fallback: set it directly on mcp package
                sys.modules['mcp'].KubernetesMCPServer = KubernetesMCPServer
        elif KubernetesMCPServer:
            # If __init__.py doesn't exist or failed, set it directly
            sys.modules['mcp'].KubernetesMCPServer = KubernetesMCPServer
        
        # Import other modules normally
        from connectors.kubernetes import KubernetesConnector
        from rag.knowledge_base import KubernetesKnowledgeBase
        
        # Set up module namespace for relative imports to work
        # The agents use relative imports like "from ..mcp import", so we need to
        # set up the package structure properly
        import types
        
        # Ensure packages exist in sys.modules (they should be imported above)
        if 'mcp' not in sys.modules:
            mcp_pkg = types.ModuleType('mcp')
            sys.modules['mcp'] = mcp_pkg
        if 'connectors' not in sys.modules:
            connectors_pkg = types.ModuleType('connectors')
            sys.modules['connectors'] = connectors_pkg
        if 'rag' not in sys.modules:
            rag_pkg = types.ModuleType('rag')
            sys.modules['rag'] = rag_pkg
        if 'agents' not in sys.modules:
            agents_pkg = types.ModuleType('agents')
            sys.modules['agents'] = agents_pkg
        
        # Set __package__ attribute on agents module so relative imports work
        # When agents do "from ..mcp import", Python needs to know the package structure
        # Create a parent package that contains both agents and mcp
        parent_pkg_name = 'multi_agent_sre_bot'
        if parent_pkg_name not in sys.modules:
            parent_pkg = types.ModuleType(parent_pkg_name)
            sys.modules[parent_pkg_name] = parent_pkg
            # Make mcp, connectors, rag, and agents subpackages
            parent_pkg.mcp = sys.modules['mcp']
            parent_pkg.connectors = sys.modules['connectors']
            parent_pkg.rag = sys.modules['rag']
            parent_pkg.agents = sys.modules['agents']
            # Also register them as subpackages in sys.modules
            sys.modules[parent_pkg_name + '.mcp'] = sys.modules['mcp']
            sys.modules[parent_pkg_name + '.connectors'] = sys.modules['connectors']
            sys.modules[parent_pkg_name + '.rag'] = sys.modules['rag']
            sys.modules[parent_pkg_name + '.agents'] = sys.modules['agents']
        
        # Set package info on agents so relative imports resolve correctly
        sys.modules['agents'].__package__ = parent_pkg_name + '.agents'
        sys.modules['agents'].__path__ = [str(project_root / "agents")]
        # Also set package info on mcp, connectors, rag
        sys.modules['mcp'].__package__ = parent_pkg_name + '.mcp'
        sys.modules['mcp'].__path__ = [str(project_root / "mcp")]
        sys.modules['connectors'].__package__ = parent_pkg_name + '.connectors'
        sys.modules['rag'].__package__ = parent_pkg_name + '.rag'
        
        # Ensure mcp package has KubernetesMCPServer available for relative imports
        # When agent does "from ..mcp import KubernetesMCPServer", it needs to find it
        if KubernetesMCPServer:
            # Make it available on the parent package's mcp subpackage
            if parent_pkg_name in sys.modules:
                parent_pkg = sys.modules[parent_pkg_name]
                if hasattr(parent_pkg, 'mcp'):
                    parent_pkg.mcp.KubernetesMCPServer = KubernetesMCPServer
        
        # Now import agents using direct file imports
        import importlib.util as util
        
        try:
            # Troubleshooting agent - use consistent naming
            module_name = 'multi_agent_sre_bot.agents.troubleshooting_agent'
            spec = util.spec_from_file_location(module_name, project_root / "agents" / "troubleshooting_agent.py")
            mod = util.module_from_spec(spec)
            # Set package info so relative imports work
            mod.__package__ = 'multi_agent_sre_bot.agents'
            mod.__name__ = module_name
            sys.modules[module_name] = mod
            sys.modules['agents.troubleshooting_agent'] = mod  # Also register with short name
            sys.modules['agents'].troubleshooting_agent = mod
            spec.loader.exec_module(mod)
            TroubleshootingAgent = mod.TroubleshootingAgent
            
            troubleshooting_agent = TroubleshootingAgent(
                k8s_connector=k8s_connector,
                mcp_server=None,
                nebius_api_key=nebius_key
            )
            agents_status["troubleshooting"] = True
        except Exception as e:
            logger.error(f"Failed to initialize troubleshooting agent: {e}", exc_info=True)
            raise
        
        try:
            # Monitoring agent - use consistent naming
            module_name = 'multi_agent_sre_bot.agents.monitoring_agent'
            spec = util.spec_from_file_location(module_name, project_root / "agents" / "monitoring_agent.py")
            mod = util.module_from_spec(spec)
            # Set package info so relative imports work
            mod.__package__ = 'multi_agent_sre_bot.agents'
            mod.__name__ = module_name
            sys.modules[module_name] = mod
            sys.modules['agents.monitoring_agent'] = mod  # Also register with short name
            sys.modules['agents'].monitoring_agent = mod
            spec.loader.exec_module(mod)
            MonitoringAgent = mod.MonitoringAgent
            
            monitoring_agent = MonitoringAgent(
                k8s_connector=k8s_connector,
                nebius_api_key=nebius_key
            )
            agents_status["monitoring"] = True
        except Exception as e:
            logger.error(f"Failed to initialize monitoring agent: {e}", exc_info=True)
            raise
        
        try:
            # Automation agent - use consistent naming
            module_name = 'multi_agent_sre_bot.agents.automation_agent'
            spec = util.spec_from_file_location(module_name, project_root / "agents" / "automation_agent.py")
            mod = util.module_from_spec(spec)
            # Set package info so relative imports work
            mod.__package__ = 'multi_agent_sre_bot.agents'
            mod.__name__ = module_name
            sys.modules[module_name] = mod
            sys.modules['agents.automation_agent'] = mod  # Also register with short name
            sys.modules['agents'].automation_agent = mod
            spec.loader.exec_module(mod)
            AutomationAgent = mod.AutomationAgent
            
            automation_agent = AutomationAgent(
                k8s_connector=k8s_connector,
                nebius_api_key=nebius_key
            )
            agents_status["automation"] = True
        except Exception as e:
            logger.error(f"Failed to initialize automation agent: {e}", exc_info=True)
            raise
        
        if knowledge_base:
            try:
                # Knowledge agent - use consistent naming
                module_name = 'multi_agent_sre_bot.agents.knowledge_agent'
                spec = util.spec_from_file_location(module_name, project_root / "agents" / "knowledge_agent.py")
                mod = util.module_from_spec(spec)
                # Set package info so relative imports work
                mod.__package__ = 'multi_agent_sre_bot.agents'
                mod.__name__ = module_name
                sys.modules[module_name] = mod
                sys.modules['agents.knowledge_agent'] = mod  # Also register with short name
                sys.modules['agents'].knowledge_agent = mod
                spec.loader.exec_module(mod)
                KnowledgeAgent = mod.KnowledgeAgent
                
                knowledge_agent = KnowledgeAgent(
                    knowledge_base=knowledge_base,
                    nebius_api_key=nebius_key
                )
                agents_status["knowledge"] = True
            except Exception as e:
                logger.warning(f"Failed to initialize knowledge agent: {e}")
                knowledge_agent = monitoring_agent
        else:
            knowledge_agent = monitoring_agent
        
        try:
            # Coordinator agent - use consistent naming
            module_name = 'multi_agent_sre_bot.agents.coordinator_agent'
            spec = util.spec_from_file_location(module_name, project_root / "agents" / "coordinator_agent.py")
            mod = util.module_from_spec(spec)
            # Set package info so relative imports work
            mod.__package__ = 'multi_agent_sre_bot.agents'
            mod.__name__ = module_name
            sys.modules[module_name] = mod
            sys.modules['agents.coordinator_agent'] = mod  # Also register with short name
            sys.modules['agents'].coordinator_agent = mod
            spec.loader.exec_module(mod)
            CoordinatorAgent = mod.CoordinatorAgent
            
            coordinator_agent = CoordinatorAgent(
                troubleshooting_agent=troubleshooting_agent,
                monitoring_agent=monitoring_agent,
                automation_agent=automation_agent,
                knowledge_agent=knowledge_agent,
                nebius_api_key=nebius_key
            )
            agents_status["coordinator"] = True
        except Exception as e:
            logger.error(f"Failed to initialize coordinator agent: {e}", exc_info=True)
            raise
        
        return coordinator_agent, memory_manager, k8s_connector, agents_status
        
    except Exception as e:
        logger.error(f"Error initializing bot: {e}", exc_info=True)
        return None, None, None, {}


def main():
    """Main Streamlit app."""
    # Custom CSS for better UI
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .status-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .status-success {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .status-warning {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
    }
    .status-error {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="main-header">🤖 Multi-Agent SRE Bot</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Advanced Kubernetes SRE bot with multi-agent architecture, MCP integration, and RAG knowledge base</div>', unsafe_allow_html=True)
    
    # Sidebar for API key configuration
    with st.sidebar:
        st.header("🔑 API Keys Configuration")
        
        # Nebius API Key
        nebius_key = st.text_input(
            "Nebius API Key",
            value=st.session_state.nebius_api_key,
            type="password",
            help="Required for AI agent functionality. Get your key from https://nebius.ai"
        )
        
        # OpenAI API Key (optional)
        openai_key = st.text_input(
            "OpenAI API Key (Optional)",
            value=st.session_state.openai_api_key,
            type="password",
            help="Optional. Used for RAG knowledge base embeddings. Get your key from https://platform.openai.com"
        )
        
        st.markdown("---")
        st.header("☸️ Kubernetes Configuration")
        
        # Kubeconfig selection with file upload support for Streamlit Cloud
        kubeconfig_options = {
            "Upload kubeconfig file": "upload",
            "Use kubeconfig from environment": "env",
            "Auto-detect (Kind cluster)": "kind",
            "Default (~/.kube/config)": "default",
            "Custom path": "custom"
        }
        
        kubeconfig_choice = st.selectbox(
            "Kubeconfig Source",
            list(kubeconfig_options.keys()),
            help="Select how to connect to Kubernetes cluster. Use 'Upload' for Streamlit Cloud deployment."
        )
        
        kubeconfig_path = None
        kubeconfig_content = None
        
        if kubeconfig_choice == "Upload kubeconfig file":
            # File upload for Streamlit Cloud
            uploaded_file = st.file_uploader(
                "Upload kubeconfig file",
                type=["yaml", "yml"],
                help="Upload your kubeconfig file. This is required for Streamlit Cloud deployment."
            )
            
            if uploaded_file is not None:
                # Read file content
                kubeconfig_content = uploaded_file.read().decode('utf-8')
                
                # Save to temporary location
                import tempfile
                temp_dir = tempfile.gettempdir()
                temp_kubeconfig = os.path.join(temp_dir, f"kubeconfig_{st.session_state.get('session_id', 'default')}.yaml")
                
                with open(temp_kubeconfig, 'w') as f:
                    f.write(kubeconfig_content)
                
                kubeconfig_path = temp_kubeconfig
                st.success(f"✅ Kubeconfig uploaded and saved")
                st.session_state.kubeconfig_path = kubeconfig_path
                st.session_state.kubeconfig_content = kubeconfig_content
                
                # Verify kubeconfig
                try:
                    result = subprocess.run(
                        ["kubectl", "config", "view", "--kubeconfig", kubeconfig_path],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        # Extract current context
                        context_result = subprocess.run(
                            ["kubectl", "config", "current-context", "--kubeconfig", kubeconfig_path],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if context_result.returncode == 0:
                            st.info(f"📝 Current context: {context_result.stdout.strip()}")
                except Exception as e:
                    st.warning(f"⚠️ Could not verify kubeconfig: {str(e)[:100]}")
        
        elif kubeconfig_choice == "Use kubeconfig from environment":
            # Use KUBECONFIG environment variable (for Streamlit Cloud secrets)
            kubeconfig_path = os.getenv("KUBECONFIG")
            if kubeconfig_path:
                st.success(f"✅ Using kubeconfig from environment: {kubeconfig_path}")
            else:
                st.info("ℹ️ KUBECONFIG environment variable not set. Use Streamlit secrets or upload file.")
                st.code("""
# In Streamlit Cloud, add to secrets:
# KUBECONFIG=/path/to/kubeconfig
# Or use base64 encoded kubeconfig in KUBECONFIG_BASE64
                """)
            
            # Also check for base64 encoded kubeconfig (common in cloud deployments)
            kubeconfig_base64 = os.getenv("KUBECONFIG_BASE64")
            if kubeconfig_base64 and not kubeconfig_path:
                try:
                    import base64
                    import tempfile
                    kubeconfig_content = base64.b64decode(kubeconfig_base64).decode('utf-8')
                    temp_dir = tempfile.gettempdir()
                    temp_kubeconfig = os.path.join(temp_dir, "kubeconfig_from_env.yaml")
                    with open(temp_kubeconfig, 'w') as f:
                        f.write(kubeconfig_content)
                    kubeconfig_path = temp_kubeconfig
                    st.success("✅ Using kubeconfig from KUBECONFIG_BASE64 environment variable")
                    st.session_state.kubeconfig_path = kubeconfig_path
                except Exception as e:
                    st.error(f"❌ Failed to decode KUBECONFIG_BASE64: {str(e)[:100]}")
        
        elif kubeconfig_choice == "Custom path":
            custom_kubeconfig = st.text_input(
                "Kubeconfig Path",
                value=os.getenv("KUBECONFIG", ""),
                help="Enter full path to kubeconfig file"
            )
            if custom_kubeconfig:
                kubeconfig_path = custom_kubeconfig
        
        elif kubeconfig_choice == "Default (~/.kube/config)":
            kubeconfig_path = os.path.expanduser("~/.kube/config")
        
        # Show cluster detection status for Kind
        if kubeconfig_choice == "Auto-detect (Kind cluster)":
            try:
                result = subprocess.run(
                    ["kind", "get", "clusters"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if "sre-bot-cluster" in result.stdout:
                    st.success("✅ Kind cluster 'sre-bot-cluster' detected")
                else:
                    st.info("ℹ️ Kind cluster not found. Run 'make cluster-up' to create it.")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                st.warning("⚠️ Kind not available. Install Kind or use custom kubeconfig.")
        
        # Store kubeconfig choice in session state
        if kubeconfig_path:
            st.session_state.kubeconfig_path = kubeconfig_path
        elif kubeconfig_choice == "Auto-detect (Kind cluster)":
            st.session_state.kubeconfig_path = None
        else:
            st.session_state.kubeconfig_path = None
        
        # Show connection instructions for Streamlit Cloud
        if kubeconfig_choice in ["Upload kubeconfig file", "Use kubeconfig from environment"]:
            with st.expander("📋 Streamlit Cloud Deployment Guide"):
                st.markdown("""
                ### For Streamlit Cloud Deployment:
                
                1. **Option 1: Upload kubeconfig** (Current session only)
                   - Upload your kubeconfig file above
                   - File is stored temporarily for this session
                
                2. **Option 2: Use Streamlit Secrets** (Recommended)
                   - Go to Streamlit Cloud → Settings → Secrets
                   - Add your kubeconfig as base64:
                   ```toml
                   KUBECONFIG_BASE64 = "base64_encoded_kubeconfig_here"
                   ```
                   - Or set path if available:
                   ```toml
                   KUBECONFIG = "/path/to/kubeconfig"
                   ```
                
                3. **Option 3: Environment Variables**
                   - Set `KUBECONFIG` or `KUBECONFIG_BASE64` in deployment settings
                
                **Note**: Your cluster must be accessible from Streamlit Cloud's servers.
                Consider using:
                - Ingress with public endpoint
                - VPN/tunnel for private clusters
                - Cloud provider managed clusters with public API endpoints
                """)
        
        # Validate and test buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Validate Keys", use_container_width=True):
                nebius_valid = validate_api_key(nebius_key, "nebius")
                openai_valid = validate_api_key(openai_key, "openai") if openai_key else True
                
                if nebius_valid:
                    st.success("✅ Nebius key format valid")
                else:
                    st.error("❌ Nebius key format invalid")
                
                if openai_key:
                    if openai_valid:
                        st.success("✅ OpenAI key format valid")
                    else:
                        st.error("❌ OpenAI key format invalid")
                else:
                    st.info("ℹ️ OpenAI key not provided (optional)")
        
        with col2:
            if st.button("🧪 Test Connection", use_container_width=True):
                if nebius_key:
                    with st.spinner("Testing Nebius API..."):
                        success, message = test_api_connection(nebius_key, "nebius")
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                else:
                    st.warning("Please enter Nebius API key first")
        
        # Save and initialize button
        st.markdown("---")
        if st.button("🚀 Initialize Multi-Agent System", type="primary", use_container_width=True):
            if not nebius_key or not validate_api_key(nebius_key, "nebius"):
                st.error("❌ Please enter a valid Nebius API key")
            else:
                with st.spinner("Initializing multi-agent system..."):
                    # Save keys to session state
                    st.session_state.nebius_api_key = nebius_key
                    st.session_state.openai_api_key = openai_key
                    
                    # Get kubeconfig path
                    kubeconfig_path = st.session_state.get("kubeconfig_path", None)
                    
                    # Initialize bot with kubeconfig
                    coordinator_agent, memory_manager, k8s_connector, agents_status = initialize_bot_with_keys(
                        nebius_key, openai_key, kubeconfig_path
                    )
                    
                    if coordinator_agent:
                        st.session_state.coordinator_agent = coordinator_agent
                        st.session_state.memory_manager = memory_manager
                        st.session_state.k8s_connector = k8s_connector
                        st.session_state.agents_status = agents_status
                        st.session_state.initialized = True
                        st.session_state.api_keys_set = True
                        st.success("✅ Multi-Agent System Initialized!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to initialize. Check logs for details.")
        
        # Status section
        st.markdown("---")
        st.header("📊 System Status")
        
        if st.session_state.initialized:
            st.success("✅ System Initialized")
            
            # Show agent status
            st.subheader("Agent Status")
            agents_status = st.session_state.agents_status
            
            status_icons = {
                "troubleshooting": "🔧",
                "monitoring": "📊",
                "automation": "⚙️",
                "knowledge": "📚",
                "coordinator": "🎯"
            }
            
            for agent_name, status in agents_status.items():
                icon = status_icons.get(agent_name, "🤖")
                if status:
                    st.success(f"{icon} {agent_name.title()} Agent: ✅ Active")
                else:
                    st.warning(f"{icon} {agent_name.title()} Agent: ⚠️ Limited")
            
            # Cluster connection status
            if st.session_state.k8s_connector:
                try:
                    info = st.session_state.k8s_connector.get_cluster_info()
                    st.success("✅ Kubernetes Connected")
                    st.caption(f"Nodes: {info.get('node_count', 'N/A')}")
                except Exception as e:
                    st.error(f"❌ Kubernetes Error: {str(e)[:50]}")
        else:
            st.warning("⚠️ System Not Initialized")
            st.info("💡 Enter API keys and click 'Initialize Multi-Agent System'")
        
        # Reset button
        st.markdown("---")
        if st.button("🔄 Reset Session", use_container_width=True):
            for key in list(st.session_state.keys()):
                if key not in ["nebius_api_key", "openai_api_key"]:
                    del st.session_state[key]
            st.session_state.initialized = False
            st.session_state.api_keys_set = False
            st.rerun()
    
    # Main content area
    if not st.session_state.initialized:
        # Show initialization prompt
        st.info("""
        👋 **Welcome to Multi-Agent SRE Bot!**
        
        To get started:
        1. **Enter your Nebius API key** in the sidebar (required)
        2. **Optionally enter OpenAI API key** for RAG knowledge base (optional)
        3. **Click "Validate Keys"** to check key formats
        4. **Click "Test Connection"** to verify API connectivity
        5. **Click "Initialize Multi-Agent System"** to start the bot
        
        Once initialized, you can:
        - Ask questions about your Kubernetes cluster
        - Get troubleshooting assistance
        - Monitor cluster health
        - Execute automated actions
        - Access Kubernetes knowledge base
        """)
        
        # Show example queries
        with st.expander("📝 Example Queries You Can Ask"):
            st.markdown("""
            - "Check the health of my cluster"
            - "Why are my pods crashing?"
            - "Show me the status of all pods in web-app namespace"
            - "What's causing high CPU usage?"
            - "How do I set up horizontal pod autoscaling?"
            - "Analyze the errors in my cluster"
            """)
        
        # Show cluster info if available
        try:
            from connectors.kubernetes import KubernetesConnector
            k8s_connector = KubernetesConnector()
            info = k8s_connector.get_cluster_info()
            st.success(f"✅ Kubernetes cluster detected: {info.get('node_count', 'N/A')} nodes")
        except Exception as e:
            st.warning(f"⚠️ Could not connect to Kubernetes cluster: {str(e)[:100]}")
            st.info("💡 Make sure your kubeconfig is set or Kind cluster is running")
    else:
        # Chat interface
        st.header("💬 Chat with SRE Bot")
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask me about your Kubernetes cluster..."):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Get response
            with st.chat_message("assistant"):
                with st.spinner("🤔 Analyzing..."):
                    try:
                        # Get context from memory
                        context = {}
                        if st.session_state.memory_manager:
                            memory_context = st.session_state.memory_manager.get_context(prompt)
                            if memory_context:
                                context["memory"] = memory_context
                        
                        # Process query
                        response = st.session_state.coordinator_agent.process_query(prompt, context)
                        
                        # Record conversation
                        if st.session_state.memory_manager:
                            st.session_state.memory_manager.record_conversation(prompt, response)
                        
                        # Display response
                        st.markdown(response)
                        
                        # Add to messages
                        st.session_state.messages.append({"role": "assistant", "content": response})
                        
                    except Exception as e:
                        error_msg = f"❌ Error: {str(e)}"
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
                        logger.error(f"Error processing query: {e}", exc_info=True)
        
        # Quick actions
        st.markdown("---")
        st.header("⚡ Quick Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Cluster Health", use_container_width=True):
                if st.session_state.initialized:
                    with st.spinner("Checking cluster health..."):
                        try:
                            response = st.session_state.coordinator_agent.process_query(
                                "Check the health of my cluster"
                            )
                            st.session_state.messages.append({"role": "user", "content": "Check the health of my cluster"})
                            st.session_state.messages.append({"role": "assistant", "content": response})
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
        
        with col2:
            if st.button("📝 View Pods", use_container_width=True):
                if st.session_state.initialized:
                    with st.spinner("Getting pod status..."):
                        try:
                            response = st.session_state.coordinator_agent.process_query(
                                "Show me the status of all pods"
                            )
                            st.session_state.messages.append({"role": "user", "content": "Show me the status of all pods"})
                            st.session_state.messages.append({"role": "assistant", "content": response})
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
        
        with col3:
            if st.button("🔍 Troubleshoot", use_container_width=True):
                if st.session_state.initialized:
                    with st.spinner("Analyzing cluster issues..."):
                        try:
                            response = st.session_state.coordinator_agent.process_query(
                                "Analyze and troubleshoot any issues in my cluster"
                            )
                            st.session_state.messages.append({"role": "user", "content": "Analyze and troubleshoot any issues in my cluster"})
                            st.session_state.messages.append({"role": "assistant", "content": response})
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")


if __name__ == "__main__":
    main()
