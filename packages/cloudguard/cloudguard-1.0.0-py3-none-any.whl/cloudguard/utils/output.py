"""
CloudGuard - Output Utilities
Console output helpers and formatting
"""

from typing import List, Dict
from collections import Counter

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import box
    console = Console()
except ImportError:
    # Fallback if rich is not installed
    class FallbackConsole:
        def print(self, *args, **kwargs):
            # Strip rich formatting tags
            import re
            text = str(args[0]) if args else ""
            text = re.sub(r'\[/?[^\]]+\]', '', text)
            print(text)
    console = FallbackConsole()


BANNER = r"""
   _____ _                 _  _____                     _ 
  / ____| |               | |/ ____|                   | |
 | |    | | ___  _   _  __| | |  __ _   _  __ _ _ __ __| |
 | |    | |/ _ \| | | |/ _` | | |_ | | | |/ _` | '__/ _` |
 | |____| | (_) | |_| | (_| | |__| | |_| | (_| | | | (_| |
  \_____|_|\___/ \__,_|\__,_|\_____|\__,_|\__,_|_|  \__,_|
                                                          
        AWS Security Compliance Scanner v1.0.0
"""


def print_banner():
    """Print the CloudGuard banner."""
    try:
        console.print(Panel(
            BANNER,
            border_style="cyan",
            box=box.ROUNDED
        ))
    except:
        print(BANNER)


def print_summary(findings: List[Dict]):
    """Print a summary table of findings."""
    severity_counts = Counter(f['severity'].lower() for f in findings)
    
    total = len(findings)
    critical = severity_counts.get('critical', 0)
    high = severity_counts.get('high', 0)
    medium = severity_counts.get('medium', 0)
    low = severity_counts.get('low', 0)
    
    console.print("\n[bold]═══════════════════════════════════════════════════════════════[/bold]")
    console.print("[bold]                         SCAN SUMMARY                          [/bold]")
    console.print("[bold]═══════════════════════════════════════════════════════════════[/bold]\n")
    
    try:
        table = Table(show_header=True, header_style="bold cyan", box=box.ROUNDED)
        table.add_column("Severity", style="bold")
        table.add_column("Count", justify="right")
        table.add_column("", justify="left")
        
        if critical > 0:
            table.add_row("🔴 Critical", str(critical), "[red]" + "█" * min(critical, 20) + "[/red]")
        if high > 0:
            table.add_row("🟠 High", str(high), "[orange1]" + "█" * min(high, 20) + "[/orange1]")
        if medium > 0:
            table.add_row("🟡 Medium", str(medium), "[yellow]" + "█" * min(medium, 20) + "[/yellow]")
        if low > 0:
            table.add_row("🟢 Low", str(low), "[blue]" + "█" * min(low, 20) + "[/blue]")
        
        table.add_row("", "", "")
        table.add_row("[bold]Total[/bold]", f"[bold]{total}[/bold]", "")
        
        console.print(table)
    except:
        console.print(f"  🔴 Critical: {critical}")
        console.print(f"  🟠 High:     {high}")
        console.print(f"  🟡 Medium:   {medium}")
        console.print(f"  🟢 Low:      {low}")
        console.print(f"  ───────────────")
        console.print(f"  Total:      {total}")
    
    console.print()
    
    if total == 0:
        console.print("[green]✓ No security issues found! Your AWS environment looks secure.[/green]")
    elif critical > 0:
        console.print("[red]⚠ Critical issues require immediate attention![/red]")
    elif high > 0:
        console.print("[orange1]⚠ High severity issues should be addressed soon.[/orange1]")
