import asyncio
import os
import threading
import time
from pathlib import Path
from typing import Optional
from collections import deque
import sys
import contextlib

import yaml
from fastmcp import FastMCP

from . import co_datascientist_api
from .settings import settings
from .workflow_runner import workflow_runner

mcp = FastMCP("CoDatascientist")

# Simple in-memory event buffer so MCP clients can pull status instead of watching server stdout
_event_buffer = deque(maxlen=500)
_event_lock = threading.Lock()
_last_stream_poll_ts = 0.0
# Minimum seconds between optimize_and_stream responses (to avoid client hammering)
_MIN_STREAM_POLL_SECONDS = float(os.getenv("CO_DATASCIENTIST_STREAM_MIN_POLL_SECONDS", "1"))


def _push_event(message: str):
    with _event_lock:
        _event_buffer.append(message)


@contextlib.contextmanager
def _tee_output():
    """Tee stdout/stderr into the MCP event buffer while still printing to console."""

    class Tee:
        def __init__(self, original):
            self.original = original
            self._buf = ""

        def write(self, data):
            self.original.write(data)
            self._buf += data
            while "\n" in self._buf:
                line, self._buf = self._buf.split("\n", 1)
                if line.strip():
                    _push_event(line)

        def flush(self):
            self.original.flush()

    orig_out, orig_err = sys.stdout, sys.stderr
    tee_out, tee_err = Tee(orig_out), Tee(orig_err)
    try:
        sys.stdout, sys.stderr = tee_out, tee_err
        yield
    finally:
        sys.stdout, sys.stderr = orig_out, orig_err
        # Flush any trailing partials
        if getattr(tee_out, "_buf", "").strip():
            _push_event(tee_out._buf.strip())
        if getattr(tee_err, "_buf", "").strip():
            _push_event(tee_err._buf.strip())


def _load_config(config_path: Optional[str]) -> dict:
    """Load YAML config and apply settings overrides."""
    if not config_path:
        return {}
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with config_file.open("r") as fh:
        config = yaml.safe_load(fh) or {}

    # Apply API key / backend overrides like the CLI does
    if "api_key" in config:
        settings.set_api_key_from_config(config["api_key"])

    backend_url = config.get("backend_url") or config.get("co_datascientist_backend_url")
    backend_url_dev = config.get("backend_url_dev") or config.get("co_datascientist_backend_url_dev")
    if backend_url or backend_url_dev:
        settings.set_backend_urls_from_config(backend_url, backend_url_dev)

    return config


def _ensure_entry_command(config: dict, working_directory: Path, entry_command: Optional[str]) -> None:
    """Guarantee entry_command exists; auto-detect a sensible default."""
    if entry_command:
        config["entry_command"] = entry_command

    if config.get("entry_command"):
        return

    # Auto-detect a runnable script
    if (working_directory / "run.py").exists():
        config["entry_command"] = "python run.py"
    elif (working_directory / "main.py").exists():
        config["entry_command"] = "python main.py"
    else:
        raise ValueError(
            "No entry_command provided and could not auto-detect one. "
            "Provide entry_command (e.g., 'python your_script.py') or add run.py/main.py."
        )


