"""
CloudGuard Tests
"""

import pytest
from click.testing import CliRunner
from cloudguard.cli import cli
from cloudguard.reports import ReportGenerator


class TestCLI:
    """Test CLI commands."""
    
    def test_cli_help(self):
        """Test that help command works."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'CloudGuard' in result.output
    
    def test_scan_help(self):
        """Test that scan help works."""
        runner = CliRunner()
        result = runner.invoke(cli, ['scan', '--help'])
        assert result.exit_code == 0
        assert '--profile' in result.output
        assert '--service' in result.output
    
    def test_list_services(self):
        """Test list-services command."""
        runner = CliRunner()
        result = runner.invoke(cli, ['list-services'])
        assert result.exit_code == 0
        assert 'S3' in result.output
        assert 'IAM' in result.output
    
    def test_version(self):
        """Test version flag."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        assert '1.0.0' in result.output


class TestReportGenerator:
    """Test report generation."""
    
    def test_empty_findings(self):
        """Test report with no findings."""
        report = ReportGenerator([])
        summary = report.get_summary()
        
        assert summary['total'] == 0
        assert summary['by_severity']['critical'] == 0
    
    def test_findings_summary(self):
        """Test findings are summarized correctly."""
        findings = [
            {'severity': 'critical', 'resource_type': 'AWS::S3::Bucket'},
            {'severity': 'critical', 'resource_type': 'AWS::S3::Bucket'},
            {'severity': 'high', 'resource_type': 'AWS::IAM::User'},
            {'severity': 'medium', 'resource_type': 'AWS::EC2::Instance'},
        ]
        
        report = ReportGenerator(findings)
        summary = report.get_summary()
        
        assert summary['total'] == 4
        assert summary['by_severity']['critical'] == 2
        assert summary['by_severity']['high'] == 1
        assert summary['by_severity']['medium'] == 1
        assert summary['by_severity']['low'] == 0
    
    def test_json_output(self, tmp_path):
        """Test JSON report generation."""
        findings = [
            {
                'severity': 'high',
                'resource_type': 'AWS::S3::Bucket',
                'resource_id': 'test-bucket',
                'title': 'Test Finding'
            }
        ]
        
        report = ReportGenerator(findings)
        output_file = tmp_path / "report.json"
        report.save_json(str(output_file))
        
        assert output_file.exists()
        
        import json
        with open(output_file) as f:
            data = json.load(f)
        
        assert 'findings' in data
        assert 'summary' in data
        assert len(data['findings']) == 1
    
    def test_html_output(self, tmp_path):
        """Test HTML report generation."""
        findings = [
            {
                'severity': 'critical',
                'resource_type': 'AWS::S3::Bucket',
                'resource_id': 'test-bucket',
                'title': 'Test Finding',
                'description': 'Test description',
                'recommendation': 'Test recommendation',
                'region': 'us-east-1',
                'cis_control': 'CIS 1.1'
            }
        ]
        
        report = ReportGenerator(findings)
        output_file = tmp_path / "report.html"
        report.save_html(str(output_file))
        
        assert output_file.exists()
        
        content = output_file.read_text()
        assert 'CloudGuard' in content
        assert 'Test Finding' in content
        assert 'critical' in content.lower()


# Integration tests (require AWS credentials)
class TestIntegration:
    """Integration tests that require AWS access."""
    
    @pytest.mark.skip(reason="Requires AWS credentials")
    def test_verify_credentials(self):
        """Test credential verification."""
        runner = CliRunner()
        result = runner.invoke(cli, ['verify'])
        assert result.exit_code == 0
    
    @pytest.mark.skip(reason="Requires AWS credentials")
    def test_scan_s3(self):
        """Test S3 scan."""
        runner = CliRunner()
        result = runner.invoke(cli, ['scan', '--service', 's3', '--quiet'])
        assert result.exit_code == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
