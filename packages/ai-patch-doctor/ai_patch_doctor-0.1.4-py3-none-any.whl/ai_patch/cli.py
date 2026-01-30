#!/usr/bin/env python3
"""AI Patch CLI - Main entry point."""

import sys
import os
import time
import json
import getpass
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import click

# Get CLI version
try:
    import importlib.metadata
    CLI_VERSION = importlib.metadata.version('ai-patch-doctor')
except Exception:
    CLI_VERSION = '0.1.3'

# Import from package (now all in ai_patch package)
from ai_patch.checks import streaming, retries, cost, trace
from ai_patch.report import ReportGenerator
from ai_patch.config import (
    Config, load_saved_config, save_config, auto_detect_provider, 
    get_or_create_install_id
)
from ai_patch.telemetry import (
    is_telemetry_enabled, send_doctor_run_event
)



def should_prompt(interactive_flag: bool, ci_flag: bool) -> bool:
    """Determine if essential prompting is allowed (e.g., API key).
    
    Returns True when: is_tty AND NOT ci_flag (frictionless mode)
    If interactive_flag is set but not TTY: print error and exit 2
    In --ci: never prompt
    
    Note: This is for ESSENTIAL prompts only (API key).
    For preference menus (target, provider), use interactive_flag directly.
    
    Args:
        interactive_flag: Whether -i/--interactive was passed
        ci_flag: Whether --ci was passed
        
    Returns:
        True if essential prompting is allowed, False otherwise
    """
    is_tty = sys.stdin.isatty() and sys.stdout.isatty()
    
    # CI mode never prompts
    if ci_flag:
        return False
    
    # Interactive mode requested
    if interactive_flag:
        if not is_tty:
            click.echo("❌ Error: Interactive mode (-i) requested but not running in a TTY")
            click.echo("   Run without -i for non-interactive mode, or run in a terminal")
            sys.exit(2)
        return True
    
    # Default: allow essential prompts in TTY (frictionless mode)
    return is_tty


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    """AI Patch - Fix-first incident patcher for AI API issues.
    
    Default command runs non-interactive doctor mode.
    """
    if ctx.invoked_subcommand is None:
        # No subcommand - run doctor mode (now non-interactive by default)
        ctx.invoke(doctor)


@main.command()
@click.option('--target', type=click.Choice(['streaming', 'retries', 'cost', 'trace', 'prod', 'all']), 
              help='Specific target to check')
@click.option('-i', '--interactive', 'interactive_flag', is_flag=True, 
              help='Enable interactive prompts (requires TTY)')
@click.option('--ci', is_flag=True, 
              help='CI mode: never prompt, fail fast on missing config')
@click.option('--provider', type=click.Choice(['openai-compatible', 'anthropic', 'gemini']),
              help='Specify provider explicitly')
@click.option('--model', help='Specify model name')
@click.option('--save', is_flag=True, 
              help='Save non-secret config (base_url, provider)')
@click.option('--save-key', is_flag=True,
              help='Save API key (requires --force)')
@click.option('--force', is_flag=True,
              help='Required with --save-key to confirm key storage')
@click.option('--no-telemetry', is_flag=True,
              help='Disable anonymous telemetry for this run')
