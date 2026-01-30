"""Telemetry module for anonymous usage tracking using PostHog.

Purpose: Help maintainers understand which AI issues users are facing
Privacy: No user identification, tracking, or sensitive data collection

Collected data:
- install_id (random UUID, locally generated on first run)
- cli_version
- os, arch
- target (check type)
- provider_type
- status (success/warning/error)
- duration_bucket

Note: PostHog automatically adds timestamp to events

Strictly forbidden:
- Prompts, payloads, request bodies
- API keys, base URLs, file paths
- Repo names, model names
- Any user or company identifiers
"""

import os
import platform
import uuid
from typing import Optional, Dict, Any
from posthog import Posthog

# PostHog configuration
# Write-only API key - safe to use in public apps
POSTHOG_API_KEY = 'phc_FrjAyzOmzkxySC7qssHHCgtCZYMaXkmvl7Zb1MqAtnK'
POSTHOG_HOST = 'https://us.i.posthog.com'
EVENT_NAME = 'doctor_run'

# Initialize PostHog client
_posthog_client = None


def get_posthog_client() -> Posthog:
    """Get or create PostHog client singleton."""
    global _posthog_client
    if _posthog_client is None:
        _posthog_client = Posthog(
            api_key=POSTHOG_API_KEY,
            host=POSTHOG_HOST,
        )
    return _posthog_client


def generate_install_id() -> str:
    """Generate a random install_id (UUID v4)."""
    return str(uuid.uuid4())


def get_duration_bucket(duration_seconds: float) -> str:
    """Calculate duration bucket for anonymization.
    
    Buckets: <1s, 1-5s, 5-10s, 10-30s, 30-60s, >60s
    """
    if duration_seconds < 1:
        return '<1s'
    elif duration_seconds < 5:
        return '1-5s'
    elif duration_seconds < 10:
        return '5-10s'
    elif duration_seconds < 30:
        return '10-30s'
    elif duration_seconds < 60:
        return '30-60s'
    else:
        return '>60s'


def is_telemetry_enabled(
    no_telemetry_flag: bool,
    config_telemetry_enabled: Optional[bool]
) -> bool:
    """Check if telemetry is enabled based on multiple opt-out mechanisms.
    
    Respects:
    - --no-telemetry flag
    - AI_PATCH_TELEMETRY=0 environment variable
    - telemetryEnabled=false in config
    
    Default: enabled (opt-out model)
    """
    # Check flag first
    if no_telemetry_flag:
        return False
    
    # Check environment variable
    env_value = os.getenv('AI_PATCH_TELEMETRY')
    if env_value in ('0', 'false', 'False', 'FALSE'):
        return False
    
    # Check config (default to true if not specified)
    if config_telemetry_enabled is False:
        return False
    
    return True


def send_telemetry_event(install_id: str, properties: Dict[str, Any]) -> None:
    """Send telemetry event using PostHog (fire-and-forget).
    
    - Never blocks or slows the CLI
    - Fails silently on network errors
    - Never changes CLI exit codes
    """
    try:
        client = get_posthog_client()
        
        # Capture event with PostHog
        client.capture(
            distinct_id=install_id,
            event=EVENT_NAME,
            properties=properties,
        )
        
        # Flush to ensure event is sent
        client.flush()
    except Exception:
        # Silently ignore all errors
        pass


def send_doctor_run_event(
    install_id: str,
    cli_version: str,
    target: str,
    provider: str,
    status: str,
    duration_seconds: float
) -> None:
    """Create and send a doctor_run telemetry event."""
    properties = {
        'cli_version': cli_version,
        'os': platform.system().lower(),
        'arch': platform.machine(),
        'target': target,
        'provider_type': provider,
        'status': status,
        'duration_bucket': get_duration_bucket(duration_seconds),
    }
    
    send_telemetry_event(install_id, properties)
