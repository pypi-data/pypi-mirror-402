"""Streaming checks - SSE, chunk gaps, timeouts."""

import time
import httpx
from typing import Dict, Any
from ai_patch.config import Config


def check(config: Config) -> Dict[str, Any]:
    """Run streaming checks."""
    
    findings = []
    metrics = {}
    not_detected = []
    not_observable = []
    
    try:
        # Test streaming endpoint
        url = f"{config.base_url.rstrip('/')}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": config.model or "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "Say hello"}],
            "stream": True,
            "max_tokens": 50
        }
        
        # Measure TTFB and streaming
        start_time = time.time()
        ttfb = None
        chunk_count = 0
        last_chunk_time = start_time
        max_chunk_gap = 0
        
        with httpx.stream("POST", url, headers=headers, json=payload, timeout=30.0) as response:
            response.raise_for_status()
            
            for chunk in response.iter_bytes():
                current_time = time.time()
                
                if ttfb is None:
                    ttfb = current_time - start_time
                
                chunk_gap = current_time - last_chunk_time
                max_chunk_gap = max(max_chunk_gap, chunk_gap)
                last_chunk_time = current_time
                chunk_count += 1
        
        total_time = time.time() - start_time
        
        # Record metrics
        metrics['ttfb_ms'] = round(ttfb * 1000, 2) if ttfb else None
        metrics['total_time_s'] = round(total_time, 2)
        metrics['chunk_count'] = chunk_count
        metrics['max_chunk_gap_s'] = round(max_chunk_gap, 2)
        
        # Check for issues
        if ttfb and ttfb > 5.0:
            findings.append({
                'severity': 'warning',
                'message': f'TTFB: {ttfb:.1f}s (threshold: 5s)'
            })
        
        if max_chunk_gap > 30.0:
            findings.append({
                'severity': 'error',
                'message': f'Max chunk gap: {max_chunk_gap:.1f}s (>30s threshold)'
            })
        elif max_chunk_gap > 10.0:
            findings.append({
                'severity': 'warning',
                'message': f'Max chunk gap: {max_chunk_gap:.1f}s (>10s threshold)'
            })
        
        # Determine status
        if not findings:
            status = 'pass'
        elif any(f['severity'] == 'error' for f in findings):
            status = 'fail'
        else:
            status = 'warn'
        
        # Add "Not observable" only if there are warnings/errors
        if status in ['warn', 'fail']:
            not_observable.append('Whether client retries after partial stream')
        
    except httpx.TimeoutException as e:
        status = 'fail'
        findings.append({
            'severity': 'error',
            'message': f'Streaming timeout: {str(e)}'
        })
    except httpx.HTTPStatusError as e:
        status = 'fail'
        findings.append({
            'severity': 'error',
            'message': f'HTTP error {e.response.status_code}'
        })
    except Exception as e:
        status = 'fail'
        findings.append({
            'severity': 'error',
            'message': f'Streaming check failed: {str(e)}'
        })
    
    return {
        'status': status,
        'findings': findings,
        'metrics': metrics,
        'not_detected': not_detected,
        'not_observable': not_observable
    }