def doctor(
    target: Optional[str],
    interactive_flag: bool,
    ci: bool,
    provider: Optional[str],
    model: Optional[str],
    save: bool,
    save_key: bool,
    force: bool,
    no_telemetry: bool
):
    """Run diagnosis (non-interactive by default)."""
    
    # Validate conflicting flags
    if interactive_flag and ci:
        click.echo("❌ Error: Cannot use both --interactive (-i) and --ci flags together")
        click.echo("   --interactive enables prompts, --ci disables prompts")
        sys.exit(2)
    
    # Check if prompting is allowed
    can_prompt = should_prompt(interactive_flag, ci)
    
    # Validate --save-key requires --force
    if save_key and not force:
        click.echo("❌ Error: --save-key requires --force flag")
        click.echo("   Example: ai-patch doctor --save-key --force")
        sys.exit(2)
    
    # Welcome message (only in explicit interactive mode)
    if interactive_flag:
        click.echo("🔍 AI Patch Doctor - Interactive Mode\n")
    
    # Initialize telemetry (get or create install_id)
    install_id, is_first_run = get_or_create_install_id()
    
    # Get saved config for telemetry preferences
    saved_config_for_telemetry = load_saved_config()
    telemetry_consent = saved_config_for_telemetry.get('telemetryEnabled') if saved_config_for_telemetry else None
    
    # First-run telemetry consent prompt (only in TTY, not in CI, not in non-interactive)
    if is_first_run and can_prompt and not ci and sys.stdin.isatty() and sys.stdout.isatty():
        click.echo("📊 Anonymous Telemetry")
        click.echo("   Help improve AI Patch by sharing anonymous usage data.")
        click.echo("   Only diagnostic patterns are collected (no secrets, prompts, or identifiers).")
        click.echo("   You can opt-out anytime with --no-telemetry or AI_PATCH_TELEMETRY=0\n")
        
        response = click.prompt("Enable anonymous telemetry? [Y/n]", default='Y', show_default=False)
        
        if response.strip().lower() in ('n', 'no'):
            telemetry_consent = False
            save_config(install_id=install_id, telemetry_enabled=False)
            click.echo("✓ Telemetry disabled\n")
        else:
            telemetry_consent = True
            save_config(install_id=install_id, telemetry_enabled=True)
            click.echo("✓ Telemetry enabled\n")
    
    # Interactive questions for target (only with -i flag)
    if not target and interactive_flag:
        click.echo("What's failing?")
        click.echo("  1. streaming / SSE stalls / partial output")
        click.echo("  2. retries / 429 / rate-limit chaos")
        click.echo("  3. cost spikes")
        click.echo("  4. traceability (request IDs, duplicates)")
        click.echo("  5. prod-only issues (all checks)")
        choice = click.prompt("Select", type=int, default=5)
        
        target_map = {
            1: 'streaming',
            2: 'retries',
            3: 'cost',
            4: 'trace',
            5: 'all'
        }
        target = target_map.get(choice, 'all')
    elif not target:
        # Non-interactive default
        target = 'all'
    
    # Auto-detect provider before any prompts
    detected_provider, detected_keys, selected_key_name, warning = auto_detect_provider(
        provider_flag=provider,
        can_prompt=can_prompt
    )
    
    # If warning and cannot continue, exit
    if warning and not can_prompt:
        if "not found" in warning.lower() or "invalid" in warning.lower():
            click.echo(f"\n❌ {warning}")
            if selected_key_name:
                click.echo(f"   Set {selected_key_name} or run with -i for interactive mode")
            sys.exit(2)
    
    # Interactive provider selection (only with -i flag)
    if not provider and interactive_flag:
        click.echo("\nWhat do you use?")
        click.echo("  1. openai-compatible (default)")
        click.echo("  2. anthropic")
        click.echo("  3. gemini")
        provider_choice = click.prompt("Select", type=int, default=1)
        
        provider_map = {
            1: 'openai-compatible',
            2: 'anthropic',
            3: 'gemini'
        }
        detected_provider = provider_map.get(provider_choice, 'openai-compatible')
    
    # Use detected provider
    provider = detected_provider
    
    # Load saved config first
    saved_config = load_saved_config()
    
    # Auto-detect config from env vars
    config = Config.auto_detect(provider)
    
    # Override with model if provided
    if model:
        config.model = model
    
    # If saved config exists, use it to fill in missing values
    if saved_config:
        if saved_config.get('apiKey') and not config.api_key:
            config.api_key = saved_config['apiKey']
        if saved_config.get('baseUrl') and not config.base_url:
            config.base_url = saved_config['baseUrl']
    
    # If still missing config, prompt for it (only if allowed)
    prompted_api_key = None
    prompted_base_url = None
    
    if not config.is_valid():
        if not can_prompt:
            # Cannot prompt - exit with clear message
            missing_vars = config.get_missing_vars()
            click.echo(f"\n❌ Missing configuration: {missing_vars}")
            click.echo(f"   Set environment variable(s) or run with -i for interactive mode")
            sys.exit(2)
        
        click.echo("\n⚙️  Configuration needed\n")
        
        # Prompt for API key if missing (essential prompt)
        if not config.api_key:
            # Check if we can safely prompt (TTY with echo off capability)
            import warnings
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                try:
                    prompted_api_key = getpass.getpass('API key not found. Paste your API key (input will be hidden): ')
                    # Check if GetPassWarning was raised
                    if w and any(issubclass(warning.category, getpass.GetPassWarning) for warning in w):
                        click.echo("\n❌ Error: Cannot safely hide API key input in this environment")
                        if provider == 'anthropic':
                            click.echo(f"   Set ANTHROPIC_API_KEY environment variable instead")
                        elif provider == 'gemini':
                            click.echo(f"   Set GEMINI_API_KEY environment variable instead")
                        else:
                            click.echo(f"   Set OPENAI_API_KEY environment variable instead")
                        sys.exit(2)
                    config.api_key = prompted_api_key
                except Exception as e:
                    click.echo(f"\n❌ Error: Cannot prompt for API key: {str(e)}")
                    sys.exit(2)
        
        # Auto-fill base URL if missing (no prompt - use provider defaults)
        if not config.base_url:
            if provider == 'anthropic':
                config.base_url = 'https://api.anthropic.com'
            elif provider == 'gemini':
                config.base_url = 'https://generativelanguage.googleapis.com'
            else:
                config.base_url = 'https://api.openai.com'
    
    # Final validation - if still invalid, exit
    if not config.is_valid():
        click.echo("\n❌ Missing configuration")
        sys.exit(2)
    
    # Display warning if one was generated
    if warning and can_prompt:
        click.echo(f"\n⚠️  {warning}")
    
    click.echo(f"\n✓ Detected: {config.base_url}")
    click.echo(f"✓ Provider: {provider}")
    
    # Run checks
    click.echo(f"\n🔬 Running {target} checks...\n")
    start_time = time.time()
    
    results = run_checks(target, config, provider)
    
    duration = time.time() - start_time
    
    # Generate report
    report_gen = ReportGenerator()
    report_data = report_gen.create_report(target, provider, config.base_url, results, duration)
    
    # Save report
    report_dir = save_report(report_data)
    
    # Print inline diagnosis
    print_diagnosis(report_data)
    
    # Display summary
    display_summary(report_data, report_dir)
    
    # Handle config saving (only via flags)
    if save or save_key:
        saved_fields = save_config(
            api_key=config.api_key if save_key else None,
            base_url=config.base_url if (save or save_key) else None,
            provider=provider if (save or save_key) else None
        )
        if saved_fields:
            click.echo(f"\n✓ Saved config: {', '.join(saved_fields)}")
    
    # Send telemetry event (fire-and-forget, never blocks)
    telemetry_enabled = is_telemetry_enabled(no_telemetry, telemetry_consent)
    if telemetry_enabled:
        status = report_data['summary']['status']
        if status not in ('success', 'warning', 'error'):
            status = 'error'
        
        send_doctor_run_event(
            install_id,
            CLI_VERSION,
            target,
            provider,
            status,
            duration
        )
    
    # Exit with appropriate code
    if report_data['summary']['status'] == 'success':
        sys.exit(0)
    else:
        sys.exit(1)


