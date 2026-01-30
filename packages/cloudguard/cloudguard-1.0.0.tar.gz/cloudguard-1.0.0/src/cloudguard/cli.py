"""
CloudGuard CLI - Main Entry Point
"""

import click
import json
import sys
from datetime import datetime
from pathlib import Path

from cloudguard import __version__
from cloudguard.scanner import SecurityScanner
from cloudguard.reports import ReportGenerator
from cloudguard.utils.output import console, print_banner, print_summary


@click.group()
@click.version_option(version=__version__, prog_name="cloudguard")
def cli():
    """
    CloudGuard - AWS Security Compliance Scanner
    
    Automated security scanning aligned with CIS AWS Foundations Benchmark.
    Scans S3, IAM, EC2, VPC, and CloudTrail for misconfigurations.
    """
    pass


@cli.command()
@click.option('--profile', '-p', default=None, help='AWS profile name to use')
@click.option('--region', '-r', default=None, help='AWS region to scan (default: all regions)')
@click.option('--service', '-s', multiple=True, 
              type=click.Choice(['s3', 'iam', 'ec2', 'vpc', 'cloudtrail', 'all']),
              default=['all'], help='Services to scan (can specify multiple)')
@click.option('--severity', type=click.Choice(['critical', 'high', 'medium', 'low', 'all']),
              default='all', help='Minimum severity to report')
@click.option('--output', '-o', type=click.Choice(['terminal', 'json', 'html', 'all']),
              default='terminal', help='Output format')
@click.option('--output-file', type=click.Path(), default=None,
              help='Output file path (auto-generated if not specified)')
@click.option('--quiet', '-q', is_flag=True, help='Suppress banner and progress output')
@click.option('--fail-on', type=click.Choice(['critical', 'high', 'medium', 'low', 'none']),
              default='none', help='Exit with error code if findings at this severity or above')
def scan(profile, region, service, severity, output, output_file, quiet, fail_on):
    """
    Run security compliance scan on your AWS account.
    
    Examples:
    
        cloudguard scan
        
        cloudguard scan --profile production --service s3 --service iam
        
        cloudguard scan --output html --output-file report.html
        
        cloudguard scan --severity high --fail-on critical
    """
    if not quiet:
        print_banner()
    
    # Normalize services
    services = list(service)
    if 'all' in services:
        services = ['s3', 'iam', 'ec2', 'vpc', 'cloudtrail']
    
    # Initialize scanner
    try:
        scanner = SecurityScanner(
            profile=profile,
            region=region,
            quiet=quiet
        )
    except Exception as e:
        console.print(f"[red]Error initializing scanner: {e}[/red]")
        sys.exit(1)
    
    # Run scan
    if not quiet:
        console.print(f"\n[bold cyan]Starting security scan...[/bold cyan]")
        console.print(f"Services: {', '.join(services)}")
        if region:
            console.print(f"Region: {region}")
        console.print()
    
    try:
        findings = scanner.scan(services=services)
    except Exception as e:
        console.print(f"[red]Error during scan: {e}[/red]")
        sys.exit(1)
    
    # Filter by severity
    if severity != 'all':
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        min_severity = severity_order[severity]
        findings = [f for f in findings if severity_order.get(f['severity'].lower(), 4) <= min_severity]
    
    # Generate output
    report_gen = ReportGenerator(findings)
    
    if output == 'terminal' or output == 'all':
        report_gen.print_terminal_report()
    
    if output == 'json' or output == 'all':
        json_file = output_file or f"cloudguard-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        report_gen.save_json(json_file)
        console.print(f"\n[green]JSON report saved to: {json_file}[/green]")
    
    if output == 'html' or output == 'all':
        html_file = output_file or f"cloudguard-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.html"
        report_gen.save_html(html_file)
        console.print(f"\n[green]HTML report saved to: {html_file}[/green]")
    
    # Print summary
    if not quiet:
        print_summary(findings)
    
    # Exit with error code if requested
    if fail_on != 'none':
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        fail_threshold = severity_order[fail_on]
        for finding in findings:
            if severity_order.get(finding['severity'].lower(), 4) <= fail_threshold:
                sys.exit(1)


