"""
CloudGuard - VPC Security Checks
Scans VPC configuration for security compliance issues
"""

from typing import List, Dict
from botocore.exceptions import ClientError

from cloudguard.checks.base import BaseSecurityCheck


class VPCSecurityCheck(BaseSecurityCheck):
    """Security checks for Amazon VPC."""
    
    def run_checks(self) -> List[Dict]:
        """Run all VPC security checks."""
        self.findings = []
        
        # Get regions to scan
        if self.region:
            regions = [self.region]
        else:
            regions = self.get_all_regions()
        
        for region in regions:
            ec2_client = self.get_client('ec2', region)
            
            # VPC flow logs check
            self._check_vpc_flow_logs(ec2_client, region)
            
            # Network ACL checks
            self._check_network_acls(ec2_client, region)
            
            # Internet gateway checks
            self._check_internet_gateways(ec2_client, region)
            
            # Peering connection checks
            self._check_peering_connections(ec2_client, region)
        
        return self.findings
    
    def _check_vpc_flow_logs(self, client, region: str):
        """Check if VPCs have flow logs enabled."""
        try:
            vpcs = client.describe_vpcs()['Vpcs']
            
            for vpc in vpcs:
                vpc_id = vpc['VpcId']
                
                # Get VPC name
                vpc_name = next(
                    (t['Value'] for t in vpc.get('Tags', []) if t['Key'] == 'Name'),
                    'Unnamed'
                )
                
                # Check for flow logs
                flow_logs = client.describe_flow_logs(
                    Filters=[{'Name': 'resource-id', 'Values': [vpc_id]}]
                )
                
                if not flow_logs.get('FlowLogs'):
                    self.findings.append(self.create_finding(
                        check_id="VPC-001",
                        title="VPC flow logs not enabled",
                        description=f"VPC '{vpc_name}' ({vpc_id}) does not have flow logs enabled",
                        severity="medium",
                        resource_type="AWS::EC2::VPC",
                        resource_id=vpc_id,
                        region=region,
                        recommendation="Enable VPC flow logs for network traffic monitoring",
                        cis_control="CIS 3.9",
                        details={"vpc_name": vpc_name}
                    ))
                else:
                    # Check if any flow log is active
                    active_logs = [f for f in flow_logs['FlowLogs'] if f['FlowLogStatus'] == 'ACTIVE']
                    if not active_logs:
                        self.findings.append(self.create_finding(
                            check_id="VPC-001",
                            title="VPC flow logs not active",
                            description=f"VPC '{vpc_name}' ({vpc_id}) has flow logs but none are active",
                            severity="medium",
                            resource_type="AWS::EC2::VPC",
                            resource_id=vpc_id,
                            region=region,
                            recommendation="Ensure VPC flow logs are active",
                            cis_control="CIS 3.9",
                            details={"vpc_name": vpc_name}
                        ))
                        
        except ClientError:
            pass
    
    def _check_network_acls(self, client, region: str):
        """Check network ACLs for overly permissive rules."""
        try:
            nacls = client.describe_network_acls()['NetworkAcls']
            
            for nacl in nacls:
                nacl_id = nacl['NetworkAclId']
                vpc_id = nacl['VpcId']
                is_default = nacl.get('IsDefault', False)
                
                for entry in nacl.get('Entries', []):
                    # Skip default deny rules
                    if entry.get('RuleNumber') == 32767:
                        continue
                    
                    # Check for allow all inbound from 0.0.0.0/0
                    if (entry.get('Egress') == False and 
                        entry.get('RuleAction') == 'allow' and
                        entry.get('CidrBlock') == '0.0.0.0/0' and
                        entry.get('Protocol') == '-1'):
                        
                        self.findings.append(self.create_finding(
                            check_id="VPC-002",
                            title="Network ACL allows all inbound traffic",
                            description=f"Network ACL '{nacl_id}' allows all inbound traffic from anywhere",
                            severity="high",
                            resource_type="AWS::EC2::NetworkAcl",
                            resource_id=nacl_id,
                            region=region,
                            recommendation="Restrict network ACL rules to specific ports and CIDR ranges",
                            cis_control="CIS 5.1",
                            details={
                                "vpc_id": vpc_id,
                                "is_default": is_default,
                                "rule_number": entry.get('RuleNumber')
                            }
                        ))
                    
                    # Check for specific risky ports open inbound
                    risky_ports = {22: 'SSH', 3389: 'RDP', 23: 'Telnet'}
                    
                    if (entry.get('Egress') == False and 
                        entry.get('RuleAction') == 'allow' and
                        entry.get('CidrBlock') == '0.0.0.0/0'):
                        
                        port_range = entry.get('PortRange', {})
                        from_port = port_range.get('From', 0)
                        to_port = port_range.get('To', 65535)
                        
                        for port, service in risky_ports.items():
                            if from_port <= port <= to_port:
                                self.findings.append(self.create_finding(
                                    check_id="VPC-003",
                                    title=f"Network ACL allows {service} from internet",
                                    description=f"Network ACL '{nacl_id}' allows {service} (port {port}) from 0.0.0.0/0",
                                    severity="high",
                                    resource_type="AWS::EC2::NetworkAcl",
                                    resource_id=nacl_id,
                                    region=region,
                                    recommendation=f"Restrict {service} access to specific IP ranges",
                                    cis_control="CIS 5.1",
                                    details={
                                        "vpc_id": vpc_id,
                                        "port": port,
                                        "service": service
                                    }
                                ))
                                
        except ClientError:
            pass
    
    def _check_internet_gateways(self, client, region: str):
        """Check for VPCs with multiple internet gateways or unexpected attachments."""
        try:
            igws = client.describe_internet_gateways()['InternetGateways']
            
            vpc_igw_count = {}
            
            for igw in igws:
                for attachment in igw.get('Attachments', []):
                    vpc_id = attachment.get('VpcId')
                    if vpc_id:
                        vpc_igw_count[vpc_id] = vpc_igw_count.get(vpc_id, 0) + 1
            
            # Report VPCs with multiple IGWs (unusual)
            for vpc_id, count in vpc_igw_count.items():
                if count > 1:
                    self.findings.append(self.create_finding(
                        check_id="VPC-004",
                        title="VPC has multiple internet gateways",
                        description=f"VPC '{vpc_id}' has {count} internet gateways attached",
                        severity="low",
                        resource_type="AWS::EC2::VPC",
                        resource_id=vpc_id,
                        region=region,
                        recommendation="Review if multiple internet gateways are necessary",
                        details={"igw_count": count}
                    ))
                    
        except ClientError:
            pass
    
    def _check_peering_connections(self, client, region: str):
        """Check VPC peering connections for security issues."""
        try:
            peerings = client.describe_vpc_peering_connections(
                Filters=[{'Name': 'status-code', 'Values': ['active']}]
            )
            
            for peering in peerings.get('VpcPeeringConnections', []):
                pcx_id = peering['VpcPeeringConnectionId']
                
                accepter = peering.get('AccepterVpcInfo', {})
                requester = peering.get('RequesterVpcInfo', {})
                
                # Check for cross-account peering
                if accepter.get('OwnerId') != requester.get('OwnerId'):
                    self.findings.append(self.create_finding(
                        check_id="VPC-005",
                        title="Cross-account VPC peering connection",
                        description=f"Peering connection '{pcx_id}' connects VPCs in different AWS accounts",
                        severity="low",
                        resource_type="AWS::EC2::VPCPeeringConnection",
                        resource_id=pcx_id,
                        region=region,
                        recommendation="Ensure cross-account peering is intentional and properly secured",
                        details={
                            "accepter_account": accepter.get('OwnerId'),
                            "requester_account": requester.get('OwnerId'),
                            "accepter_vpc": accepter.get('VpcId'),
                            "requester_vpc": requester.get('VpcId')
                        }
                    ))
                    
        except ClientError:
            pass