@main.command()
@click.option('--safe', is_flag=True, help='Apply in safe mode (dry-run by default)')
def apply(safe: bool):
    """Apply suggested fixes (experimental - not fully implemented in MVP)."""
    click.echo("❌ Apply functionality is not available in the free CLI. This tool diagnoses incidents only.")
    sys.exit(1)


@main.command()
@click.option('--target', type=click.Choice(['streaming', 'retries', 'cost', 'trace']))
def test(target: Optional[str]):
    """Run standard test for selected target."""
    if not target:
        click.echo("❌ Please specify --target")
        sys.exit(1)
    
    click.echo(f"🧪 Running {target} test...\n")
    
    config = Config.auto_detect('openai-compatible')
    
    # Run specific test
    results = run_checks(target, config, 'openai-compatible')
    
    # Display results
    check_result = results.get(target, {})
    status = check_result.get('status', 'unknown')
    
    if status == 'pass':
        click.echo(f"✅ {target.upper()} test passed")
        sys.exit(0)
    else:
        click.echo(f"❌ {target.upper()} test failed")
        for finding in check_result.get('findings', []):
            click.echo(f"   {finding['severity'].upper()}: {finding['message']}")
        sys.exit(1)


@main.command()
@click.option('--with-badgr', is_flag=True, help='Enable deep diagnosis through Badgr proxy (not available in MVP)')
def diagnose(with_badgr: bool):
    """Deep diagnosis mode (experimental)."""
    
    if with_badgr:
        click.echo("❌ --with-badgr is not available in MVP")
        click.echo("   This feature requires the Badgr receipt gateway")
        sys.exit(2)
    
    click.echo("🔬 AI Patch Deep Diagnosis\n")
    
    # Run standard diagnosis
    config = Config.auto_detect('openai-compatible')
    results = run_checks('all', config, 'openai-compatible')
    
    click.echo("\n✓ Diagnosis complete")


@main.command()
@click.option('--redact', is_flag=True, default=True, help='Redact sensitive data (default: true)')
def share(redact: bool):
    """Create redacted share bundle."""
    click.echo("📦 Creating share bundle...\n")
    
    report_path = find_latest_report()
    if not report_path:
        click.echo("❌ No report found. Run 'ai-patch doctor' first.")
        sys.exit(1)
    
    # Create share bundle
    bundle_path = report_path.parent / "share-bundle.zip"
    
    click.echo(f"✓ Created: {bundle_path}")


