"""Report generation for AI Patch."""

import json
from datetime import datetime, timezone
from typing import Dict, Any


class ReportGenerator:
    """Generate reports in JSON and Markdown formats."""
    
    VERSION = "1.0.0"
    
    def create_report(
        self,
        target: str,
        provider: str,
        base_url: str,
        checks: Dict[str, Any],
        duration: float
    ) -> Dict[str, Any]:
        """Create a report dictionary."""
        
        # Determine overall status
        status = 'success'
        for check_name, check_result in checks.items():
            check_status = check_result.get('status', 'unknown')
            if check_status == 'fail':
                status = 'error'
                break
            elif check_status == 'warn' and status == 'success':
                status = 'warning'
        
        # Calculate estimated cost if available
        estimated_cost = None
        for check_name, check_result in checks.items():
            metrics = check_result.get('metrics', {})
            if 'estimated_cost_usd' in metrics:
                if estimated_cost is None:
                    estimated_cost = 0
                estimated_cost += metrics.get('estimated_cost_usd', 0)
        
        # Build report
        report = {
            'version': self.VERSION,
            'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            'target': target,
            'provider': provider,
            'base_url': base_url,
            'checks': checks,
            'summary': {
                'status': status,
                'duration_seconds': round(duration, 2)
            },
            # BYOK receipt schema metadata
            'receipt_format': 'badgr-compatible',
            'execution_authority': 'ai-patch',
            'billing_authority': 'customer',
            # Coverage limitations
            'coverage': {
                'mode': 'synthetic',
                'missing': [
                    'live retry storms',
                    'cross-request correlation',
                    'partial stream truncation',
                    'tail latency amplification'
                ]
            }
        }
        
        # Add cost fields only if cost exists
        if estimated_cost is not None:
            report['estimated_cost_usd'] = round(estimated_cost, 6)
            report['cost_source'] = 'model_pricing_table'
        
        return report
    
    def generate_markdown(self, report: Dict[str, Any]) -> str:
        """Generate Markdown report from report data."""
        
        lines = []
        lines.append("# AI Patch Report")
        lines.append("")
        lines.append(f"**Generated:** {report['timestamp']}")
        lines.append(f"**Target:** {report['target']}")
        lines.append(f"**Provider:** {report['provider']}")
        lines.append(f"**Base URL:** {report['base_url']}")
        lines.append("")
        
        # Summary
        summary = report['summary']
        status_emoji = {
            'success': '✅',
            'warning': '⚠️',
            'error': '❌'
        }
        
        lines.append("## Summary")
        lines.append("")
        lines.append(f"**Status:** {status_emoji.get(summary['status'], '•')} {summary['status'].upper()}")
        lines.append(f"**Duration:** {summary['duration_seconds']}s")
        lines.append("")
        
        # Organize findings into three buckets
        detected = []
        not_detected = []
        not_observable = []
        
        for check_name, check_result in report['checks'].items():
            findings = check_result.get('findings', [])
            check_not_detected = check_result.get('not_detected', [])
            check_not_observable = check_result.get('not_observable', [])
            
            for finding in findings:
                message = finding.get('message', '')
                
                # Detected: findings with evidence
                if finding.get('severity') in ['info', 'warning', 'error']:
                    detected.append(f"[{check_name}] {message}")
            
            # Aggregate not detected and not observable items
            not_detected.extend(check_not_detected)
            for item in check_not_observable:
                if item not in not_observable:
                    not_observable.append(item)
        
        # Three-bucket structure
        lines.append("## Detected")
        lines.append("")
        if detected:
            for item in detected:
                lines.append(f"• {item}")
        else:
            lines.append("No issues detected")
        lines.append("")
        
        lines.append("## Not detected")
        lines.append("")
        if not_detected:
            for item in not_detected:
                lines.append(f"• {item}")
        else:
            lines.append("No explicit checks for absent items")
        lines.append("")
        
        # Only show "Not observable" if status is warning or error
        if summary['status'] != 'success' and not_observable:
            lines.append("## Not observable from provider probe")
            lines.append("")
            for item in not_observable:
                lines.append(f"• {item}")
            lines.append("")
        
        # Conditional note
        if summary['status'] != 'success':
            lines.append("### Note")
            lines.append("Here's exactly what I can see from the provider probe.")
            lines.append("Here's what I cannot see without real traffic.")
            lines.append("")
        
        # Footer with conditional Badgr
        lines.append("---")
        lines.append("")
        lines.append("📊 Report: ./ai-patch-reports/latest/report.md")
        lines.append("")
        
        # Badgr messaging - only when status != success and relevant items exist
        if summary['status'] != 'success' and not_observable:
            specific_item = not_observable[0].lower()
            lines.append(f"To observe {specific_item}, run one real request through the receipt gateway (2-minute base_url swap).")
            lines.append("")
        
        lines.append("Generated by AI Patch — re-run: npx ai-patch")
        
        return '\n'.join(lines)
