"""Report generator for formatting and outputting discovered API endpoints."""

import json
import csv
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import pandas as pd
from jinja2 import Template

from .endpoint_extractor import Endpoint
from ..config import config

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generate reports of discovered API endpoints in various formats."""
    
    def __init__(self):
        self.output_format = config.get('output.format', 'json')
        self.output_file = config.get('output.file', 'endpoints.json')
        self.include_metadata = config.get('output.include_metadata', True)
        self.pretty_print = config.get('output.pretty_print', True)
        self.include_sections = config.get('output.include_sections', {})
    
    def generate_report(self, endpoints: List[Endpoint], target_url: str, scan_duration: float) -> str:
        """Generate a report in the configured format.
        
        Args:
            endpoints: List of discovered endpoints
            target_url: The target URL that was scanned
            scan_duration: Time taken for the scan in seconds
            
        Returns:
            Path to the generated report file
        """
        # Prepare report data
        report_data = self._prepare_report_data(endpoints, target_url, scan_duration)
        
        # Generate report based on format
        if self.output_format.lower() == 'json':
            return self._generate_json_report(report_data)
        elif self.output_format.lower() == 'csv':
            return self._generate_csv_report(endpoints)
        elif self.output_format.lower() == 'html':
            return self._generate_html_report(report_data)
        elif self.output_format.lower() == 'markdown':
            return self._generate_markdown_report(report_data)
        else:
            raise ValueError(f"Unsupported output format: {self.output_format}")
    
    def _prepare_report_data(self, endpoints: List[Endpoint], target_url: str, scan_duration: float) -> Dict[str, Any]:
        """Prepare structured data for report generation."""
        # Convert endpoints to dictionaries
        endpoint_dicts = []
        for endpoint in endpoints:
            endpoint_dict = {
                'url': endpoint.url,
                'method': endpoint.method,
                'type': endpoint.endpoint_type,
                'parameters': endpoint.parameters,
                'headers': endpoint.headers,
                'source': endpoint.source,
                'confidence': endpoint.confidence,
                'discovered_at': endpoint.discovered_at
            }
            
            if self.include_metadata:
                endpoint_dict['metadata'] = endpoint.metadata
            
            endpoint_dicts.append(endpoint_dict)
        
        # Generate statistics
        stats = self._generate_statistics(endpoints)
        
        # Prepare report structure
        report_data = {}
        
        if self.include_sections.get('summary', True):
            report_data['summary'] = {
                'target_url': target_url,
                'scan_duration_seconds': round(scan_duration, 2),
                'total_endpoints': len(endpoints),
                'scan_timestamp': datetime.now().isoformat(),
                'scraper_version': '0.1.0'
            }
        
        if self.include_sections.get('statistics', True):
            report_data['statistics'] = stats
        
        if self.include_sections.get('endpoints', True):
            report_data['endpoints'] = endpoint_dicts
        
        return report_data
    
    def _generate_statistics(self, endpoints: List[Endpoint]) -> Dict[str, Any]:
        """Generate statistics about discovered endpoints."""
        if not endpoints:
            return {}
        
        # Count by type
        type_counts = {}
        for endpoint in endpoints:
            endpoint_type = endpoint.endpoint_type
            type_counts[endpoint_type] = type_counts.get(endpoint_type, 0) + 1
        
        # Count by method
        method_counts = {}
        for endpoint in endpoints:
            method = endpoint.method
            method_counts[method] = method_counts.get(method, 0) + 1
        
        # Count by source
        source_counts = {}
        for endpoint in endpoints:
            source = endpoint.source
            source_counts[source] = source_counts.get(source, 0) + 1
        
        # Confidence distribution
        confidence_ranges = {
            'high (0.8-1.0)': 0,
            'medium (0.6-0.8)': 0,
            'low (0.0-0.6)': 0
        }
        
        for endpoint in endpoints:
            conf = endpoint.confidence
            if conf >= 0.8:
                confidence_ranges['high (0.8-1.0)'] += 1
            elif conf >= 0.6:
                confidence_ranges['medium (0.6-0.8)'] += 1
            else:
                confidence_ranges['low (0.0-0.6)'] += 1
        
        # Average confidence
        avg_confidence = sum(ep.confidence for ep in endpoints) / len(endpoints)
        
        return {
            'by_type': type_counts,
            'by_method': method_counts,
            'by_source': source_counts,
            'confidence_distribution': confidence_ranges,
            'average_confidence': round(avg_confidence, 3),
            'unique_domains': len(set(self._extract_domain(ep.url) for ep in endpoints))
        }
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc
    
    def _generate_json_report(self, report_data: Dict[str, Any]) -> str:
        """Generate JSON format report."""
        # Ensure output directory exists
        output_path = Path(self.output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write JSON report
        with open(output_path, 'w', encoding='utf-8') as f:
            if self.pretty_print:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            else:
                json.dump(report_data, f, ensure_ascii=False)
        
        logger.info(f"JSON report generated: {output_path}")
        return str(output_path)
    
    def _generate_csv_report(self, endpoints: List[Endpoint]) -> str:
        """Generate CSV format report."""
        # Change file extension to .csv
        output_path = Path(self.output_file).with_suffix('.csv')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Prepare data for CSV
        csv_data = []
        for endpoint in endpoints:
            row = {
                'URL': endpoint.url,
                'Method': endpoint.method,
                'Type': endpoint.endpoint_type,
                'Parameters': ', '.join(endpoint.parameters),
                'Source': endpoint.source,
                'Confidence': endpoint.confidence,
                'Discovered At': endpoint.discovered_at
            }
            
            if self.include_metadata:
                # Flatten metadata
                for key, value in endpoint.metadata.items():
                    row[f'Metadata_{key}'] = str(value)
            
            csv_data.append(row)
        
        # Write CSV using pandas for better handling
        df = pd.DataFrame(csv_data)
        df.to_csv(output_path, index=False)
        
        logger.info(f"CSV report generated: {output_path}")
        return str(output_path)
    
    def _generate_html_report(self, report_data: Dict[str, Any]) -> str:
        """Generate HTML format report."""
        # Change file extension to .html
        output_path = Path(self.output_file).with_suffix('.html')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # HTML template
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Endpoint Discovery Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1, h2, h3 { color: #333; }
        .summary { background: #e8f4fd; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .stat-card { background: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid #007bff; }
        .endpoint { border: 1px solid #ddd; margin-bottom: 10px; border-radius: 5px; overflow: hidden; }
        .endpoint-header { background: #f8f9fa; padding: 10px; font-weight: bold; }
        .endpoint-body { padding: 10px; }
        .method { padding: 2px 8px; border-radius: 3px; color: white; font-size: 12px; font-weight: bold; }
        .method-GET { background: #28a745; }
        .method-POST { background: #007bff; }
        .method-PUT { background: #ffc107; color: #000; }
        .method-DELETE { background: #dc3545; }
        .method-PATCH { background: #6f42c1; }
        .confidence { float: right; }
        .confidence-high { color: #28a745; }
        .confidence-medium { color: #ffc107; }
        .confidence-low { color: #dc3545; }
        .type-rest { border-left-color: #28a745; }
        .type-graphql { border-left-color: #e10098; }
        .type-websocket { border-left-color: #ff6b6b; }
        .type-other { border-left-color: #6c757d; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f8f9fa; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 API Endpoint Discovery Report</h1>
        
        {% if summary %}
        <div class="summary">
            <h2>📊 Scan Summary</h2>
            <p><strong>Target URL:</strong> {{ summary.target_url }}</p>
            <p><strong>Scan Duration:</strong> {{ summary.scan_duration_seconds }} seconds</p>
            <p><strong>Total Endpoints Found:</strong> {{ summary.total_endpoints }}</p>
            <p><strong>Scan Timestamp:</strong> {{ summary.scan_timestamp }}</p>
        </div>
        {% endif %}
        
        {% if statistics %}
        <h2>📈 Statistics</h2>
        <div class="stats">
            <div class="stat-card">
                <h3>By Type</h3>
                {% for type, count in statistics.by_type.items() %}
                <p>{{ type|title }}: {{ count }}</p>
                {% endfor %}
            </div>
            <div class="stat-card">
                <h3>By Method</h3>
                {% for method, count in statistics.by_method.items() %}
                <p>{{ method }}: {{ count }}</p>
                {% endfor %}
            </div>
            <div class="stat-card">
                <h3>By Source</h3>
                {% for source, count in statistics.by_source.items() %}
                <p>{{ source|title }}: {{ count }}</p>
                {% endfor %}
            </div>
            <div class="stat-card">
                <h3>Confidence</h3>
                <p>Average: {{ statistics.average_confidence }}</p>
                {% for range, count in statistics.confidence_distribution.items() %}
                <p>{{ range|title }}: {{ count }}</p>
                {% endfor %}
            </div>
        </div>
        {% endif %}
        
        {% if endpoints %}
        <h2>🎯 Discovered Endpoints ({{ endpoints|length }})</h2>
        {% for endpoint in endpoints %}
        <div class="endpoint type-{{ endpoint.type }}">
            <div class="endpoint-header">
                <span class="method method-{{ endpoint.method }}">{{ endpoint.method }}</span>
                {{ endpoint.url }}
                <span class="confidence confidence-{% if endpoint.confidence >= 0.8 %}high{% elif endpoint.confidence >= 0.6 %}medium{% else %}low{% endif %}">
                    {{ (endpoint.confidence * 100)|round }}% confidence
                </span>
            </div>
            <div class="endpoint-body">
                <p><strong>Type:</strong> {{ endpoint.type|title }}</p>
                <p><strong>Source:</strong> {{ endpoint.source|title }}</p>
                {% if endpoint.parameters %}
                <p><strong>Parameters:</strong> {{ endpoint.parameters|join(', ') }}</p>
                {% endif %}
                {% if endpoint.headers %}
                <p><strong>Headers:</strong></p>
                <table>
                    {% for key, value in endpoint.headers.items() %}
                    <tr><td>{{ key }}</td><td>{{ value }}</td></tr>
                    {% endfor %}
                </table>
                {% endif %}
                <p><strong>Discovered:</strong> {{ endpoint.discovered_at }}</p>
            </div>
        </div>
        {% endfor %}
        {% endif %}
        
        <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; text-align: center;">
            Generated by API Endpoint Scraper v0.1.0
        </footer>
    </div>
</body>
</html>
        """
        
        # Render template
        template = Template(html_template)
        html_content = template.render(**report_data)
        
        # Write HTML file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML report generated: {output_path}")
        return str(output_path)
    
    def _generate_markdown_report(self, report_data: Dict[str, Any]) -> str:
        """Generate Markdown format report."""
        # Change file extension to .md
        output_path = Path(self.output_file).with_suffix('.md')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Build markdown content
        md_lines = []
        md_lines.append("# 🔍 API Endpoint Discovery Report")
        md_lines.append("")
        
        # Summary section
        if 'summary' in report_data:
            summary = report_data['summary']
            md_lines.append("## 📊 Scan Summary")
            md_lines.append("")
            md_lines.append(f"- **Target URL:** {summary['target_url']}")
            md_lines.append(f"- **Scan Duration:** {summary['scan_duration_seconds']} seconds")
            md_lines.append(f"- **Total Endpoints Found:** {summary['total_endpoints']}")
            md_lines.append(f"- **Scan Timestamp:** {summary['scan_timestamp']}")
            md_lines.append("")
        
        # Statistics section
        if 'statistics' in report_data:
            stats = report_data['statistics']
            md_lines.append("## 📈 Statistics")
            md_lines.append("")
            
            if 'by_type' in stats:
                md_lines.append("### By Type")
                for endpoint_type, count in stats['by_type'].items():
                    md_lines.append(f"- {endpoint_type.title()}: {count}")
                md_lines.append("")
            
            if 'by_method' in stats:
                md_lines.append("### By Method")
                for method, count in stats['by_method'].items():
                    md_lines.append(f"- {method}: {count}")
                md_lines.append("")
            
            if 'by_source' in stats:
                md_lines.append("### By Source")
                for source, count in stats['by_source'].items():
                    md_lines.append(f"- {source.title()}: {count}")
                md_lines.append("")
            
            if 'average_confidence' in stats:
                md_lines.append(f"### Average Confidence: {stats['average_confidence']}")
                md_lines.append("")
        
        # Endpoints section
        if 'endpoints' in report_data:
            endpoints = report_data['endpoints']
            md_lines.append(f"## 🎯 Discovered Endpoints ({len(endpoints)})")
            md_lines.append("")
            
            for i, endpoint in enumerate(endpoints, 1):
                confidence_pct = round(endpoint['confidence'] * 100)
                md_lines.append(f"### {i}. `{endpoint['method']}` {endpoint['url']}")
                md_lines.append("")
                md_lines.append(f"- **Type:** {endpoint['type'].title()}")
                md_lines.append(f"- **Source:** {endpoint['source'].title()}")
                md_lines.append(f"- **Confidence:** {confidence_pct}%")
                
                if endpoint['parameters']:
                    md_lines.append(f"- **Parameters:** {', '.join(endpoint['parameters'])}")
                
                if endpoint['headers']:
                    md_lines.append("- **Headers:**")
                    for key, value in endpoint['headers'].items():
                        md_lines.append(f"  - `{key}`: {value}")
                
                md_lines.append(f"- **Discovered:** {endpoint['discovered_at']}")
                md_lines.append("")
        
        # Footer
        md_lines.append("---")
        md_lines.append("*Generated by API Endpoint Scraper v0.1.0*")
        
        # Write markdown file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(md_lines))
        
        logger.info(f"Markdown report generated: {output_path}")
        return str(output_path)
    
    def generate_multiple_formats(self, endpoints: List[Endpoint], target_url: str, scan_duration: float) -> List[str]:
        """Generate reports in multiple formats.
        
        Returns:
            List of generated file paths
        """
        formats = ['json', 'html', 'csv', 'markdown']
        generated_files = []
        
        original_format = self.output_format
        original_file = self.output_file
        
        try:
            for fmt in formats:
                self.output_format = fmt
                # Keep the same base name but change extension
                base_path = Path(original_file).with_suffix('')
                self.output_file = str(base_path) + f'.{fmt}'
                
                file_path = self.generate_report(endpoints, target_url, scan_duration)
                generated_files.append(file_path)
        
        finally:
            # Restore original settings
            self.output_format = original_format
            self.output_file = original_file
        
        return generated_files 