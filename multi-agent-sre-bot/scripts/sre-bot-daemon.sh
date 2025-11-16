#!/bin/bash
# SRE Bot daemon management script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PID_FILE="$PROJECT_DIR/.sre-bot.pid"
LOG_FILE="$PROJECT_DIR/logs/sre-bot.log"
DAEMON_SCRIPT="$PROJECT_DIR/daemon.py"

# Ensure logs directory exists
mkdir -p "$PROJECT_DIR/logs"

start_daemon() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "⚠️  SRE bot is already running (PID: $PID)"
            return 1
        else
            rm -f "$PID_FILE"
        fi
    fi
    
    echo "🤖 Starting SRE bot in daemon mode..."
    
    cd "$PROJECT_DIR"
    
    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    # Export Kind cluster kubeconfig if it exists
    if kind get clusters | grep -q "^sre-bot-cluster$"; then
        # Use default kubeconfig location (kind stores it there)
        KUBECONFIG_PATH="$HOME/.kube/config"
        
        export KUBECONFIG="$KUBECONFIG_PATH"
        echo "📝 Using Kind cluster kubeconfig: $KUBECONFIG_PATH"
        
        # Set context
        kubectl config use-context kind-sre-bot-cluster >/dev/null 2>&1
        
        # Verify connection
        if kubectl cluster-info --context kind-sre-bot-cluster >/dev/null 2>&1; then
            echo "✅ Cluster connection verified"
        else
            echo "⚠️  Could not verify cluster connection, but continuing..."
        fi
    fi
    
    # Start daemon
    nohup python3 "$DAEMON_SCRIPT" > "$LOG_FILE" 2>&1 &
    DAEMON_PID=$!
    
    echo $DAEMON_PID > "$PID_FILE"
    
    sleep 2
    
    if ps -p "$DAEMON_PID" > /dev/null 2>&1; then
        echo "✅ SRE bot started (PID: $DAEMON_PID)"
        echo "📝 Logs: $LOG_FILE"
    else
        echo "❌ Failed to start SRE bot"
        rm -f "$PID_FILE"
        return 1
    fi
}

stop_daemon() {
    if [ ! -f "$PID_FILE" ]; then
        echo "⚠️  SRE bot is not running (no PID file)"
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    
    if ! ps -p "$PID" > /dev/null 2>&1; then
        echo "⚠️  SRE bot is not running (process not found)"
        rm -f "$PID_FILE"
        return 1
    fi
    
    echo "🛑 Stopping SRE bot (PID: $PID)..."
    kill "$PID" || true
    
    # Wait for process to stop
    for i in {1..10}; do
        if ! ps -p "$PID" > /dev/null 2>&1; then
            break
        fi
        sleep 1
    done
    
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "⚠️  Process still running, forcing kill..."
        kill -9 "$PID" || true
    fi
    
    rm -f "$PID_FILE"
    echo "✅ SRE bot stopped"
}

status_daemon() {
    if [ ! -f "$PID_FILE" ]; then
        echo "❌ SRE bot is not running"
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "✅ SRE bot is running (PID: $PID)"
        echo "📝 Log file: $LOG_FILE"
        return 0
    else
        echo "❌ SRE bot is not running (stale PID file)"
        rm -f "$PID_FILE"
        return 1
    fi
}

show_logs() {
    if [ ! -f "$LOG_FILE" ]; then
        echo "⚠️  Log file not found: $LOG_FILE"
        return 1
    fi
    
    echo "📝 SRE Bot Logs (last 50 lines):"
    echo "---"
    tail -50 "$LOG_FILE"
}

# Main
case "${1:-}" in
    start)
        start_daemon
        ;;
    stop)
        stop_daemon
        ;;
    status)
        status_daemon
        ;;
    logs)
        show_logs
        ;;
    restart)
        stop_daemon
        sleep 2
        start_daemon
        ;;
    *)
        echo "Usage: $0 {start|stop|status|logs|restart}"
        exit 1
        ;;
esac

