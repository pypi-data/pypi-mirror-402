"""
CloudGuard - IAM Security Checks
Scans IAM configuration for security compliance issues
"""

import json
from typing import List, Dict
from datetime import datetime, timezone, timedelta
from botocore.exceptions import ClientError

from cloudguard.checks.base import BaseSecurityCheck


class IAMSecurityCheck(BaseSecurityCheck):
    """Security checks for AWS IAM."""
    
    def run_checks(self) -> List[Dict]:
        """Run all IAM security checks."""
        self.findings = []
        
        iam_client = self.get_client('iam')
        
        # Account-level checks
        self._check_root_mfa(iam_client)
        self._check_root_access_keys(iam_client)
        self._check_password_policy(iam_client)
        
        # User-level checks
        self._check_unused_credentials(iam_client)
        self._check_admin_privileges(iam_client)
        self._check_user_mfa(iam_client)
        
        # Policy checks
        self._check_wildcard_policies(iam_client)
        
        return self.findings
    
    def _check_root_mfa(self, client):
        """Check if root account has MFA enabled."""
        try:
            summary = client.get_account_summary()
            
            if summary['SummaryMap'].get('AccountMFAEnabled', 0) != 1:
                self.findings.append(self.create_finding(
                    check_id="IAM-001",
                    title="Root account MFA not enabled",
                    description="The root account does not have MFA enabled",
                    severity="critical",
                    resource_type="AWS::IAM::Account",
                    resource_id="root",
                    recommendation="Enable MFA for the root account immediately",
                    cis_control="CIS 1.5"
                ))
        except ClientError:
            pass
    
    def _check_root_access_keys(self, client):
        """Check if root account has access keys."""
        try:
            summary = client.get_account_summary()
            
            if summary['SummaryMap'].get('AccountAccessKeysPresent', 0) > 0:
                self.findings.append(self.create_finding(
                    check_id="IAM-002",
                    title="Root account has access keys",
                    description="The root account has active access keys",
                    severity="critical",
                    resource_type="AWS::IAM::Account",
                    resource_id="root",
                    recommendation="Delete root account access keys and use IAM users instead",
                    cis_control="CIS 1.4"
                ))
        except ClientError:
            pass
    
    def _check_password_policy(self, client):
        """Check if password policy meets security requirements."""
        try:
            policy = client.get_account_password_policy()['PasswordPolicy']
            
            issues = []
            
            if policy.get('MinimumPasswordLength', 0) < 14:
                issues.append("Minimum length less than 14 characters")
            if not policy.get('RequireSymbols', False):
                issues.append("Symbols not required")
            if not policy.get('RequireNumbers', False):
                issues.append("Numbers not required")
            if not policy.get('RequireUppercaseCharacters', False):
                issues.append("Uppercase not required")
            if not policy.get('RequireLowercaseCharacters', False):
                issues.append("Lowercase not required")
            if policy.get('MaxPasswordAge', 0) == 0 or policy.get('MaxPasswordAge', 999) > 90:
                issues.append("Password expiration not set or > 90 days")
            if policy.get('PasswordReusePrevention', 0) < 24:
                issues.append("Password reuse prevention less than 24")
            
            if issues:
                self.findings.append(self.create_finding(
                    check_id="IAM-003",
                    title="Password policy does not meet security requirements",
                    description="The account password policy has security weaknesses",
                    severity="high",
                    resource_type="AWS::IAM::AccountPasswordPolicy",
                    resource_id="password-policy",
                    recommendation="Strengthen the password policy to meet CIS requirements",
                    cis_control="CIS 1.8-1.11",
                    details={"issues": issues}
                ))
                
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchEntity':
                self.findings.append(self.create_finding(
                    check_id="IAM-003",
                    title="No password policy configured",
                    description="The account has no custom password policy",
                    severity="high",
                    resource_type="AWS::IAM::AccountPasswordPolicy",
                    resource_id="password-policy",
                    recommendation="Configure a strong password policy",
                    cis_control="CIS 1.8-1.11"
                ))
    
    def _check_unused_credentials(self, client):
        """Check for unused IAM credentials."""
        try:
            users = client.list_users()['Users']
            threshold_date = datetime.now(timezone.utc) - timedelta(days=90)
            
            for user in users:
                username = user['UserName']
                
                # Check password last used
                password_last_used = user.get('PasswordLastUsed')
                if password_last_used and password_last_used < threshold_date:
                    self.findings.append(self.create_finding(
                        check_id="IAM-004",
                        title="IAM user password unused for 90+ days",
                        description=f"User '{username}' has not used their password in over 90 days",
                        severity="medium",
                        resource_type="AWS::IAM::User",
                        resource_id=username,
                        recommendation="Review and disable or delete unused credentials",
                        cis_control="CIS 1.12"
                    ))
                
                # Check access keys
                try:
                    keys = client.list_access_keys(UserName=username)['AccessKeyMetadata']
                    for key in keys:
                        if key['Status'] == 'Active':
                            key_last_used = client.get_access_key_last_used(
                                AccessKeyId=key['AccessKeyId']
                            )['AccessKeyLastUsed']
                            
                            last_used_date = key_last_used.get('LastUsedDate')
                            if last_used_date and last_used_date < threshold_date:
                                self.findings.append(self.create_finding(
                                    check_id="IAM-005",
                                    title="IAM access key unused for 90+ days",
                                    description=f"Access key for user '{username}' unused for 90+ days",
                                    severity="medium",
                                    resource_type="AWS::IAM::AccessKey",
                                    resource_id=key['AccessKeyId'],
                                    recommendation="Rotate or delete unused access keys",
                                    cis_control="CIS 1.12"
                                ))
                except ClientError:
                    pass
                    
        except ClientError:
            pass
    
    def _check_admin_privileges(self, client):
        """Check for users with full administrator privileges."""
        try:
            users = client.list_users()['Users']
            
            for user in users:
                username = user['UserName']
                
                # Check attached policies
                attached = client.list_attached_user_policies(UserName=username)
                for policy in attached.get('AttachedPolicies', []):
                    if policy['PolicyArn'] == 'arn:aws:iam::aws:policy/AdministratorAccess':
                        self.findings.append(self.create_finding(
                            check_id="IAM-006",
                            title="IAM user has full administrator privileges",
                            description=f"User '{username}' has AdministratorAccess policy attached",
                            severity="high",
                            resource_type="AWS::IAM::User",
                            resource_id=username,
                            recommendation="Apply principle of least privilege - use specific permissions",
                            cis_control="CIS 1.16"
                        ))
                
                # Check group memberships for admin
                groups = client.list_groups_for_user(UserName=username)
                for group in groups.get('Groups', []):
                    group_policies = client.list_attached_group_policies(GroupName=group['GroupName'])
                    for policy in group_policies.get('AttachedPolicies', []):
                        if policy['PolicyArn'] == 'arn:aws:iam::aws:policy/AdministratorAccess':
                            self.findings.append(self.create_finding(
                                check_id="IAM-006",
                                title="IAM user has admin via group membership",
                                description=f"User '{username}' has AdministratorAccess via group '{group['GroupName']}'",
                                severity="high",
                                resource_type="AWS::IAM::User",
                                resource_id=username,
                                recommendation="Apply principle of least privilege - use specific permissions",
                                cis_control="CIS 1.16"
                            ))
                            
        except ClientError:
            pass
    
    def _check_user_mfa(self, client):
        """Check if IAM users have MFA enabled."""
        try:
            users = client.list_users()['Users']
            
            for user in users:
                username = user['UserName']
                
                # Check if user has console access
                try:
                    client.get_login_profile(UserName=username)
                    has_console_access = True
                except ClientError as e:
                    if e.response['Error']['Code'] == 'NoSuchEntity':
                        has_console_access = False
                    else:
                        continue
                
                if has_console_access:
                    # Check MFA devices
                    mfa_devices = client.list_mfa_devices(UserName=username)
                    if not mfa_devices.get('MFADevices'):
                        self.findings.append(self.create_finding(
                            check_id="IAM-007",
                            title="IAM user without MFA",
                            description=f"User '{username}' has console access but no MFA enabled",
                            severity="high",
                            resource_type="AWS::IAM::User",
                            resource_id=username,
                            recommendation="Enable MFA for all users with console access",
                            cis_control="CIS 1.6"
                        ))
                        
        except ClientError:
            pass
    
    def _check_wildcard_policies(self, client):
        """Check for policies with dangerous wildcard permissions."""
        try:
            paginator = client.get_paginator('list_policies')
            
            for page in paginator.paginate(Scope='Local'):
                for policy in page['Policies']:
                    policy_arn = policy['Arn']
                    
                    # Get the policy document
                    version = client.get_policy_version(
                        PolicyArn=policy_arn,
                        VersionId=policy['DefaultVersionId']
                    )
                    
                    document = version['PolicyVersion']['Document']
                    if isinstance(document, str):
                        document = json.loads(document)
                    
                    # Check for wildcard permissions
                    statements = document.get('Statement', [])
                    if not isinstance(statements, list):
                        statements = [statements]
                    
                    for statement in statements:
                        if statement.get('Effect') == 'Allow':
                            actions = statement.get('Action', [])
                            resources = statement.get('Resource', [])
                            
                            if not isinstance(actions, list):
                                actions = [actions]
                            if not isinstance(resources, list):
                                resources = [resources]
                            
                            if '*' in actions and '*' in resources:
                                self.findings.append(self.create_finding(
                                    check_id="IAM-008",
                                    title="Policy with full wildcard permissions",
                                    description=f"Policy '{policy['PolicyName']}' grants Action:* on Resource:*",
                                    severity="critical",
                                    resource_type="AWS::IAM::Policy",
                                    resource_id=policy_arn,
                                    recommendation="Apply principle of least privilege - specify exact permissions needed",
                                    cis_control="CIS 1.16"
                                ))
                                
        except ClientError:
            pass
