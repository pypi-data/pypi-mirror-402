"""
CloudGuard - Report Generator
Generates JSON and HTML reports from scan findings
"""

import json
from datetime import datetime
from typing import List, Dict
from collections import Counter

from cloudguard.utils.output import console


class ReportGenerator:
    """Generate reports from security scan findings."""
    
    def __init__(self, findings: List[Dict]):
        """
        Initialize the report generator.
        
        Args:
            findings: List of finding dictionaries from the scanner
        """
        self.findings = findings
        self.timestamp = datetime.now().isoformat()
    
    def get_summary(self) -> Dict:
        """Get a summary of findings by severity."""
        severity_counts = Counter(f['severity'].lower() for f in self.findings)
        service_counts = Counter(f['resource_type'].split('::')[1] for f in self.findings)
        
        return {
            'total': len(self.findings),
            'by_severity': {
                'critical': severity_counts.get('critical', 0),
                'high': severity_counts.get('high', 0),
                'medium': severity_counts.get('medium', 0),
                'low': severity_counts.get('low', 0)
            },
            'by_service': dict(service_counts)
        }
    
    def print_terminal_report(self):
        """Print findings to terminal with colors."""
        if not self.findings:
            console.print("\n[green]✓ No security issues found![/green]")
            return
        
        severity_colors = {
            'critical': 'red',
            'high': 'orange1',
            'medium': 'yellow',
            'low': 'blue'
        }
        
        severity_icons = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🟢'
        }
        
        # Group by severity
        by_severity = {'critical': [], 'high': [], 'medium': [], 'low': []}
        for finding in self.findings:
            sev = finding['severity'].lower()
            if sev in by_severity:
                by_severity[sev].append(finding)
        
        console.print("\n[bold]═══════════════════════════════════════════════════════════════[/bold]")
        console.print("[bold]                    SECURITY SCAN FINDINGS                      [/bold]")
        console.print("[bold]═══════════════════════════════════════════════════════════════[/bold]\n")
        
        for severity in ['critical', 'high', 'medium', 'low']:
            findings_list = by_severity[severity]
            if not findings_list:
                continue
            
            color = severity_colors[severity]
            icon = severity_icons[severity]
            
            console.print(f"[bold {color}]{icon} {severity.upper()} ({len(findings_list)})[/bold {color}]")
            console.print("─" * 60)
            
            for finding in findings_list:
                console.print(f"  [{color}]■[/{color}] {finding['title']}")
                console.print(f"    Resource: {finding['resource_id']}")
                if finding.get('region') and finding['region'] != 'global':
                    console.print(f"    Region: {finding['region']}")
                if finding.get('cis_control'):
                    console.print(f"    CIS Control: {finding['cis_control']}")
                console.print()
    
    def save_json(self, filepath: str):
        """Save findings as JSON."""
        report = {
            'report_generated': self.timestamp,
            'summary': self.get_summary(),
            'findings': self.findings
        }
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
    
    def save_html(self, filepath: str):
        """Save findings as an HTML report."""
        summary = self.get_summary()
        
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CloudGuard Security Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #e4e4e7;
            padding: 2rem;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            margin-bottom: 2rem;
            padding: 2rem;
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .header h1 {{
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            background: linear-gradient(90deg, #00d4ff, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .header .timestamp {{
            color: #a1a1aa;
            font-size: 0.9rem;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }}
        .summary-card {{
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
            transition: transform 0.2s;
        }}
        .summary-card:hover {{
            transform: translateY(-2px);
        }}
        .summary-card .count {{
            font-size: 2.5rem;
            font-weight: bold;
        }}
        .summary-card .label {{
            color: #a1a1aa;
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 1px;
        }}
        .critical .count {{ color: #ef4444; }}
        .high .count {{ color: #f97316; }}
        .medium .count {{ color: #eab308; }}
        .low .count {{ color: #3b82f6; }}
        .total .count {{ color: #00ff88; }}
        
        .section {{
            margin-bottom: 2rem;
        }}
        .section-title {{
            font-size: 1.25rem;
            margin-bottom: 1rem;
            padding-left: 1rem;
            border-left: 4px solid #00d4ff;
        }}
        .finding {{
            background: rgba(255,255,255,0.03);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            border-left: 4px solid;
            transition: background 0.2s;
        }}
        .finding:hover {{
            background: rgba(255,255,255,0.06);
        }}
        .finding.critical {{ border-color: #ef4444; }}
        .finding.high {{ border-color: #f97316; }}
        .finding.medium {{ border-color: #eab308; }}
        .finding.low {{ border-color: #3b82f6; }}
        
        .finding-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 0.75rem;
        }}
        .finding-title {{
            font-weight: 600;
            font-size: 1.1rem;
        }}
        .severity-badge {{
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }}
        .severity-badge.critical {{ background: rgba(239,68,68,0.2); color: #ef4444; }}
        .severity-badge.high {{ background: rgba(249,115,22,0.2); color: #f97316; }}
        .severity-badge.medium {{ background: rgba(234,179,8,0.2); color: #eab308; }}
        .severity-badge.low {{ background: rgba(59,130,246,0.2); color: #3b82f6; }}
        
        .finding-meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            margin-bottom: 0.75rem;
            font-size: 0.875rem;
            color: #a1a1aa;
        }}
        .finding-meta span {{
            display: flex;
            align-items: center;
            gap: 0.25rem;
        }}
        .finding-description {{
            color: #d4d4d8;
            margin-bottom: 0.75rem;
            line-height: 1.6;
        }}
        .finding-recommendation {{
            background: rgba(0,212,255,0.1);
            padding: 0.75rem 1rem;
            border-radius: 8px;
            font-size: 0.875rem;
            color: #00d4ff;
        }}
        .finding-recommendation strong {{
            color: #00ff88;
        }}
        
        .no-findings {{
            text-align: center;
            padding: 4rem;
            color: #00ff88;
            font-size: 1.5rem;
        }}
        .no-findings .checkmark {{
            font-size: 4rem;
            margin-bottom: 1rem;
        }}
        
        footer {{
            text-align: center;
            margin-top: 2rem;
            padding-top: 2rem;
            border-top: 1px solid rgba(255,255,255,0.1);
            color: #71717a;
            font-size: 0.875rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>🛡️ CloudGuard Security Report</h1>
            <p class="timestamp">Generated: {self.timestamp}</p>
        </header>
        
        <div class="summary">
            <div class="summary-card total">
                <div class="count">{summary['total']}</div>
                <div class="label">Total Findings</div>
            </div>
            <div class="summary-card critical">
                <div class="count">{summary['by_severity']['critical']}</div>
                <div class="label">Critical</div>
            </div>
            <div class="summary-card high">
                <div class="count">{summary['by_severity']['high']}</div>
                <div class="label">High</div>
            </div>
            <div class="summary-card medium">
                <div class="count">{summary['by_severity']['medium']}</div>
                <div class="label">Medium</div>
            </div>
            <div class="summary-card low">
                <div class="count">{summary['by_severity']['low']}</div>
                <div class="label">Low</div>
            </div>
        </div>
'''
        
        if not self.findings:
            html += '''
        <div class="no-findings">
            <div class="checkmark">✓</div>
            <div>No security issues found!</div>
        </div>
'''
        else:
            # Group findings by severity
            by_severity = {'critical': [], 'high': [], 'medium': [], 'low': []}
            for finding in self.findings:
                sev = finding['severity'].lower()
                if sev in by_severity:
                    by_severity[sev].append(finding)
            
            for severity in ['critical', 'high', 'medium', 'low']:
                findings_list = by_severity[severity]
                if not findings_list:
                    continue
                
                html += f'''
        <div class="section">
            <h2 class="section-title">{severity.upper()} ({len(findings_list)})</h2>
'''
                for finding in findings_list:
                    region_display = f" • {finding.get('region', 'global')}" if finding.get('region') else ""
                    cis_display = f" • {finding.get('cis_control', '')}" if finding.get('cis_control') else ""
                    
                    html += f'''
            <div class="finding {severity}">
                <div class="finding-header">
                    <span class="finding-title">{finding['title']}</span>
                    <span class="severity-badge {severity}">{severity}</span>
                </div>
                <div class="finding-meta">
                    <span>📦 {finding['resource_id']}</span>
                    <span>📍 {finding['resource_type']}{region_display}{cis_display}</span>
                </div>
                <p class="finding-description">{finding['description']}</p>
                <div class="finding-recommendation">
                    <strong>Recommendation:</strong> {finding.get('recommendation', 'N/A')}
                </div>
            </div>
'''
                html += '        </div>\n'
        
        html += '''
        <footer>
            <p>Generated by CloudGuard AWS Security Scanner</p>
        </footer>
    </div>
</body>
</html>
'''
        
        with open(filepath, 'w') as f:
            f.write(html)
