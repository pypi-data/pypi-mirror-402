# CloudGuard - AWS Security Compliance Scanner

<p align="center">
  <img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/AWS-Security-orange.svg" alt="AWS Security">
</p>

**CloudGuard** is a command-line security compliance scanner for AWS environments. It performs automated security checks aligned with the CIS AWS Foundations Benchmark to help identify misconfigurations and security risks.

## Features

- 🔍 **26+ Security Checks** across 5 AWS services
- 🎯 **CIS Benchmark Aligned** - Maps to CIS AWS Foundations Benchmark controls
- 📊 **Multiple Output Formats** - Terminal, JSON, and HTML reports
- 🚀 **Easy to Use** - Simple CLI with sensible defaults
- 🔧 **Configurable** - Filter by service, severity, or region
- 💰 **Cost-Effective** - Runs locally with minimal AWS API calls

## Supported Services & Checks

### S3 (6 checks)
- Public access block configuration
- Default encryption
- Versioning enabled
- Access logging
- HTTPS enforcement
- Public bucket policies

### IAM (8 checks)
- Root account MFA
- Root access keys
- Password policy strength
- Unused credentials (90+ days)
- Admin privilege usage
- User MFA enforcement
- Wildcard policies

### EC2 (7 checks)
- Security groups with risky open ports (SSH, RDP, databases)
- Unencrypted EBS volumes
- IMDSv2 enforcement
- Public AMIs
- Default security group rules

### VPC (5 checks)
- Flow logs enabled
- Network ACL configurations
- Internet gateway exposure
- Peering connections

### CloudTrail (10 checks)
- Multi-region logging
- Log file validation
- S3 bucket security
- KMS encryption
- CloudWatch integration

## Installation

### From PyPI (recommended)

```bash
pip install cloudguard
```

### From Source

```bash
git clone https://github.com/yourusername/cloudguard.git
cd cloudguard
pip install -e .
```

## Quick Start

### Basic Scan

```bash
# Scan all services with default settings
cloudguard scan
```

### Using a Specific AWS Profile

```bash
cloudguard scan --profile production
```

### Scan Specific Services

```bash
cloudguard scan --service s3 --service iam
```

### Generate HTML Report

```bash
cloudguard scan --output html --output-file security-report.html
```

### Filter by Severity

```bash
cloudguard scan --severity high
```

## CLI Reference

### `cloudguard scan`

Run security compliance scan on your AWS account.

```
Options:
  -p, --profile TEXT        AWS profile name to use
  -r, --region TEXT         AWS region to scan (default: all regions)
  -s, --service TEXT        Services to scan: s3, iam, ec2, vpc, cloudtrail, all
      --severity TEXT       Minimum severity: critical, high, medium, low, all
  -o, --output TEXT         Output format: terminal, json, html, all
      --output-file PATH    Output file path
  -q, --quiet              Suppress banner and progress output
      --fail-on TEXT       Exit with error if findings at severity level
```

### `cloudguard verify`

Verify AWS credentials and permissions.

```bash
cloudguard verify --profile my-profile
```

### `cloudguard list-services`

List available services and security checks.

```bash
cloudguard list-services
```

### `cloudguard convert`

Convert a JSON report to HTML format.

```bash
cloudguard convert report.json --format html
```

## Examples

### CI/CD Integration

```bash
# Fail pipeline if critical findings exist
cloudguard scan --quiet --fail-on critical

# Generate JSON for processing
cloudguard scan --output json --output-file results.json --quiet
```

### Daily Security Report

```bash
# Generate comprehensive HTML report
cloudguard scan \
  --profile production \
  --output html \
  --output-file "security-report-$(date +%Y%m%d).html"
```

### Quick Check Specific Services

```bash
# Check only S3 and IAM for critical issues
cloudguard scan -s s3 -s iam --severity critical
```

## AWS Permissions Required

CloudGuard requires read-only access to scan AWS resources. Here's a minimal IAM policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetBucketAcl",
        "s3:GetBucketPolicy",
        "s3:GetBucketLogging",
        "s3:GetBucketVersioning",
        "s3:GetBucketEncryption",
        "s3:GetPublicAccessBlock",
        "s3:ListAllMyBuckets",
        "iam:GetAccountPasswordPolicy",
        "iam:GetAccountSummary",
        "iam:ListUsers",
        "iam:ListAccessKeys",
        "iam:GetAccessKeyLastUsed",
        "iam:ListAttachedUserPolicies",
        "iam:ListGroupsForUser",
        "iam:ListAttachedGroupPolicies",
        "iam:ListMFADevices",
        "iam:GetLoginProfile",
        "iam:ListPolicies",
        "iam:GetPolicyVersion",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeVolumes",
        "ec2:DescribeInstances",
        "ec2:DescribeImages",
        "ec2:DescribeVpcs",
        "ec2:DescribeFlowLogs",
        "ec2:DescribeNetworkAcls",
        "ec2:DescribeInternetGateways",
        "ec2:DescribeVpcPeeringConnections",
        "ec2:DescribeRegions",
        "cloudtrail:DescribeTrails",
        "cloudtrail:GetTrailStatus",
        "cloudtrail:GetEventSelectors",
        "sts:GetCallerIdentity"
      ],
      "Resource": "*"
    }
  ]
}
```

## Output Examples

### Terminal Output

```
═══════════════════════════════════════════════════════════════
                    SECURITY SCAN FINDINGS                      
═══════════════════════════════════════════════════════════════

🔴 CRITICAL (3)
────────────────────────────────────────────────────────────────
  ■ Root account MFA not enabled
    Resource: root
    CIS Control: CIS 1.5

  ■ S3 bucket public access block not configured
    Resource: my-public-bucket
    CIS Control: CIS 2.1.5

🟠 HIGH (5)
────────────────────────────────────────────────────────────────
  ■ Security group allows SSH from internet
    Resource: sg-0123456789abcdef
    Region: us-east-1
    CIS Control: CIS 5.2
```

### HTML Report

Generates a professional, dark-themed HTML report with:
- Summary statistics
- Findings grouped by severity
- Resource details and recommendations
- CIS control mappings

## Development

### Setup Development Environment

```bash
git clone https://github.com/yourusername/cloudguard.git
cd cloudguard
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
```

### Code Formatting

```bash
black src/
isort src/
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- CIS (Center for Internet Security) for the AWS Foundations Benchmark
- AWS for boto3 and comprehensive API documentation
- The Python community for excellent CLI tools

---

**Made with ❤️ for the cloud security community**
