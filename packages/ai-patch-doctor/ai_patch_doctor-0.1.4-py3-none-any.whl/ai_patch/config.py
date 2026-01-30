"""Configuration management for AI Patch."""

import os
import json
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass

# Import after module is created
try:
    from .telemetry import generate_install_id
except ImportError:
    # Fallback for development
    import uuid
    def generate_install_id() -> str:
        return str(uuid.uuid4())


@dataclass
class Config:
    """Configuration for AI Patch checks."""
    
    base_url: str
    api_key: str
    provider: str
    model: Optional[str] = None
    
    @classmethod
    def auto_detect(cls, provider: str = 'openai-compatible') -> 'Config':
        """Auto-detect configuration from environment variables."""
        
        if provider == 'openai-compatible':
            base_url = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com')
            api_key = os.getenv('OPENAI_API_KEY', '')
            model = os.getenv('MODEL', 'gpt-3.5-turbo')
            
            # Check for common gateway env vars
            if not base_url or base_url == 'https://api.openai.com':
                # Try LiteLLM proxy
                litellm_url = os.getenv('LITELLM_PROXY_URL')
                if litellm_url:
                    base_url = litellm_url
                
                # Try Portkey
                portkey_url = os.getenv('PORTKEY_BASE_URL')
                if portkey_url:
                    base_url = portkey_url
                    
                # Try Helicone
                helicone_url = os.getenv('HELICONE_BASE_URL')
                if helicone_url:
                    base_url = helicone_url
        
        elif provider == 'anthropic':
            base_url = os.getenv('ANTHROPIC_BASE_URL', 'https://api.anthropic.com')
            api_key = os.getenv('ANTHROPIC_API_KEY', '')
            model = os.getenv('MODEL', 'claude-3-5-sonnet-20241022')
        
        elif provider == 'gemini':
            base_url = os.getenv('GEMINI_BASE_URL', 'https://generativelanguage.googleapis.com')
            api_key = os.getenv('GEMINI_API_KEY', '')
            model = os.getenv('MODEL', 'gemini-pro')
        
        else:
            base_url = os.getenv('OPENAI_BASE_URL', '')
            api_key = os.getenv('OPENAI_API_KEY', '')
            model = os.getenv('MODEL', 'gpt-3.5-turbo')
        
        return cls(
            base_url=base_url,
            api_key=api_key,
            provider=provider,
            model=model
        )
    
    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        return bool(self.base_url and self.api_key)
    
    def get_missing_vars(self) -> str:
        """Get list of missing environment variables."""
        missing = []
        
        if not self.base_url:
            if self.provider == 'anthropic':
                missing.append('ANTHROPIC_BASE_URL')
            elif self.provider == 'gemini':
                missing.append('GEMINI_BASE_URL')
            else:
                missing.append('OPENAI_BASE_URL')
        
        if not self.api_key:
            if self.provider == 'anthropic':
                missing.append('ANTHROPIC_API_KEY')
            elif self.provider == 'gemini':
                missing.append('GEMINI_API_KEY')
            else:
                missing.append('OPENAI_API_KEY')
        
        return ', '.join(missing)


def load_saved_config() -> Optional[Dict[str, Any]]:
    """Load saved configuration from home directory (~/.ai-patch/config.json).
    
    Returns:
        Dictionary with config fields, or None if file doesn't exist or can't be read
    """
    try:
        home_dir = Path.home()
        config_path = home_dir / '.ai-patch' / 'config.json'
        
        if not config_path.exists():
            return None
        
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        return {
            'apiKey': config_data.get('apiKey'),
            'baseUrl': config_data.get('baseUrl'),
            'provider': config_data.get('provider'),
            'installId': config_data.get('installId'),
            'telemetryEnabled': config_data.get('telemetryEnabled')
        }
    except Exception:
        # Silently fail and return None
        return None


