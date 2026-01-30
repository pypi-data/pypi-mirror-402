"""Retry checks - 429s, Retry-After, backoff."""

import httpx
from typing import Dict, Any
from ai_patch.config import Config


def check(config: Config) -> Dict[str, Any]:
    """Run retry checks."""
    
    findings = []
    metrics = {}
    not_detected = []
    not_observable = []
    
    try:
        # Test for 429 handling
        url = f"{config.base_url.rstrip('/')}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": config.model or "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "Test"}],
            "max_tokens": 10
        }
        
        # Make a test request
        response = httpx.post(url, headers=headers, json=payload, timeout=30.0)
        
        if response.is_error and response.status_code != 429:
            response.raise_for_status()
        
        # Check for rate limit headers
        if 'retry-after' in response.headers:
            retry_after = response.headers['retry-after']
            findings.append({
                'severity': 'info',
                'message': f'Retry-After header: {retry_after}s'
            })
            metrics['retry_after_s'] = retry_after
        
        if 'x-ratelimit-remaining' in response.headers:
            remaining = response.headers['x-ratelimit-remaining']
            metrics['ratelimit_remaining'] = remaining
            
            if int(remaining) < 10:
                findings.append({
                    'severity': 'warning',
                    'message': f'Rate limit remaining: {remaining} requests'
                })
        
        # Check for 429 status
        if response.status_code == 429:
            findings.append({
                'severity': 'warning',
                'message': 'Rate limiting detected (HTTP 429)'
            })
        
        # If no rate limiting detected, add to not_detected
        if response.status_code != 429 and 'retry-after' not in response.headers:
            not_detected.append('Rate limiting (no 429s in 1 probe)')
        
        # Add "Not observable" only if there are warnings/errors
        has_warnings = any(f['severity'] in ['warning', 'error'] for f in findings)
        if has_warnings:
            not_observable.append('Retry policy')
            not_observable.append('Retry after stream start')
        
        status = 'warn' if any(f['severity'] in ['warning', 'error'] for f in findings) else 'pass'
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            status = 'warn'
            retry_after = e.response.headers.get('retry-after', 'not set')
            findings.append({
                'severity': 'warning',
                'message': f'Rate limited (429). Retry-After: {retry_after}'
            })
            not_observable = ['Retry policy', 'Retry after stream start']
        else:
            status = 'fail'
            findings.append({
                'severity': 'error',
                'message': f'HTTP error {e.response.status_code}'
            })
    except Exception as e:
        status = 'fail'
        findings.append({
            'severity': 'error',
            'message': f'Retry check failed: {str(e)}'
        })
    
    return {
        'status': status,
        'findings': findings,
        'metrics': metrics,
        'not_detected': not_detected,
        'not_observable': not_observable
    }