@mcp.tool()
async def optimize_code(
    working_directory: str,
    entry_command: Optional[str] = None,
    config_path: Optional[str] = None,
    use_cached_qa: bool = False,
) -> str:
    """
    Start the Tropiflo workflow from MCP with the same behavior as the CLI `run` command.

    Args:
        working_directory: Absolute path to the project you want to evolve.
        entry_command: Optional run command (e.g., "python xor.py"). If omitted, tries run.py then main.py.
        config_path: Optional path to config.yaml (same as CLI). If provided, overrides entry_command/mode/urls/etc.
        use_cached_qa: Reuse previous Q&A answers to skip prompts.

    Returns:
        Status string with cost information or error message.
    """
    if workflow_runner.workflow is not None and not workflow_runner.workflow.finished:
        return "Another workflow is already in progress, cannot run more than one simultaneously. Please wait until it finishes, or ask the agent to stop it."

    project_path = Path(working_directory).resolve()
    if not project_path.exists():
        return f"Working directory does not exist: {project_path}"

    # Load config (if provided) and align with CLI defaults
    try:
        config: dict = _load_config(config_path)
    except Exception as exc:
        return f"Failed to load config: {exc}"

    # Default to local mode unless specified
    config.setdefault("mode", "local")

    # Ensure entry_command is present (required for Docker generation)
    try:
        _ensure_entry_command(config, project_path, entry_command)
    except Exception as exc:
        return str(exc)

    # Parallel & QA flags
    try:
        config["parallel"] = max(1, int(config.get("parallel", 1)))
    except Exception:
        config["parallel"] = 1
    if use_cached_qa:
        config["use_cached_qa"] = True
    else:
        # Default to skipping interactive Q&A in MCP so we don't block on server console
        config.setdefault("use_cached_qa", True)

    # Make sure we have an API key (matches CLI behavior)
    try:
        settings.get_api_key()
        if not settings.api_key or not settings.api_key.get_secret_value():
            return "No API key found. Please run 'set-token' (CLI) or add api_key to your config."
    except Exception as exc:
        return f"Error loading API key: {exc}"

    # Check usage status before starting expensive workflow
    try:
        usage_status = await co_datascientist_api.get_user_usage_status()
        usage_msg = f"\n💰 Usage Status: ${usage_status['current_usage_usd']:.2f} / ${usage_status['limit_usd']:.2f} used"

        if usage_status["is_blocked"]:
            return f"🚨 BLOCKED: Usage limit exceeded! {usage_msg}\nCannot start new workflow. Use 'get_usage_status' tool for details."
        elif usage_status["usage_percentage"] >= 90:
            usage_msg += f" ({usage_status['usage_percentage']:.1f}% - CRITICAL)"
        elif usage_status["usage_percentage"] >= 80:
            usage_msg += f" ({usage_status['usage_percentage']:.1f}% - WARNING)"
        else:
            usage_msg += f" ({usage_status['usage_percentage']:.1f}%)"
    except Exception as exc:
        usage_msg = f" (Could not check usage status: {exc})"

    print("starting workflow!")

    # Kick off the async workflow in a background thread to avoid blocking the MCP event loop
    threading.Thread(
        target=lambda: asyncio.run(
            _run_with_tee(project_path, config)
        ),
        daemon=True,
    ).start()

    return f"Workflow started successfully!{usage_msg}\n💡 Use 'check_workflow_status' to monitor progress and costs."

async def _run_with_tee(project_path: Path, config: dict):
    with _tee_output():
        await workflow_runner.run_workflow(str(project_path), config, None)

@mcp.tool()
async def stop_workflow() -> str:
    """
    schedules stopping the currently running workflow. keep using the "check_workflow_status" tool to check the workflow status until it is finished / stopped.
    """
    if workflow_runner.workflow is None:
        return "No workflow is currently running."
    print("stopping workflow...")
    workflow_runner.should_stop_workflow = True
    try:
        if getattr(workflow_runner, "workflow", None) and getattr(workflow_runner.workflow, "workflow_id", None):
            await co_datascientist_api.stop_workflow(workflow_runner.workflow.workflow_id)
    except Exception:
        # best-effort; keep returning success message
        pass
    return "Workflow scheduled to stop."


@mcp.tool()
async def check_workflow_status() -> dict:
    """
    Deprecated: use optimize_and_stream for status/logs.
    """
    return {"error": "check_workflow_status is deprecated; please poll optimize_and_stream instead."}


@mcp.tool()
async def get_events() -> dict:
    """
    Retrieve recent workflow events captured from stdout/stderr.
    Returns and clears the buffer.
    """
    with _event_lock:
        events = list(_event_buffer)
        _event_buffer.clear()
    return {"events": events}


def _status_snapshot() -> dict:
    """Lightweight status snapshot without sleeps."""
    duration_seconds = time.time() - workflow_runner.start_timestamp if getattr(workflow_runner, "start_timestamp", 0) else 0
    if workflow_runner.workflow is None:
        return {"status": "not started", "duration_seconds": duration_seconds}
    return {
        "status": workflow_runner.workflow.status_text,
        "info": workflow_runner.workflow.info,
        "finished": workflow_runner.workflow.finished,
        "duration_seconds": duration_seconds,
    }


def _start_workflow_thread(project_path: Path, config: dict):
    threading.Thread(
        target=lambda: asyncio.run(
            _run_with_tee(project_path, config)
        ),
        daemon=True,
    ).start()