@cli.command()
@click.option('--profile', '-p', default=None, help='AWS profile name to use')
def list_services(profile):
    """
    List available AWS services and checks.
    """
    print_banner()
    
    checks_info = {
        's3': [
            'Public access block configuration',
            'Bucket encryption',
            'Bucket versioning',
            'Bucket logging',
            'Secure transport policy (HTTPS)',
            'Public bucket policies'
        ],
        'iam': [
            'Root account MFA',
            'Root account access keys',
            'Password policy strength',
            'Unused credentials (90+ days)',
            'Users with admin privileges',
            'Policies with wildcard permissions'
        ],
        'ec2': [
            'Security groups with risky open ports',
            'Unencrypted EBS volumes',
            'IMDSv2 enforcement',
            'Public AMIs',
            'Instances in public subnets',
            'Unused security groups'
        ],
        'vpc': [
            'VPC flow logs enabled',
            'Default security group restrictions',
            'Network ACL configurations',
            'Internet gateway exposure'
        ],
        'cloudtrail': [
            'CloudTrail enabled in all regions',
            'Log file validation',
            'S3 bucket logging',
            'CloudWatch integration',
            'KMS encryption'
        ]
    }
    
    console.print("\n[bold cyan]Available Security Checks[/bold cyan]\n")
    
    for service, checks in checks_info.items():
        console.print(f"[bold yellow]{service.upper()}[/bold yellow]")
        for check in checks:
            console.print(f"  • {check}")
        console.print()


@cli.command()
@click.argument('report_file', type=click.Path(exists=True))
@click.option('--format', '-f', type=click.Choice(['html', 'json']), default='html',
              help='Convert to format')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
def convert(report_file, format, output):
    """
    Convert a JSON report to HTML format.
    
    Example:
    
        cloudguard convert report.json --format html
    """
    print_banner()
    
    with open(report_file, 'r') as f:
        findings = json.load(f)
    
    report_gen = ReportGenerator(findings)
    
    if format == 'html':
        output_path = output or report_file.replace('.json', '.html')
        report_gen.save_html(output_path)
        console.print(f"[green]HTML report saved to: {output_path}[/green]")
    elif format == 'json':
        output_path = output or report_file.replace('.html', '.json')
        report_gen.save_json(output_path)
        console.print(f"[green]JSON report saved to: {output_path}[/green]")


@cli.command()
@click.option('--profile', '-p', default=None, help='AWS profile name to use')
def verify(profile):
    """
    Verify AWS credentials and permissions.
    """
    print_banner()
    
    console.print("\n[bold cyan]Verifying AWS Configuration...[/bold cyan]\n")
    
    try:
        import boto3
        
        session = boto3.Session(profile_name=profile) if profile else boto3.Session()
        sts = session.client('sts')
        
        identity = sts.get_caller_identity()
        
        console.print("[green]✓ AWS credentials valid[/green]")
        console.print(f"  Account: {identity['Account']}")
        console.print(f"  User/Role: {identity['Arn']}")
        
        # Test basic permissions
        console.print("\n[bold]Testing service access:[/bold]")
        
        services_to_test = [
            ('s3', 'list_buckets'),
            ('iam', 'get_account_summary'),
            ('ec2', 'describe_instances'),
            ('cloudtrail', 'describe_trails'),
        ]
        
        for service_name, operation in services_to_test:
            try:
                client = session.client(service_name)
                getattr(client, operation)()
                console.print(f"  [green]✓[/green] {service_name.upper()}")
            except Exception as e:
                console.print(f"  [red]✗[/red] {service_name.upper()}: {str(e)[:50]}")
        
        console.print("\n[green]AWS configuration verified successfully![/green]")
        
    except Exception as e:
        console.print(f"[red]✗ AWS credentials error: {e}[/red]")
        console.print("\nMake sure you have configured AWS credentials:")
        console.print("  • Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables")
        console.print("  • Or run 'aws configure' to set up a profile")
        console.print("  • Or use --profile flag to specify a named profile")
        sys.exit(1)


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == '__main__':
    main()
