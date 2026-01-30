"""
CloudGuard - CloudTrail Security Checks
Scans CloudTrail configuration for security compliance issues
"""

from typing import List, Dict
from botocore.exceptions import ClientError

from cloudguard.checks.base import BaseSecurityCheck


class CloudTrailSecurityCheck(BaseSecurityCheck):
    """Security checks for AWS CloudTrail."""
    
    def run_checks(self) -> List[Dict]:
        """Run all CloudTrail security checks."""
        self.findings = []
        
        # CloudTrail is regional but multi-region trails show in all regions
        # So we check from us-east-1 for simplicity
        cloudtrail_client = self.get_client('cloudtrail', 'us-east-1')
        
        # Check if CloudTrail is enabled
        self._check_cloudtrail_enabled(cloudtrail_client)
        
        return self.findings
    
    def _check_cloudtrail_enabled(self, client):
        """Check CloudTrail configuration."""
        try:
            trails = client.describe_trails()['trailList']
            
            if not trails:
                self.findings.append(self.create_finding(
                    check_id="CT-001",
                    title="CloudTrail not enabled",
                    description="No CloudTrail trails are configured in this account",
                    severity="critical",
                    resource_type="AWS::CloudTrail::Trail",
                    resource_id="N/A",
                    recommendation="Enable CloudTrail with multi-region logging",
                    cis_control="CIS 3.1"
                ))
                return
            
            has_multiregion = False
            has_mgmt_events = False
            
            for trail in trails:
                trail_name = trail['Name']
                trail_arn = trail.get('TrailARN', trail_name)
                home_region = trail.get('HomeRegion', 'unknown')
                
                # Check multi-region
                if trail.get('IsMultiRegionTrail', False):
                    has_multiregion = True
                
                # Get trail status
                try:
                    status = client.get_trail_status(Name=trail_arn)
                    is_logging = status.get('IsLogging', False)
                    
                    if not is_logging:
                        self.findings.append(self.create_finding(
                            check_id="CT-002",
                            title="CloudTrail logging is disabled",
                            description=f"Trail '{trail_name}' exists but logging is disabled",
                            severity="critical",
                            resource_type="AWS::CloudTrail::Trail",
                            resource_id=trail_arn,
                            region=home_region,
                            recommendation="Enable logging for the CloudTrail trail",
                            cis_control="CIS 3.1"
                        ))
                except ClientError:
                    pass
                
                # Check log file validation
                if not trail.get('LogFileValidationEnabled', False):
                    self.findings.append(self.create_finding(
                        check_id="CT-003",
                        title="CloudTrail log file validation disabled",
                        description=f"Trail '{trail_name}' does not have log file validation enabled",
                        severity="medium",
                        resource_type="AWS::CloudTrail::Trail",
                        resource_id=trail_arn,
                        region=home_region,
                        recommendation="Enable log file validation to detect tampering",
                        cis_control="CIS 3.2"
                    ))
                
                # Check S3 bucket for CloudTrail logs
                s3_bucket = trail.get('S3BucketName')
                if s3_bucket:
                    self._check_cloudtrail_bucket(s3_bucket, trail_name, trail_arn, home_region)
                
                # Check KMS encryption
                if not trail.get('KMSKeyId'):
                    self.findings.append(self.create_finding(
                        check_id="CT-005",
                        title="CloudTrail not encrypted with KMS",
                        description=f"Trail '{trail_name}' is not using KMS encryption",
                        severity="medium",
                        resource_type="AWS::CloudTrail::Trail",
                        resource_id=trail_arn,
                        region=home_region,
                        recommendation="Enable KMS encryption for CloudTrail logs",
                        cis_control="CIS 3.7"
                    ))
                
                # Check CloudWatch integration
                if not trail.get('CloudWatchLogsLogGroupArn'):
                    self.findings.append(self.create_finding(
                        check_id="CT-006",
                        title="CloudTrail not integrated with CloudWatch",
                        description=f"Trail '{trail_name}' is not sending logs to CloudWatch",
                        severity="medium",
                        resource_type="AWS::CloudTrail::Trail",
                        resource_id=trail_arn,
                        region=home_region,
                        recommendation="Configure CloudWatch Logs integration for real-time monitoring",
                        cis_control="CIS 3.4"
                    ))
                
                # Check event selectors for management events
                try:
                    selectors = client.get_event_selectors(TrailName=trail_arn)
                    
                    # Check basic event selectors
                    for selector in selectors.get('EventSelectors', []):
                        if selector.get('IncludeManagementEvents', False):
                            has_mgmt_events = True
                            
                            # Check read/write type
                            read_write = selector.get('ReadWriteType', 'All')
                            if read_write != 'All':
                                self.findings.append(self.create_finding(
                                    check_id="CT-007",
                                    title="CloudTrail not logging all management events",
                                    description=f"Trail '{trail_name}' only logs {read_write} management events",
                                    severity="medium",
                                    resource_type="AWS::CloudTrail::Trail",
                                    resource_id=trail_arn,
                                    region=home_region,
                                    recommendation="Configure trail to log All management events",
                                    cis_control="CIS 3.1"
                                ))
                    
                    # Check advanced event selectors
                    for selector in selectors.get('AdvancedEventSelectors', []):
                        # Advanced selectors are more complex - simplified check
                        has_mgmt_events = True
                        
                except ClientError:
                    pass
            
            # Check for multi-region trail
            if not has_multiregion:
                self.findings.append(self.create_finding(
                    check_id="CT-008",
                    title="No multi-region CloudTrail",
                    description="No CloudTrail trail is configured for multi-region logging",
                    severity="high",
                    resource_type="AWS::CloudTrail::Trail",
                    resource_id="N/A",
                    recommendation="Configure at least one trail with multi-region logging enabled",
                    cis_control="CIS 3.1"
                ))
            
            # Check for management events
            if not has_mgmt_events:
                self.findings.append(self.create_finding(
                    check_id="CT-009",
                    title="CloudTrail not logging management events",
                    description="No CloudTrail trail is configured to log management events",
                    severity="high",
                    resource_type="AWS::CloudTrail::Trail",
                    resource_id="N/A",
                    recommendation="Enable management event logging in CloudTrail",
                    cis_control="CIS 3.1"
                ))
                    
        except ClientError as e:
            self.findings.append(self.create_finding(
                check_id="CT-ERROR",
                title="Unable to check CloudTrail",
                description=f"Error accessing CloudTrail: {str(e)}",
                severity="high",
                resource_type="AWS::CloudTrail::Trail",
                resource_id="N/A",
                recommendation="Check IAM permissions for CloudTrail access"
            ))
    
    def _check_cloudtrail_bucket(self, bucket_name: str, trail_name: str, trail_arn: str, region: str):
        """Check the S3 bucket used by CloudTrail."""
        try:
            s3_client = self.get_client('s3')
            
            # Check bucket logging
            try:
                logging = s3_client.get_bucket_logging(Bucket=bucket_name)
                if 'LoggingEnabled' not in logging:
                    self.findings.append(self.create_finding(
                        check_id="CT-004",
                        title="CloudTrail S3 bucket logging disabled",
                        description=f"S3 bucket '{bucket_name}' for trail '{trail_name}' does not have access logging",
                        severity="medium",
                        resource_type="AWS::S3::Bucket",
                        resource_id=bucket_name,
                        region=region,
                        recommendation="Enable access logging on the CloudTrail S3 bucket",
                        cis_control="CIS 3.6"
                    ))
            except ClientError:
                pass
            
            # Check bucket public access
            try:
                public_access = s3_client.get_public_access_block(Bucket=bucket_name)
                config = public_access['PublicAccessBlockConfiguration']
                
                if not all([
                    config.get('BlockPublicAcls', False),
                    config.get('IgnorePublicAcls', False),
                    config.get('BlockPublicPolicy', False),
                    config.get('RestrictPublicBuckets', False)
                ]):
                    self.findings.append(self.create_finding(
                        check_id="CT-010",
                        title="CloudTrail bucket public access not fully blocked",
                        description=f"S3 bucket '{bucket_name}' for CloudTrail does not have all public access blocks enabled",
                        severity="high",
                        resource_type="AWS::S3::Bucket",
                        resource_id=bucket_name,
                        region=region,
                        recommendation="Enable all public access block settings on CloudTrail bucket",
                        cis_control="CIS 3.3"
                    ))
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchPublicAccessBlockConfiguration':
                    self.findings.append(self.create_finding(
                        check_id="CT-010",
                        title="CloudTrail bucket has no public access block",
                        description=f"S3 bucket '{bucket_name}' for CloudTrail has no public access block configured",
                        severity="high",
                        resource_type="AWS::S3::Bucket",
                        resource_id=bucket_name,
                        region=region,
                        recommendation="Enable public access block on CloudTrail bucket",
                        cis_control="CIS 3.3"
                    ))
                    
        except ClientError:
            pass
