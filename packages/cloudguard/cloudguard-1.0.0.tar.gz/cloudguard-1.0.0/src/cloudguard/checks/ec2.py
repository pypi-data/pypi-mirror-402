"""
CloudGuard - EC2 Security Checks
Scans EC2 instances and security groups for security compliance issues
"""

from typing import List, Dict
from botocore.exceptions import ClientError

from cloudguard.checks.base import BaseSecurityCheck


# Risky ports that should not be open to the world
RISKY_PORTS = {
    22: 'SSH',
    3389: 'RDP',
    3306: 'MySQL',
    5432: 'PostgreSQL',
    1433: 'MSSQL',
    27017: 'MongoDB',
    6379: 'Redis',
    11211: 'Memcached',
    9200: 'Elasticsearch',
    5601: 'Kibana',
    23: 'Telnet',
    21: 'FTP',
    445: 'SMB',
    135: 'RPC'
}


class EC2SecurityCheck(BaseSecurityCheck):
    """Security checks for Amazon EC2."""
    
    def run_checks(self) -> List[Dict]:
        """Run all EC2 security checks."""
        self.findings = []
        
        # Get regions to scan
        if self.region:
            regions = [self.region]
        else:
            regions = self.get_all_regions()
        
        for region in regions:
            ec2_client = self.get_client('ec2', region)
            
            # Security group checks
            self._check_security_groups(ec2_client, region)
            
            # EBS encryption checks
            self._check_ebs_encryption(ec2_client, region)
            
            # IMDSv2 checks
            self._check_imdsv2(ec2_client, region)
            
            # Public AMI checks
            self._check_public_amis(ec2_client, region)
            
            # Default security group checks
            self._check_default_security_groups(ec2_client, region)
        
        return self.findings
    
    def _check_security_groups(self, client, region: str):
        """Check security groups for risky open ports."""
        try:
            paginator = client.get_paginator('describe_security_groups')
            
            for page in paginator.paginate():
                for sg in page['SecurityGroups']:
                    sg_id = sg['SecurityGroupId']
                    sg_name = sg.get('GroupName', 'Unknown')
                    
                    for permission in sg.get('IpPermissions', []):
                        from_port = permission.get('FromPort', 0)
                        to_port = permission.get('ToPort', 65535)
                        
                        # Check for open to world (0.0.0.0/0 or ::/0)
                        open_cidrs = []
                        for ip_range in permission.get('IpRanges', []):
                            if ip_range.get('CidrIp') == '0.0.0.0/0':
                                open_cidrs.append('0.0.0.0/0')
                        for ip_range in permission.get('Ipv6Ranges', []):
                            if ip_range.get('CidrIpv6') == '::/0':
                                open_cidrs.append('::/0')
                        
                        if not open_cidrs:
                            continue
                        
                        # Check if risky ports are exposed
                        for port, service in RISKY_PORTS.items():
                            if from_port <= port <= to_port:
                                self.findings.append(self.create_finding(
                                    check_id="EC2-001",
                                    title=f"Security group allows {service} from internet",
                                    description=f"Security group '{sg_name}' ({sg_id}) allows port {port} ({service}) from {', '.join(open_cidrs)}",
                                    severity="critical" if port in [22, 3389, 23] else "high",
                                    resource_type="AWS::EC2::SecurityGroup",
                                    resource_id=sg_id,
                                    region=region,
                                    recommendation=f"Restrict port {port} access to specific IP ranges",
                                    cis_control="CIS 5.2" if port == 22 else "CIS 5.3" if port == 3389 else "CIS 5.4",
                                    details={
                                        "group_name": sg_name,
                                        "port": port,
                                        "service": service,
                                        "open_to": open_cidrs
                                    }
                                ))
                        
                        # Check for all ports open
                        if from_port == 0 and to_port == 65535:
                            self.findings.append(self.create_finding(
                                check_id="EC2-002",
                                title="Security group allows all ports from internet",
                                description=f"Security group '{sg_name}' ({sg_id}) allows all ports from {', '.join(open_cidrs)}",
                                severity="critical",
                                resource_type="AWS::EC2::SecurityGroup",
                                resource_id=sg_id,
                                region=region,
                                recommendation="Restrict access to only required ports",
                                cis_control="CIS 5.4"
                            ))
                            
        except ClientError:
            pass
    
    def _check_ebs_encryption(self, client, region: str):
        """Check for unencrypted EBS volumes."""
        try:
            paginator = client.get_paginator('describe_volumes')
            
            for page in paginator.paginate():
                for volume in page['Volumes']:
                    if not volume.get('Encrypted', False):
                        volume_id = volume['VolumeId']
                        
                        # Get attached instance info
                        attachments = volume.get('Attachments', [])
                        attached_to = [a.get('InstanceId', 'Unattached') for a in attachments]
                        
                        self.findings.append(self.create_finding(
                            check_id="EC2-003",
                            title="EBS volume not encrypted",
                            description=f"Volume '{volume_id}' is not encrypted",
                            severity="high",
                            resource_type="AWS::EC2::Volume",
                            resource_id=volume_id,
                            region=region,
                            recommendation="Enable encryption for EBS volumes. Create encrypted snapshot and new volume.",
                            cis_control="CIS 2.2.1",
                            details={"attached_to": attached_to}
                        ))
                        
        except ClientError:
            pass
    
    def _check_imdsv2(self, client, region: str):
        """Check if instances enforce IMDSv2."""
        try:
            paginator = client.get_paginator('describe_instances')
            
            for page in paginator.paginate():
                for reservation in page['Reservations']:
                    for instance in reservation['Instances']:
                        if instance['State']['Name'] != 'running':
                            continue
                        
                        instance_id = instance['InstanceId']
                        metadata_options = instance.get('MetadataOptions', {})
                        
                        http_tokens = metadata_options.get('HttpTokens', 'optional')
                        
                        if http_tokens != 'required':
                            # Get instance name
                            name_tag = next(
                                (t['Value'] for t in instance.get('Tags', []) if t['Key'] == 'Name'),
                                'Unnamed'
                            )
                            
                            self.findings.append(self.create_finding(
                                check_id="EC2-004",
                                title="EC2 instance does not enforce IMDSv2",
                                description=f"Instance '{name_tag}' ({instance_id}) allows IMDSv1",
                                severity="medium",
                                resource_type="AWS::EC2::Instance",
                                resource_id=instance_id,
                                region=region,
                                recommendation="Configure instance to require IMDSv2 (HttpTokens=required)",
                                cis_control="CIS 5.6",
                                details={"instance_name": name_tag}
                            ))
                            
        except ClientError:
            pass
    
    def _check_public_amis(self, client, region: str):
        """Check for AMIs that are publicly shared."""
        try:
            # Get account ID
            sts = self.session.client('sts')
            account_id = sts.get_caller_identity()['Account']
            
            # List AMIs owned by this account
            amis = client.describe_images(Owners=[account_id])
            
            for ami in amis.get('Images', []):
                if ami.get('Public', False):
                    self.findings.append(self.create_finding(
                        check_id="EC2-005",
                        title="AMI is publicly accessible",
                        description=f"AMI '{ami['ImageId']}' ({ami.get('Name', 'Unnamed')}) is public",
                        severity="high",
                        resource_type="AWS::EC2::Image",
                        resource_id=ami['ImageId'],
                        region=region,
                        recommendation="Make the AMI private unless intentionally sharing",
                        cis_control="CIS 2.1.4",
                        details={"ami_name": ami.get('Name', 'Unnamed')}
                    ))
                    
        except ClientError:
            pass
    
    def _check_default_security_groups(self, client, region: str):
        """Check that default security groups restrict all traffic."""
        try:
            vpcs = client.describe_vpcs()['Vpcs']
            
            for vpc in vpcs:
                vpc_id = vpc['VpcId']
                
                # Get default security group
                sgs = client.describe_security_groups(
                    Filters=[
                        {'Name': 'vpc-id', 'Values': [vpc_id]},
                        {'Name': 'group-name', 'Values': ['default']}
                    ]
                )
                
                for sg in sgs.get('SecurityGroups', []):
                    sg_id = sg['SecurityGroupId']
                    
                    # Check for any inbound rules
                    if sg.get('IpPermissions'):
                        self.findings.append(self.create_finding(
                            check_id="EC2-006",
                            title="Default security group has inbound rules",
                            description=f"Default security group in VPC '{vpc_id}' allows inbound traffic",
                            severity="medium",
                            resource_type="AWS::EC2::SecurityGroup",
                            resource_id=sg_id,
                            region=region,
                            recommendation="Remove all rules from default security group",
                            cis_control="CIS 5.4"
                        ))
                    
                    # Check for any outbound rules beyond default
                    outbound = sg.get('IpPermissionsEgress', [])
                    has_custom_outbound = False
                    for rule in outbound:
                        # Default allows all outbound - check if it's the default rule
                        if rule.get('IpProtocol') == '-1':
                            for ip_range in rule.get('IpRanges', []):
                                if ip_range.get('CidrIp') == '0.0.0.0/0':
                                    has_custom_outbound = True
                    
                    if has_custom_outbound:
                        self.findings.append(self.create_finding(
                            check_id="EC2-007",
                            title="Default security group allows outbound traffic",
                            description=f"Default security group in VPC '{vpc_id}' allows all outbound traffic",
                            severity="low",
                            resource_type="AWS::EC2::SecurityGroup",
                            resource_id=sg_id,
                            region=region,
                            recommendation="Restrict outbound rules in default security group",
                            cis_control="CIS 5.4"
                        ))
                        
        except ClientError:
            pass
