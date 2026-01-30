"""
CloudGuard - S3 Security Checks
Scans S3 buckets for security compliance issues
"""

from typing import List, Dict
from botocore.exceptions import ClientError

from cloudguard.checks.base import BaseSecurityCheck


class S3SecurityCheck(BaseSecurityCheck):
    """Security checks for Amazon S3."""
    
    def run_checks(self) -> List[Dict]:
        """Run all S3 security checks."""
        self.findings = []
        
        s3_client = self.get_client('s3')
        
        try:
            buckets = s3_client.list_buckets()['Buckets']
        except ClientError as e:
            return [self.create_finding(
                check_id="S3-ERROR",
                title="Unable to list S3 buckets",
                description=f"Error accessing S3: {str(e)}",
                severity="high",
                resource_type="AWS::S3::Bucket",
                resource_id="N/A",
                recommendation="Check IAM permissions for S3 access"
            )]
        
        for bucket in buckets:
            bucket_name = bucket['Name']
            
            # Check public access block
            self._check_public_access_block(s3_client, bucket_name)
            
            # Check bucket encryption
            self._check_bucket_encryption(s3_client, bucket_name)
            
            # Check bucket versioning
            self._check_bucket_versioning(s3_client, bucket_name)
            
            # Check bucket logging
            self._check_bucket_logging(s3_client, bucket_name)
            
            # Check bucket policy for public access
            self._check_bucket_policy(s3_client, bucket_name)
            
            # Check secure transport
            self._check_secure_transport(s3_client, bucket_name)
        
        return self.findings
    
    def _check_public_access_block(self, client, bucket_name: str):
        """Check if public access block is configured."""
        try:
            response = client.get_public_access_block(Bucket=bucket_name)
            config = response['PublicAccessBlockConfiguration']
            
            missing_blocks = []
            if not config.get('BlockPublicAcls', False):
                missing_blocks.append('BlockPublicAcls')
            if not config.get('IgnorePublicAcls', False):
                missing_blocks.append('IgnorePublicAcls')
            if not config.get('BlockPublicPolicy', False):
                missing_blocks.append('BlockPublicPolicy')
            if not config.get('RestrictPublicBuckets', False):
                missing_blocks.append('RestrictPublicBuckets')
            
            if missing_blocks:
                self.findings.append(self.create_finding(
                    check_id="S3-001",
                    title="S3 bucket public access block not fully configured",
                    description=f"Bucket '{bucket_name}' has incomplete public access block settings",
                    severity="high",
                    resource_type="AWS::S3::Bucket",
                    resource_id=bucket_name,
                    recommendation="Enable all public access block settings for the bucket",
                    cis_control="CIS 2.1.5",
                    details={"missing_blocks": missing_blocks}
                ))
                
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchPublicAccessBlockConfiguration':
                self.findings.append(self.create_finding(
                    check_id="S3-001",
                    title="S3 bucket public access block not configured",
                    description=f"Bucket '{bucket_name}' has no public access block configuration",
                    severity="critical",
                    resource_type="AWS::S3::Bucket",
                    resource_id=bucket_name,
                    recommendation="Enable public access block for the bucket",
                    cis_control="CIS 2.1.5"
                ))
    
    def _check_bucket_encryption(self, client, bucket_name: str):
        """Check if bucket has default encryption enabled."""
        try:
            client.get_bucket_encryption(Bucket=bucket_name)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ServerSideEncryptionConfigurationNotFoundError':
                self.findings.append(self.create_finding(
                    check_id="S3-002",
                    title="S3 bucket encryption not enabled",
                    description=f"Bucket '{bucket_name}' does not have default encryption enabled",
                    severity="high",
                    resource_type="AWS::S3::Bucket",
                    resource_id=bucket_name,
                    recommendation="Enable default encryption with SSE-S3 or SSE-KMS",
                    cis_control="CIS 2.1.1"
                ))
    
    def _check_bucket_versioning(self, client, bucket_name: str):
        """Check if bucket versioning is enabled."""
        try:
            response = client.get_bucket_versioning(Bucket=bucket_name)
            status = response.get('Status', 'Disabled')
            
            if status != 'Enabled':
                self.findings.append(self.create_finding(
                    check_id="S3-003",
                    title="S3 bucket versioning not enabled",
                    description=f"Bucket '{bucket_name}' does not have versioning enabled",
                    severity="medium",
                    resource_type="AWS::S3::Bucket",
                    resource_id=bucket_name,
                    recommendation="Enable versioning to protect against accidental deletions",
                    cis_control="CIS 2.1.3"
                ))
        except ClientError:
            pass
    
    def _check_bucket_logging(self, client, bucket_name: str):
        """Check if bucket logging is enabled."""
        try:
            response = client.get_bucket_logging(Bucket=bucket_name)
            
            if 'LoggingEnabled' not in response:
                self.findings.append(self.create_finding(
                    check_id="S3-004",
                    title="S3 bucket logging not enabled",
                    description=f"Bucket '{bucket_name}' does not have access logging enabled",
                    severity="medium",
                    resource_type="AWS::S3::Bucket",
                    resource_id=bucket_name,
                    recommendation="Enable server access logging for audit trail",
                    cis_control="CIS 2.1.2"
                ))
        except ClientError:
            pass
    
    def _check_bucket_policy(self, client, bucket_name: str):
        """Check bucket policy for public access."""
        try:
            policy = client.get_bucket_policy(Bucket=bucket_name)
            policy_text = policy.get('Policy', '')
            
            # Simple check for wildcard principal
            if '"Principal":"*"' in policy_text or '"Principal": "*"' in policy_text:
                # Check if there's a condition limiting access
                if '"Condition"' not in policy_text:
                    self.findings.append(self.create_finding(
                        check_id="S3-005",
                        title="S3 bucket policy allows public access",
                        description=f"Bucket '{bucket_name}' has a policy allowing public access",
                        severity="critical",
                        resource_type="AWS::S3::Bucket",
                        resource_id=bucket_name,
                        recommendation="Review and restrict the bucket policy",
                        cis_control="CIS 2.1.5"
                    ))
        except ClientError as e:
            if e.response['Error']['Code'] != 'NoSuchBucketPolicy':
                pass
    
    def _check_secure_transport(self, client, bucket_name: str):
        """Check if bucket enforces HTTPS-only access."""
        try:
            policy = client.get_bucket_policy(Bucket=bucket_name)
            policy_text = policy.get('Policy', '')
            
            # Check for secure transport condition
            has_secure_transport = (
                '"aws:SecureTransport"' in policy_text and
                '"false"' in policy_text.lower() and
                '"Effect":"Deny"' in policy_text.replace(' ', '')
            )
            
            if not has_secure_transport:
                self.findings.append(self.create_finding(
                    check_id="S3-006",
                    title="S3 bucket does not enforce HTTPS",
                    description=f"Bucket '{bucket_name}' does not have a policy denying non-HTTPS requests",
                    severity="medium",
                    resource_type="AWS::S3::Bucket",
                    resource_id=bucket_name,
                    recommendation="Add a bucket policy denying requests where aws:SecureTransport is false",
                    cis_control="CIS 2.1.1"
                ))
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchBucketPolicy':
                self.findings.append(self.create_finding(
                    check_id="S3-006",
                    title="S3 bucket does not enforce HTTPS",
                    description=f"Bucket '{bucket_name}' has no policy to enforce HTTPS-only access",
                    severity="medium",
                    resource_type="AWS::S3::Bucket",
                    resource_id=bucket_name,
                    recommendation="Add a bucket policy denying requests where aws:SecureTransport is false",
                    cis_control="CIS 2.1.1"
                ))