def save_config(
    api_key: Optional[str] = None, 
    base_url: Optional[str] = None,
    provider: Optional[str] = None,
    install_id: Optional[str] = None,
    telemetry_enabled: Optional[bool] = None
) -> List[str]:
    """Save configuration to home directory (~/.ai-patch/config.json).
    
    Creates directory if it doesn't exist.
    Sets permissions to 0600 on Unix systems.
    
    Args:
        api_key: API key to save
        base_url: Base URL to save
        provider: Provider to save
        install_id: Install ID to save
        telemetry_enabled: Telemetry preference to save
        
    Returns:
        List of fields that were saved
    """
    try:
        home_dir = Path.home()
        config_dir = home_dir / '.ai-patch'
        config_path = config_dir / 'config.json'
        
        # Create directory if it doesn't exist
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing config if it exists
        existing_config = {}
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    existing_config = json.load(f)
            except Exception:
                pass
        
        # Prepare config data
        config_data = existing_config.copy()
        saved_fields = []
        
        if api_key:
            config_data['apiKey'] = api_key
            saved_fields.append('api_key')
        if base_url:
            config_data['baseUrl'] = base_url
            saved_fields.append('base_url')
        if provider:
            config_data['provider'] = provider
            saved_fields.append('provider')
        if install_id:
            config_data['installId'] = install_id
            saved_fields.append('install_id')
        if telemetry_enabled is not None:
            config_data['telemetryEnabled'] = telemetry_enabled
            saved_fields.append('telemetry_enabled')
        
        # Write config file
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        # On Unix, set permissions to 0600
        if os.name != 'nt':  # Not Windows
            try:
                os.chmod(config_path, 0o600)
            except Exception:
                # Ignore chmod errors
                pass
        
        return saved_fields
    except Exception as e:
        print(f'Warning: Could not save config.')
        return []


def auto_detect_provider(
    provider_flag: Optional[str] = None,
    can_prompt: bool = False
) -> Tuple[str, List[str], Optional[str], Optional[str]]:
    """Auto-detect provider from environment variables.
    
    Args:
        provider_flag: Explicit provider from --provider flag
        can_prompt: Whether prompting is allowed (for validation)
        
    Returns:
        Tuple of (provider, detected_keys_list, selected_key_name, warning_message)
    """
    # Define provider order and their corresponding env var names
    provider_keys = {
        'openai-compatible': 'OPENAI_API_KEY',
        'anthropic': 'ANTHROPIC_API_KEY',
        'gemini': 'GEMINI_API_KEY'
    }
    
    # Check which keys exist in environment
    detected_keys = []
    for prov, key_name in provider_keys.items():
        if os.getenv(key_name):
            detected_keys.append(prov)
    
    warning_message = None
    selected_provider = None
    selected_key_name = None
    
    # If --provider is provided, validate it
    if provider_flag:
        if provider_flag not in provider_keys:
            # Invalid provider
            return (provider_flag, detected_keys, None, f"Invalid provider: {provider_flag}")
        
        # Check if provider has key in env
        if provider_flag not in detected_keys:
            if can_prompt:
                # Allow user to paste key interactively
                warning_message = f"{provider_keys[provider_flag]} not found in environment"
            else:
                return (provider_flag, detected_keys, None, 
                       f"Provider '{provider_flag}' specified but {provider_keys[provider_flag]} not found")
        
        selected_provider = provider_flag
        selected_key_name = provider_keys.get(provider_flag)
    
    # If exactly one key exists, use it
    elif len(detected_keys) == 1:
        selected_provider = detected_keys[0]
        selected_key_name = provider_keys[selected_provider]
    
    # If multiple keys exist, use heuristics
    elif len(detected_keys) > 1:
        # Prefer provider with custom base URL env var set
        for prov in detected_keys:
            if prov == 'openai-compatible' and os.getenv('OPENAI_BASE_URL'):
                selected_provider = prov
                selected_key_name = provider_keys[prov]
                break
            elif prov == 'anthropic' and os.getenv('ANTHROPIC_BASE_URL'):
                selected_provider = prov
                selected_key_name = provider_keys[prov]
                break
            elif prov == 'gemini' and os.getenv('GEMINI_BASE_URL'):
                selected_provider = prov
                selected_key_name = provider_keys[prov]
                break
        
        # Default to openai-compatible if no custom base URL
        if not selected_provider:
            selected_provider = 'openai-compatible'
            selected_key_name = provider_keys[selected_provider]
            warning_message = f"Multiple API keys detected ({', '.join(detected_keys)}). Defaulting to openai-compatible."
    
    # No keys detected
    else:
        selected_provider = provider_flag or 'openai-compatible'
        selected_key_name = provider_keys.get(selected_provider)
        if not can_prompt:
            warning_message = f"No API keys found. Set {selected_key_name} or run with -i"
    
    return (selected_provider, detected_keys, selected_key_name, warning_message)


def get_or_create_install_id() -> Tuple[str, bool]:
    """Get or create install_id for telemetry.
    
    - Loads from config if exists
    - Generates new UUID if not
    - Saves to config automatically
    
    Returns:
        Tuple of (install_id, is_first_run)
    """
    try:
        saved_config = load_saved_config()
        
        # If install_id exists, return it
        if saved_config and saved_config.get('installId'):
            return (saved_config['installId'], False)
        
        # Generate new install_id
        install_id = generate_install_id()
        
        # Save to config
        save_config(install_id=install_id)
        
        return (install_id, True)
    except Exception:
        # If anything fails, generate a new ID without saving
        return (generate_install_id(), False)

