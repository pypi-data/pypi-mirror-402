"""
CloudGuard - Base Security Check Class
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime, timezone
import boto3


class BaseSecurityCheck(ABC):
    """Base class for all security checks."""
    
    def __init__(self, session: boto3.Session, region: Optional[str], scan_id: str):
        """
        Initialize the security check.
        
        Args:
            session: Boto3 session to use
            region: AWS region to scan
            scan_id: Unique identifier for this scan
        """
        self.session = session
        self.region = region
        self.scan_id = scan_id
        self.findings = []
    
    @abstractmethod
    def run_checks(self) -> List[Dict]:
        """Run all security checks and return findings."""
        pass
    
    def create_finding(
        self,
        check_id: str,
        title: str,
        description: str,
        severity: str,
        resource_type: str,
        resource_id: str,
        region: str = "global",
        recommendation: str = "",
        cis_control: str = "",
        details: Dict = None
    ) -> Dict:
        """
        Create a standardized finding dictionary.
        
        Args:
            check_id: Unique identifier for this check type
            title: Short title of the finding
            description: Detailed description of the issue
            severity: critical, high, medium, or low
            resource_type: Type of AWS resource
            resource_id: Identifier of the affected resource
            region: AWS region where resource exists
            recommendation: How to remediate the issue
            cis_control: Related CIS benchmark control
            details: Additional details dictionary
            
        Returns:
            Standardized finding dictionary
        """
        finding = {
            "scan_id": self.scan_id,
            "check_id": check_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "title": title,
            "description": description,
            "severity": severity,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "region": region,
            "recommendation": recommendation,
            "cis_control": cis_control,
            "details": details or {}
        }
        return finding
    
    def get_client(self, service_name: str, region: str = None):
        """Get a boto3 client for the specified service."""
        return self.session.client(service_name, region_name=region or self.region)
    
    def get_all_regions(self) -> List[str]:
        """Get list of all enabled AWS regions."""
        ec2 = self.session.client('ec2', region_name='us-east-1')
        regions = ec2.describe_regions(AllRegions=False)
        return [r['RegionName'] for r in regions['Regions']]
