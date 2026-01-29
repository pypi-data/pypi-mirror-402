"""Traceability checks - request IDs, correlation."""

import httpx
import hashlib
import uuid
from typing import Dict, Any
from ai_patch.config import Config


def check(config: Config) -> Dict[str, Any]:
    """Run traceability checks."""
    
    findings = []
    metrics = {}
    not_detected = []
    not_observable = []
    
    try:
        url = f"{config.base_url.rstrip('/')}/v1/chat/completions"
        
        # Generate stable request ID
        request_id = str(uuid.uuid4())
        
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
            "X-Request-ID": request_id
        }
        
        payload = {
            "model": config.model or "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "Test"}],
            "max_tokens": 10
        }
        
        # Make test request
        response = httpx.post(url, headers=headers, json=payload, timeout=30.0)
        response.raise_for_status()
        
        # Check for request ID in response
        provider_request_id = (
            response.headers.get('x-request-id') or
            response.headers.get('openai-request-id') or
            response.headers.get('cf-ray')  # Cloudflare
        )
        
        if provider_request_id:
            findings.append({
                'severity': 'info',
                'message': f'Provider request ID: {provider_request_id}'
            })
            metrics['provider_request_id'] = provider_request_id
        else:
            findings.append({
                'severity': 'warning',
                'message': 'Provider request ID not found in response headers'
            })
            not_detected.append('Provider request ID (not found in response headers)')
        
        # Calculate request hash for duplicate detection
        payload_str = str(sorted(payload.items()))
        request_hash = hashlib.sha256(payload_str.encode()).hexdigest()[:16]
        
        metrics['request_hash'] = request_hash
        
        findings.append({
            'severity': 'info',
            'message': f'Generated request hash: {request_hash}'
        })
        
        # Add "Not observable" only if there are warnings
        if not provider_request_id:
            not_observable.append('Duplicate requests')
        
        status = 'pass' if provider_request_id else 'warn'
        
    except Exception as e:
        status = 'fail'
        findings.append({
            'severity': 'error',
            'message': f'Trace check failed: {str(e)}'
        })
    
    return {
        'status': status,
        'findings': findings,
        'metrics': metrics,
        'not_detected': not_detected,
        'not_observable': not_observable
    }