@mcp.tool()
async def optimize_and_stream(
    working_directory: str,
    entry_command: Optional[str] = None,
    config_path: Optional[str] = None,
    use_cached_qa: bool = True,
) -> dict:
    """
    Start or continue an optimization workflow and stream back buffered events + status.
    Poll this, not check_workflow_status. Client guidance:
      - Do not call more often than CO_DATASCIENTIST_STREAM_MIN_POLL_SECONDS
        (default 1s). If you do, you still get events, but you'll see throttled=true
        and retry_after_seconds; respect that before the next poll.
      - Always display events_text (newline-joined events) to the user.
      - Stop polling when finished=true.
    """
    started = False
    # If no workflow or finished, start a new one
    if workflow_runner.workflow is None or getattr(workflow_runner.workflow, "finished", False):
        project_path = Path(working_directory).resolve()
        if not project_path.exists():
            return {"error": f"Working directory does not exist: {project_path}"}
        try:
            config: dict = _load_config(config_path)
        except Exception as exc:
            return {"error": f"Failed to load config: {exc}"}

        config.setdefault("mode", "local")
        try:
            _ensure_entry_command(config, project_path, entry_command)
        except Exception as exc:
            return {"error": str(exc)}

        try:
            config["parallel"] = max(1, int(config.get("parallel", 1)))
        except Exception:
            config["parallel"] = 1
        config["use_cached_qa"] = True if use_cached_qa else config.get("use_cached_qa", True)

        try:
            settings.get_api_key()
            if not settings.api_key or not settings.api_key.get_secret_value():
                return {"error": "No API key found. Please run 'set-token' or add api_key to your config."}
        except Exception as exc:
            return {"error": f"Error loading API key: {exc}"}

        _start_workflow_thread(project_path, config)
        started = True
        _push_event(f"Started workflow at {project_path} with entry_command='{config.get('entry_command')}' parallel={config.get('parallel')} engine={config.get('engine', 'EVOLVE_HYPOTHESIS')}")

    # Throttle to avoid excessive polling from clients
    global _last_stream_poll_ts
    now = time.time()
    # Gather events and status
    with _event_lock:
        events = list(_event_buffer)
        _event_buffer.clear()

    status = _status_snapshot()
    events_text = "\n".join(events) if events else ""
    if _last_stream_poll_ts and (now - _last_stream_poll_ts) < _MIN_STREAM_POLL_SECONDS:
        retry_after = max(1, int(_MIN_STREAM_POLL_SECONDS - (now - _last_stream_poll_ts)))
        return {
            "started": started,
            "status": status,
            "events": events,  # still deliver whatever was buffered
            "events_text": events_text,
            "finished": status.get("finished", False),
            "throttled": True,
            "retry_after_seconds": retry_after,
            "message": "Throttled: please wait before the next poll.",
        }

    _last_stream_poll_ts = now
    return {
        "started": started,
        "status": status,
        "events": events,
        "events_text": events_text,
        "finished": status.get("finished", False),
        "message": "No new events yet; still running" if not events else "Events included",
    }


@mcp.tool()
async def get_usage_status() -> dict:
    """
    Get your current usage status and remaining balance. Shows a quick overview similar to 'co-datascientist status' command.
    
    returns:
        dictionary with usage information including:
        - current usage vs limit
        - remaining balance  
        - usage percentage
        - status indicator
        - helpful tips
    """
    try:
        usage_status = await co_datascientist_api.get_user_usage_status()
        
        # Determine status message and emoji
        percentage = usage_status['usage_percentage']
        if usage_status['is_blocked']:
            status_msg = "🚨 BLOCKED - Free tokens exhausted! Contact support or wait for reset."
        elif percentage >= 90:
            status_msg = f"🟥 CRITICAL - Only ${usage_status['remaining_usd']:.2f} remaining!"
        elif percentage >= 80:
            status_msg = f"🟨 WARNING - Approaching limit ({percentage:.1f}% used)"
        elif percentage >= 50:
            status_msg = f"🟦 MODERATE - {percentage:.1f}% of limit used"
        else:
            status_msg = f"🟩 GOOD - Plenty of free tokens remaining"
        
        # Create progress bar representation
        bar_width = 20
        filled = int(bar_width * percentage / 100)
        bar = "█" * filled + "░" * (bar_width - filled)
        
        return {
            "summary": f"💰 Quick Usage Status",
            "used": f"${usage_status['current_usage_usd']:.2f} / ${usage_status['limit_usd']:.2f}",
            "remaining": f"${usage_status['remaining_usd']:.2f}",
            "progress_bar": f"[{bar}] {percentage:.1f}%",
            "status": status_msg,
            "is_blocked": usage_status['is_blocked'],
            "tips": [
                "Use 'get_cost_summary' for basic cost breakdown",
                "Use 'get_detailed_costs' for full analysis",
                "Monitor costs during workflows with 'check_workflow_status'"
            ]
        }
        
    except Exception as e:
        return {
            "error": f"Error getting usage status: {e}",
            "tips": ["Check your network connection", "Verify MCP server is running correctly"]
        }