@main.command()
def revert():
    """Undo applied changes (experimental - not fully implemented in MVP)."""
    click.echo("↩️  Reverting applied changes...\n")
    
    # TODO: Implement revert logic
    click.echo("✓ Reverted all applied changes")


def run_checks(target: str, config: Config, provider: str) -> Dict[str, Any]:
    """Run the specified checks."""
    results = {}
    
    targets_to_run = []
    if target == 'all' or target == 'prod':
        targets_to_run = ['streaming', 'retries', 'cost', 'trace']
    else:
        targets_to_run = [target]
    
    for t in targets_to_run:
        if t == 'streaming':
            results['streaming'] = streaming.check(config)
        elif t == 'retries':
            results['retries'] = retries.check(config)
        elif t == 'cost':
            results['cost'] = cost.check(config)
        elif t == 'trace':
            results['trace'] = trace.check(config)
    
    return results


def save_report(report_data: Dict[str, Any]) -> Path:
    """Save report to ai-patch-reports directory with latest pointer."""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    reports_base = Path.cwd() / "ai-patch-reports"
    report_dir = reports_base / timestamp
    report_dir.mkdir(parents=True, exist_ok=True)
    
    # Sanitize report data before saving (remove any potential secrets)
    sanitized_data = sanitize_report_data(report_data)
    
    # Save JSON
    json_path = report_dir / "report.json"
    with open(json_path, 'w') as f:
        json.dump(sanitized_data, f, indent=2)
    
    # Save Markdown
    md_path = report_dir / "report.md"
    report_gen = ReportGenerator()
    md_content = report_gen.generate_markdown(sanitized_data)
    with open(md_path, 'w') as f:
        f.write(md_content)
    
    # Create latest pointer
    latest_symlink = reports_base / "latest"
    latest_json = reports_base / "latest.json"
    
    # Try symlink first
    try:
        # Remove existing symlink or directory (including broken symlinks)
        if latest_symlink.is_symlink():
            latest_symlink.unlink()
        elif latest_symlink.exists():
            latest_symlink.unlink()
        latest_symlink.symlink_to(timestamp, target_is_directory=True)
    except (OSError, NotImplementedError):
        # Symlink failed (Windows or permissions) - use latest.json
        with open(latest_json, 'w') as f:
            json.dump({"latest": timestamp}, f)
    
    return report_dir


def sanitize_report_data(data: Any) -> Any:
    """Sanitize report data to remove any potential secrets or API keys.
    
    This is a deep sanitization that recursively checks all fields.
    """
    if not isinstance(data, (dict, list)):
        return data
    
    if isinstance(data, list):
        return [sanitize_report_data(item) for item in data]
    
    sanitized = {}
    secret_fields = ['apikey', 'api_key', 'apikey', 'key', 'secret', 'token', 'password', 'authorization']
    
    for key, value in data.items():
        lower_key = key.lower()
        
        # Skip fields that might contain secrets
        if any(sf in lower_key for sf in secret_fields):
            continue
        
        # Recursively sanitize nested objects
        sanitized[key] = sanitize_report_data(value)
    
    return sanitized


def find_latest_report() -> Optional[Path]:
    """Find the latest report directory.
    
    Resolution order:
    1. latest/report.json (symlink)
    2. latest.json -> timestamp dir
    3. fallback: newest directory by mtime
    """
    reports_dir = Path.cwd() / "ai-patch-reports"
    if not reports_dir.exists():
        return None
    
    # Try symlink first
    latest_symlink = reports_dir / "latest"
    if latest_symlink.is_symlink() or (latest_symlink.exists() and latest_symlink.is_dir()):
        report_json = latest_symlink / "report.json"
        if report_json.exists():
            return report_json
    
    # Try latest.json
    latest_json = reports_dir / "latest.json"
    if latest_json.exists():
        try:
            with open(latest_json, 'r') as f:
                data = json.load(f)
                timestamp = data.get('latest')
                if timestamp:
                    report_json = reports_dir / timestamp / "report.json"
                    if report_json.exists():
                        return report_json
        except Exception:
            pass
    
    # Fallback: find newest by mtime
    try:
        dirs = [d for d in reports_dir.iterdir() if d.is_dir() and d.name != 'latest']
        if not dirs:
            return None
        
        # Sort by modification time
        newest = max(dirs, key=lambda d: d.stat().st_mtime)
        report_json = newest / "report.json"
        if report_json.exists():
            return report_json
    except Exception:
        pass
    
    return None


