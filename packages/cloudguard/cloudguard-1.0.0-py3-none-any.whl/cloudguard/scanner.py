"""
CloudGuard Scanner - Main orchestrator for security checks
"""

import boto3
from datetime import datetime, timezone
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from cloudguard.checks.s3 import S3SecurityCheck
from cloudguard.checks.iam import IAMSecurityCheck
from cloudguard.checks.ec2 import EC2SecurityCheck
from cloudguard.checks.vpc import VPCSecurityCheck
from cloudguard.checks.cloudtrail import CloudTrailSecurityCheck
from cloudguard.utils.output import console


class SecurityScanner:
    """Main security scanner that orchestrates all checks."""
    
    def __init__(self, profile: Optional[str] = None, region: Optional[str] = None, quiet: bool = False):
        """
        Initialize the security scanner.
        
        Args:
            profile: AWS profile name to use
            region: AWS region to scan (None for all regions)
            quiet: Suppress progress output
        """
        self.session = boto3.Session(profile_name=profile) if profile else boto3.Session()
        self.region = region
        self.quiet = quiet
        self.scan_id = f"scan-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        
        # Map service names to check classes
        self.check_classes = {
            's3': S3SecurityCheck,
            'iam': IAMSecurityCheck,
            'ec2': EC2SecurityCheck,
            'vpc': VPCSecurityCheck,
            'cloudtrail': CloudTrailSecurityCheck,
        }
    
    def scan(self, services: List[str] = None) -> List[Dict]:
        """
        Run security scans on specified services.
        
        Args:
            services: List of service names to scan. If None, scans all services.
            
        Returns:
            List of finding dictionaries
        """
        if services is None:
            services = list(self.check_classes.keys())
        
        all_findings = []
        
        for service in services:
            if service not in self.check_classes:
                if not self.quiet:
                    console.print(f"[yellow]Warning: Unknown service '{service}', skipping[/yellow]")
                continue
            
            if not self.quiet:
                console.print(f"[cyan]Scanning {service.upper()}...[/cyan]")
            
            try:
                check_class = self.check_classes[service]
                checker = check_class(
                    session=self.session,
                    region=self.region,
                    scan_id=self.scan_id
                )
                findings = checker.run_checks()
                all_findings.extend(findings)
                
                if not self.quiet:
                    finding_count = len(findings)
                    if finding_count > 0:
                        console.print(f"  [yellow]Found {finding_count} issue(s)[/yellow]")
                    else:
                        console.print(f"  [green]No issues found[/green]")
                        
            except Exception as e:
                if not self.quiet:
                    console.print(f"  [red]Error scanning {service}: {e}[/red]")
        
        return all_findings
    
    def scan_parallel(self, services: List[str] = None, max_workers: int = 5) -> List[Dict]:
        """
        Run security scans in parallel for faster execution.
        
        Args:
            services: List of service names to scan
            max_workers: Maximum number of parallel workers
            
        Returns:
            List of finding dictionaries
        """
        if services is None:
            services = list(self.check_classes.keys())
        
        all_findings = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_service = {}
            
            for service in services:
                if service not in self.check_classes:
                    continue
                    
                check_class = self.check_classes[service]
                checker = check_class(
                    session=self.session,
                    region=self.region,
                    scan_id=self.scan_id
                )
                future = executor.submit(checker.run_checks)
                future_to_service[future] = service
            
            for future in as_completed(future_to_service):
                service = future_to_service[future]
                try:
                    findings = future.result()
                    all_findings.extend(findings)
                    
                    if not self.quiet:
                        console.print(f"[cyan]{service.upper()}:[/cyan] {len(findings)} finding(s)")
                        
                except Exception as e:
                    if not self.quiet:
                        console.print(f"[red]Error scanning {service}: {e}[/red]")
        
        return all_findings