@mcp.tool()
async def get_cost_summary() -> dict:
    """
    Get a summary of your usage costs and token consumption. Similar to 'co-datascientist costs' command.
    
    returns:
        dictionary with cost summary including:
        - total cost
        - usage limits
        - token counts
        - workflow counts
    """
    try:
        costs_response = await co_datascientist_api.get_user_costs_summary()
        usage_status = await co_datascientist_api.get_user_usage_status()
        
        # Status indicator
        if usage_status['is_blocked']:
            status_indicator = "🚨 BLOCKED - Free tokens exhausted!"
            status_detail = f"You've used ${usage_status['current_usage_usd']:.2f} of your ${usage_status['limit_usd']:.2f} limit."
        elif usage_status['usage_percentage'] >= 80:
            status_indicator = f"⚠️  Approaching limit - {usage_status['usage_percentage']:.1f}% used"
            status_detail = f"${usage_status['remaining_usd']:.2f} remaining"
        else:
            status_indicator = f"✅ Active - {usage_status['usage_percentage']:.1f}% of limit used"
            status_detail = f"${usage_status['remaining_usd']:.2f} remaining"
        
        return {
            "title": "💰 Co-DataScientist Usage Summary",
            "total_cost": f"${costs_response['total_cost_usd']:.8f}",
            "usage_limit": f"${usage_status['limit_usd']:.2f}",
            "remaining": f"${usage_status['remaining_usd']:.2f} ({usage_status['usage_percentage']:.1f}% used)",
            "status": status_indicator,
            "status_detail": status_detail,
            "total_tokens": f"{costs_response['total_tokens']:,}",
            "workflows_completed": costs_response['workflows_completed'],
            "last_updated": costs_response.get('last_updated', 'Unknown'),
            "tip": "💡 Use 'get_detailed_costs' for full breakdown"
        }
        
    except Exception as e:
        return {
            "error": f"Error getting cost summary: {e}",
            "tip": "Check your connection and try again"
        }


@mcp.tool()
async def get_detailed_costs() -> dict:
    """
    Get detailed cost breakdown including all workflows and model calls. Similar to 'co-datascientist costs --detailed' command.
    
    returns:
        dictionary with detailed cost information including:
        - total costs and limits
        - per-workflow breakdown
        - model call details
        - usage status
    """
    try:
        costs_response = await co_datascientist_api.get_user_costs()
        usage_status = await co_datascientist_api.get_user_usage_status()
        
        # Status with emoji
        if usage_status['is_blocked']:
            status_msg = f"🚨 Status: BLOCKED (limit exceeded)"
        elif usage_status['usage_percentage'] >= 80:
            status_msg = f"⚠️  Status: Approaching limit ({usage_status['usage_percentage']:.1f}%)"
        else:
            status_msg = f"✅ Status: Active ({usage_status['usage_percentage']:.1f}% used)"
        
        # Build workflow breakdown
        workflow_breakdown = []
        if costs_response['workflows']:
            for workflow_id, workflow_data in costs_response['workflows'].items():
                workflow_info = {
                    "id": workflow_id[:8] + "...",
                    "cost": f"${workflow_data['cost']:.8f}",
                    "tokens": f"{workflow_data['input_tokens'] + workflow_data['output_tokens']:,}",
                    "model_calls": len(workflow_data['model_calls'])
                }
                
                # Add recent model calls
                recent_calls = []
                for call in workflow_data['model_calls'][-3:]:  # Last 3 calls
                    recent_calls.append({
                        "model": call['model'],
                        "cost": f"${call['cost']:.8f}",
                        "tokens": f"{call['input_tokens']}+{call['output_tokens']}"
                    })
                workflow_info["recent_calls"] = recent_calls
                
                if len(workflow_data['model_calls']) > 3:
                    workflow_info["additional_calls"] = len(workflow_data['model_calls']) - 3
                
                workflow_breakdown.append(workflow_info)
        
        return {
            "title": "💰 Co-DataScientist Usage Details",
            "total_cost": f"${costs_response['total_cost_usd']:.8f}",
            "usage_limit": f"${usage_status['limit_usd']:.2f}",
            "remaining": f"${usage_status['remaining_usd']:.2f}",
            "usage_percentage": f"{usage_status['usage_percentage']:.1f}%",
            "status": status_msg,
            "total_tokens": f"{costs_response['total_tokens']:,} ({costs_response['total_input_tokens']:,} input + {costs_response['total_output_tokens']:,} output)",
            "workflows_count": costs_response['workflows_count'],
            "last_updated": costs_response.get('last_updated', 'Unknown'),
            "workflow_breakdown": workflow_breakdown
        }
        
    except Exception as e:
        return {
            "error": f"Error getting detailed costs: {e}",
            "tip": "Check your connection and try again"
        }


async def run_mcp_server():
    # Use SSE transport so IDE clients can connect over HTTP
    # Default away from 8000 to avoid clashing with backend; env overrides still respected
    port = int(os.getenv("CO_DATASCIENTIST_MCP_PORT", "8765"))
    await mcp.run_async(
        transport="sse",
        host=settings.host,
        port=port,
    )