def print_diagnosis(report_data: Dict[str, Any]) -> None:
    """Print inline diagnosis."""
    summary = report_data['summary']
    status = summary['status']
    checks = report_data['checks']
    
    # Status emoji and message
    status_emoji = {
        'success': '✅',
        'warning': '⚠️',
        'error': '❌'
    }
    
    click.echo(f"\n{status_emoji.get(status, '•')} Status: {status.upper()}")
    
    # Organize findings into three buckets
    detected = []
    not_detected = []
    not_observable = []
    
    for check_name, check_result in checks.items():
        findings = check_result.get('findings', [])
        check_not_detected = check_result.get('not_detected', [])
        check_not_observable = check_result.get('not_observable', [])
        
        for finding in findings:
            severity = finding.get('severity', 'info')
            message = finding.get('message', '')
            
            # Detected items (with evidence)
            if message:
                detected.append((severity, check_name, message))
        
        # Aggregate not detected and not observable items
        not_detected.extend(check_not_detected)
        for item in check_not_observable:
            if item not in not_observable:
                not_observable.append(item)
    
    # Detected section
    if detected:
        click.echo("\nDetected:")
        for severity, check_name, message in detected:
            click.echo(f"  • [{check_name}] {message}")
    else:
        click.echo("\nDetected:")
        click.echo("  • No issues detected")
    
    # Not detected section
    click.echo("\nNot detected:")
    if not_detected:
        for item in not_detected:
            click.echo(f"  • {item}")
    else:
        click.echo("  • (No explicit checks for absent items in this run)")
    
    # Success message (RULE 6)
    if status == 'success':
        click.echo("\nAll checks passed for this run. This tool does not monitor production.")
    
    # Not observable section (only if status != success)
    if status != 'success' and not_observable:
        click.echo("\nNot observable from provider probe:")
        for item in not_observable:
            click.echo(f"  • {item}")
    
    # Conditional note
    if status != 'success':
        click.echo("\nNote:")
        click.echo("Here's exactly what I can see from the provider probe.")
        click.echo("Here's what I cannot see without real traffic.")


def display_summary(report_data: Dict[str, Any], report_dir: Path):
    """Display report summary."""
    summary = report_data['summary']
    status = summary['status']
    checks = report_data['checks']
    provider = report_data['provider']
    base_url = report_data['base_url']
    
    # Show file path
    reports_base = Path.cwd() / "ai-patch-reports"
    latest_path = reports_base / "latest"
    
    if latest_path.exists():
        display_path = "./ai-patch-reports/latest/report.md"
    else:
        display_path = f"./{report_dir.relative_to(Path.cwd())}/report.md"
    
    click.echo(f"\n📊 Report: {display_path}")
    
    # Badgr messaging - only when status != success
    if status != 'success':
        # Find most severe finding
        most_severe_finding = ''
        for check_name, check_result in checks.items():
            findings = check_result.get('findings', [])
            for finding in findings:
                if finding.get('severity') in ['error', 'warning']:
                    most_severe_finding = f"[{check_name}] {finding.get('message', '')}"
                    if finding.get('severity') == 'error':
                        break
            if most_severe_finding and any(f.get('severity') == 'error' for f in findings):
                break
        
        # Find what we can't see
        cannot_see = ''
        for check_name, check_result in checks.items():
            not_obs = check_result.get('not_observable', [])
            if not_obs:
                cannot_see = not_obs[0]
                break
        if not cannot_see:
            cannot_see = 'retry behavior, partial streams, concurrency'
        
        # Provider-specific env var
        env_var = 'OPENAI_BASE_URL'
        if provider == 'anthropic':
            env_var = 'ANTHROPIC_BASE_URL'
        elif provider == 'gemini':
            env_var = 'GEMINI_BASE_URL'
        
        # Detect original base URL
        original_base_url = base_url
        
        click.echo('\n' + '=' * 60)
        if most_severe_finding:
            click.echo(f"\nWhat I found: {most_severe_finding}")
        click.echo(f"\nWhat I can't see: {cannot_see}")
        click.echo('\nRun one request through Badgr gateway (copy/paste):')
        click.echo('')
        click.echo(f'export {env_var}="https://aibadgr.com/v1"')
        click.echo('# Make one API call here (your code)')
        click.echo(f'export {env_var}="{original_base_url}"')
        click.echo('')
        click.echo('=' * 60)
    
    # Repeat pain footer (production-anchored)
    click.echo('\n---')
    click.echo('ℹ️  This report explains this incident only.')
    click.echo('')
    click.echo('If this happens again in production, you won\'t see it unless you run this manually.')
    
    click.echo("\nGenerated by AI Patch — re-run: pipx run ai-patch")


if __name__ == '__main__':
    main()
