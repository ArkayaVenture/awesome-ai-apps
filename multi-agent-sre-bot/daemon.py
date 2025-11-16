#!/usr/bin/env python3
"""SRE Bot daemon mode - runs the bot in the background."""
import os
import sys
import time
import signal
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup logging
log_dir = project_root / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "sre-bot.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Load environment
load_dotenv()

# Global flag for graceful shutdown
shutdown = False

def signal_handler(signum, frame):
    """Handle shutdown signals."""
    global shutdown
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    shutdown = True

def main():
    """Main daemon loop."""
    global shutdown
    
    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    logger.info("🤖 SRE Bot daemon starting...")
    logger.info(f"📝 Logging to: {log_file}")
    
    try:
        # Import after path setup - use absolute imports
        import sys
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        # Import modules directly to avoid __init__.py relative import issues
        import importlib.util
        
        # Import config
        from config import settings
        
        # Import connectors
        spec = importlib.util.spec_from_file_location("kubernetes_connector", project_root / "connectors" / "kubernetes.py")
        kubernetes_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(kubernetes_module)
        KubernetesConnector = kubernetes_module.KubernetesConnector
        
        # Import RAG (optional)
        try:
            spec = importlib.util.spec_from_file_location("knowledge_base", project_root / "rag" / "knowledge_base.py")
            rag_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(rag_module)
            KubernetesKnowledgeBase = rag_module.KubernetesKnowledgeBase
        except Exception as e:
            logger.warning(f"Could not load knowledge base: {e}")
            KubernetesKnowledgeBase = None
        
        # Import memory (optional)
        try:
            spec = importlib.util.spec_from_file_location("memory_manager", project_root / "memory" / "memory_manager.py")
            memory_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(memory_module)
            MemoryManager = memory_module.MemoryManager
        except Exception as e:
            logger.warning(f"Could not load memory manager: {e}")
            MemoryManager = None
        
        # Import agents (only if API key available)
        TroubleshootingAgent = None
        MonitoringAgent = None
        AutomationAgent = None
        KnowledgeAgent = None
        CoordinatorAgent = None
        
        if settings.nebius_api_key:
            try:
                # Import agents using direct file imports
                import importlib.util as util
                
                # Troubleshooting agent
                spec = util.spec_from_file_location("troubleshooting", project_root / "agents" / "troubleshooting_agent.py")
                mod = util.module_from_spec(spec)
                sys.modules['troubleshooting_agent'] = mod
                spec.loader.exec_module(mod)
                TroubleshootingAgent = mod.TroubleshootingAgent
                
                # Monitoring agent
                spec = util.spec_from_file_location("monitoring", project_root / "agents" / "monitoring_agent.py")
                mod = util.module_from_spec(spec)
                sys.modules['monitoring_agent'] = mod
                spec.loader.exec_module(mod)
                MonitoringAgent = mod.MonitoringAgent
                
                # Automation agent
                spec = util.spec_from_file_location("automation", project_root / "agents" / "automation_agent.py")
                mod = util.module_from_spec(spec)
                sys.modules['automation_agent'] = mod
                spec.loader.exec_module(mod)
                AutomationAgent = mod.AutomationAgent
                
                # Knowledge agent
                if KubernetesKnowledgeBase:
                    spec = util.spec_from_file_location("knowledge", project_root / "agents" / "knowledge_agent.py")
                    mod = util.module_from_spec(spec)
                    sys.modules['knowledge_agent'] = mod
                    spec.loader.exec_module(mod)
                    KnowledgeAgent = mod.KnowledgeAgent
                
                # Coordinator agent
                spec = util.spec_from_file_location("coordinator", project_root / "agents" / "coordinator_agent.py")
                mod = util.module_from_spec(spec)
                sys.modules['coordinator_agent'] = mod
                spec.loader.exec_module(mod)
                CoordinatorAgent = mod.CoordinatorAgent
                
            except Exception as e:
                logger.error(f"Failed to import agents: {e}", exc_info=True)
                logger.warning("Continuing in monitoring-only mode")
        
        # Initialize components
        logger.info("🔧 Initializing components...")
        
        # Kubernetes connector
        # Use Kind cluster kubeconfig if available
        kubeconfig = settings.kubeconfig
        if not kubeconfig:
            # Try to use Kind cluster kubeconfig
            import subprocess
            try:
                result = subprocess.run(
                    ["kubectl", "config", "view", "--minify", "--context", "kind-sre-bot-cluster"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    kubeconfig = os.path.expanduser("~/.kube/config")
                    logger.info(f"📝 Using Kind cluster kubeconfig: {kubeconfig}")
            except Exception:
                pass
        
        k8s_connector = KubernetesConnector(kubeconfig=kubeconfig)
        logger.info("✅ Kubernetes connector initialized")
        
        # Knowledge base (optional, may take time to initialize)
        knowledge_base = None
        if KubernetesKnowledgeBase:
            try:
                if settings.openai_api_key:
                    knowledge_base = KubernetesKnowledgeBase(
                        vector_db_path=settings.vector_db_path,
                        openai_api_key=settings.openai_api_key
                    )
                    logger.info("✅ Knowledge base initialized")
                else:
                    logger.warning("⚠️  OPENAI_API_KEY not set. Knowledge base disabled.")
            except Exception as e:
                logger.warning(f"⚠️  Knowledge base initialization failed: {e}. Continuing without it.")
        
        # Memory manager (optional)
        memory_manager = None
        if MemoryManager:
            try:
                memory_manager = MemoryManager(
                    database_url=settings.database_url,
                    openai_api_key=settings.openai_api_key
                )
                logger.info("✅ Memory manager initialized")
            except Exception as e:
                logger.warning(f"⚠️  Memory manager initialization failed: {e}. Continuing without it.")
        
        # Check if API keys and agents are available
        coordinator_agent = None
        if not settings.nebius_api_key or not TroubleshootingAgent:
            logger.warning("⚠️  NEBIUS_API_KEY not set or agents not available. Bot will monitor but AI features will be limited.")
            logger.warning("💡 Set NEBIUS_API_KEY in .env file for full functionality.")
            logger.info("📊 Running in monitoring-only mode (no AI agents)")
        else:
            try:
                # Initialize agents
                logger.info("🤖 Initializing AI agents...")
                troubleshooting_agent = TroubleshootingAgent(
                    k8s_connector=k8s_connector,
                    mcp_server=None,  # MCP optional
                    nebius_api_key=settings.nebius_api_key
                )
                logger.info("✅ Troubleshooting agent initialized")
                
                monitoring_agent = MonitoringAgent(
                    k8s_connector=k8s_connector,
                    nebius_api_key=settings.nebius_api_key
                )
                logger.info("✅ Monitoring agent initialized")
                
                automation_agent = AutomationAgent(
                    k8s_connector=k8s_connector,
                    nebius_api_key=settings.nebius_api_key
                )
                logger.info("✅ Automation agent initialized")
                
                if knowledge_base and KnowledgeAgent:
                    knowledge_agent = KnowledgeAgent(
                        knowledge_base=knowledge_base,
                        nebius_api_key=settings.nebius_api_key
                    )
                    logger.info("✅ Knowledge agent initialized")
                else:
                    logger.warning("⚠️  Knowledge base not available. Skipping knowledge agent.")
                    knowledge_agent = monitoring_agent  # Use monitoring agent as fallback
                
                if CoordinatorAgent:
                    coordinator_agent = CoordinatorAgent(
                        troubleshooting_agent=troubleshooting_agent,
                        monitoring_agent=monitoring_agent,
                        automation_agent=automation_agent,
                        knowledge_agent=knowledge_agent,
                        nebius_api_key=settings.nebius_api_key
                    )
                    logger.info("✅ Coordinator agent initialized")
                    logger.info("✅ All agents initialized")
                else:
                    logger.warning("⚠️  Coordinator agent not available")
            except Exception as e:
                logger.error(f"❌ Failed to initialize agents: {e}", exc_info=True)
                logger.warning("⚠️  Continuing in monitoring-only mode")
                coordinator_agent = None
        logger.info("🚀 SRE Bot daemon is running...")
        logger.info("📊 Monitoring cluster for issues...")
        
        # Main monitoring loop
        iteration = 0
        while not shutdown:
            try:
                iteration += 1
                
                # Every 30 seconds, check cluster health
                if iteration % 6 == 0:  # 30 seconds (5 second intervals)
                    logger.info("🔍 Performing health check...")
                    
                    # Get cluster info
                    cluster_info = k8s_connector.get_cluster_info()
                    pod_statuses = k8s_connector.get_pod_status()
                    
                    # Check for issues
                    issues_found = []
                    for namespace in ["web-app", "api-service", "database", "default"]:
                        pods = k8s_connector.get_pod_status(namespace)
                        events = k8s_connector.get_events(namespace, limit=10)
                        
                        # Check for failed pods
                        for pod_name, status in pods.items():
                            if isinstance(status, dict):
                                if status.get("status") not in ["Running", "Succeeded"]:
                                    issues_found.append(f"Pod {pod_name} in {namespace} is {status.get('status')}")
                                if status.get("restarts", 0) > 3:
                                    issues_found.append(f"Pod {pod_name} in {namespace} has {status.get('restarts')} restarts")
                        
                        # Check for error events
                        for event in events:
                            if isinstance(event, dict) and event.get("type") == "Warning":
                                issues_found.append(f"Warning in {namespace}: {event.get('reason')} - {event.get('message')}")
                    
                    if issues_found:
                        logger.warning(f"⚠️  Found {len(issues_found)} potential issues:")
                        for issue in issues_found[:5]:  # Log first 5
                            logger.warning(f"  - {issue}")
                        
                        # Use troubleshooting agent to analyze (if available)
                        if len(issues_found) > 0 and coordinator_agent:
                            try:
                                issue_summary = "\n".join(issues_found[:3])
                                logger.info("🔧 Analyzing issues with troubleshooting agent...")
                                response = coordinator_agent.troubleshooting_agent.diagnose(
                                    f"Found the following issues in the cluster:\n{issue_summary}",
                                    namespace="default"
                                )
                                logger.info(f"💡 Troubleshooting suggestions:\n{response[:500]}...")  # First 500 chars
                            except Exception as e:
                                logger.error(f"Error in troubleshooting: {e}")
                        elif len(issues_found) > 0:
                            logger.info("💡 Issues detected. Set NEBIUS_API_KEY for AI-powered analysis.")
                    else:
                        logger.info("✅ Cluster health check passed - no issues detected")
                
                # Sleep for 5 seconds
                time.sleep(5)
                
            except KeyboardInterrupt:
                shutdown = True
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                time.sleep(10)  # Wait longer on error
        
        logger.info("🛑 SRE Bot daemon shutting down...")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

