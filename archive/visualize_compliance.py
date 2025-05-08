import os
import json
import re
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from datetime import datetime
from pathlib import Path

def parse_pylint_results(file_path):
    """Extract useful metrics from Pylint results"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Extract score
    score = 0.0
    score_match = re.search(r'rated at (\d+\.\d+)/10', content)
    if score_match:
        score = float(score_match.group(1))
    
    # Count issue types
    issue_types = {
        'error': len(re.findall(r'E:', content)),
        'warning': len(re.findall(r'W:', content)),
        'convention': len(re.findall(r'C:', content)),
        'refactor': len(re.findall(r'R:', content)),
        'fatal': len(re.findall(r'F:', content))
    }
    
    # Extract issues per module
    module_pattern = r'\*{10} Module ([\w\.]+)'
    modules = re.findall(module_pattern, content)
    module_issues = {module: 0 for module in modules}
    
    for module in modules:
        # Count lines between this module and the next one (or end)
        start = content.find(f"************* Module {module}")
        if start != -1:
            next_module = content.find("************* Module", start + 1)
            if next_module == -1:
                next_module = len(content)
            
            module_section = content[start:next_module]
            # Count lines that look like issues
            issues = len(re.findall(r'[EWCRF]:', module_section))
            module_issues[module] = issues
    
    return {'score': score, 'issue_types': issue_types, 'module_issues': module_issues}

def parse_bandit_results(file_path):
    """Extract useful metrics from Bandit results"""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        results = data.get('results', [])
        
        # Count issues by severity
        severity_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        for issue in results:
            severity = issue.get('issue_severity', 'UNKNOWN')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Count issues by confidence
        confidence_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        for issue in results:
            confidence = issue.get('issue_confidence', 'UNKNOWN')
            confidence_counts[confidence] = confidence_counts.get(confidence, 0) + 1
        
        # Count issues by type
        issue_types = {}
        for issue in results:
            issue_type = issue.get('test_id', 'unknown')
            issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
        
        return {
            'total_issues': len(results),
            'severity_counts': severity_counts,
            'confidence_counts': confidence_counts,
            'issue_types': issue_types
        }
    except Exception as e:
        print(f"Error parsing Bandit results: {e}")
        return {'total_issues': 0, 'severity_counts': {}, 'confidence_counts': {}, 'issue_types': {}}

def parse_safety_results(file_path):
    """Extract useful metrics from Safety results"""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Count issues by severity
        severity_counts = {'high': 0, 'medium': 0, 'low': 0}
        for issue in data:
            vulnerabilities = issue.get('vulnerabilities', [])
            for vuln in vulnerabilities:
                severity = vuln.get('severity', 'unknown')
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Count issues by package
        package_counts = {}
        for issue in data:
            package = issue.get('name', 'unknown')
            package_counts[package] = package_counts.get(package, 0) + len(issue.get('vulnerabilities', []))
        
        return {
            'total_issues': len(data),
            'severity_counts': severity_counts,
            'package_counts': package_counts
        }
    except Exception as e:
        print(f"Error parsing Safety results: {e}")
        return {'total_issues': 0, 'severity_counts': {}, 'package_counts': {}}

def parse_djlint_results(file_path):
    """Extract useful metrics from djLint results"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Count total issues
        issues = [line for line in content.split('\n') if line.strip()]
        total_issues = len(issues)
        
        # Count issues by file
        file_pattern = r'([\w\/\.]+):\d+:\d+:'
        file_counts = {}
        for issue in issues:
            match = re.search(file_pattern, issue)
            if match:
                file_name = match.group(1)
                file_counts[file_name] = file_counts.get(file_name, 0) + 1
        
        # Count issues by type
        type_pattern = r': ([A-Z]\d{3}) '
        type_counts = {}
        for issue in issues:
            match = re.search(type_pattern, issue)
            if match:
                issue_type = match.group(1)
                type_counts[issue_type] = type_counts.get(issue_type, 0) + 1
        
        return {
            'total_issues': total_issues,
            'file_counts': file_counts,
            'type_counts': type_counts
        }
    except Exception as e:
        print(f"Error parsing djLint results: {e}")
        return {'total_issues': 0, 'file_counts': {}, 'type_counts': {}}

def generate_visualizations(results_dir):
    """Create visualizations from compliance results"""
    output_dir = Path(results_dir) / "visualizations"
    output_dir.mkdir(exist_ok=True)
    
    # Get the latest results of each type
    latest_bandit = max(Path(results_dir).glob("bandit_results_*.json"), default=None, key=os.path.getctime)
    latest_pylint = max(Path(results_dir).glob("pylint_results_*.txt"), default=None, key=os.path.getctime)
    latest_djlint = max(Path(results_dir).glob("djlint_results_*.txt"), default=None, key=os.path.getctime)
    latest_safety = max(Path(results_dir).glob("safety_results_*.json"), default=None, key=os.path.getctime)
    
    # Set a nice style for all plots
    plt.style.use('seaborn-v0_8-whitegrid')
    
    # Create timestamp for output files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Dictionary to store summary data for the final report
    summary_data = {}
    
    # Process Pylint results
    if latest_pylint:
        pylint_data = parse_pylint_results(latest_pylint)
        summary_data['pylint'] = pylint_data
        
        # Create score visualization
        plt.figure(figsize=(8, 6))
        score = pylint_data['score']
        colors = ['#ff6b6b', '#feca57', '#1dd1a1']
        color_idx = 0 if score < 3 else (1 if score < 7 else 2)
        
        plt.barh(['Pylint Score'], [score], color=colors[color_idx])
        plt.barh(['Pylint Score'], [10], color='#f1f2f6', alpha=0.3)
        
        for i, v in enumerate([score]):
            plt.text(v + 0.1, i, f"{v}/10", va='center', fontweight='bold')
        
        plt.xlim(0, 10.5)
        plt.title('Code Quality Score', fontsize=16)
        plt.tight_layout()
        plt.savefig(output_dir / f"pylint_score_{timestamp}.png", dpi=300)
        
        # Create issue types visualization
        plt.figure(figsize=(10, 6))
        issue_types = pylint_data['issue_types']
        labels = ['Error', 'Warning', 'Convention', 'Refactor', 'Fatal']
        values = [issue_types.get('error', 0), issue_types.get('warning', 0), 
                 issue_types.get('convention', 0), issue_types.get('refactor', 0),
                 issue_types.get('fatal', 0)]
        
        colors = ['#ff6b6b', '#feca57', '#48dbfb', '#1dd1a1', '#5f27cd']
        plt.bar(labels, values, color=colors)
        
        for i, v in enumerate(values):
            plt.text(i, v + 0.5, str(v), ha='center')
        
        plt.title('Code Issues by Type', fontsize=16)
        plt.ylabel('Number of Issues')
        plt.tight_layout()
        plt.savefig(output_dir / f"pylint_issues_{timestamp}.png", dpi=300)
        
        # Create module issues visualization (top 10)
        plt.figure(figsize=(12, 8))
        module_issues = pylint_data['module_issues']
        sorted_modules = sorted(module_issues.items(), key=lambda x: x[1], reverse=True)[:10]
        
        module_names = [item[0] for item in sorted_modules]
        issue_counts = [item[1] for item in sorted_modules]
        
        # Shorten module names if too long
        shortened_names = [name[-25:] if len(name) > 25 else name for name in module_names]
        
        plt.barh(shortened_names, issue_counts, color=sns.color_palette("Reds_r", len(sorted_modules)))
        
        plt.title('Top 10 Modules with Issues', fontsize=16)
        plt.xlabel('Number of Issues')
        plt.tight_layout()
        plt.savefig(output_dir / f"pylint_modules_{timestamp}.png", dpi=300)
        
    # Process Bandit results
    if latest_bandit:
        bandit_data = parse_bandit_results(latest_bandit)
        summary_data['bandit'] = bandit_data
        
        if bandit_data['total_issues'] > 0:
            # Create severity visualization
            plt.figure(figsize=(10, 6))
            severity_counts = bandit_data['severity_counts']
            labels = list(severity_counts.keys())
            values = list(severity_counts.values())
            
            colors = {'HIGH': '#ff6b6b', 'MEDIUM': '#feca57', 'LOW': '#1dd1a1'}
            bar_colors = [colors.get(label, '#48dbfb') for label in labels]
            
            plt.bar(labels, values, color=bar_colors)
            
            for i, v in enumerate(values):
                plt.text(i, v + 0.1, str(v), ha='center')
            
            plt.title('Security Issues by Severity', fontsize=16)
            plt.ylabel('Number of Issues')
            plt.tight_layout()
            plt.savefig(output_dir / f"bandit_severity_{timestamp}.png", dpi=300)
    
    # Process Safety results  
    if latest_safety:
        safety_data = parse_safety_results(latest_safety)
        summary_data['safety'] = safety_data
        
        if safety_data['total_issues'] > 0:
            # Create vulnerability by package visualization
            plt.figure(figsize=(10, 6))
            package_counts = safety_data['package_counts']
            
            sorted_packages = sorted(package_counts.items(), key=lambda x: x[1], reverse=True)
            package_names = [item[0] for item in sorted_packages]
            vuln_counts = [item[1] for item in sorted_packages]
            
            plt.bar(package_names, vuln_counts, color=sns.color_palette("Reds_d", len(sorted_packages)))
            
            for i, v in enumerate(vuln_counts):
                plt.text(i, v + 0.1, str(v), ha='center')
            
            plt.title('Vulnerable Packages', fontsize=16)
            plt.ylabel('Number of Vulnerabilities')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plt.savefig(output_dir / f"safety_packages_{timestamp}.png", dpi=300)
    
    # Process djLint results
    if latest_djlint:
        djlint_data = parse_djlint_results(latest_djlint)
        summary_data['djlint'] = djlint_data
        
        if djlint_data['total_issues'] > 0:
            # Create issues by file visualization
            plt.figure(figsize=(12, 8))
            file_counts = djlint_data['file_counts']
            
            sorted_files = sorted(file_counts.items(), key=lambda x: x[1], reverse=True)
            file_names = [item[0] for item in sorted_files]
            issue_counts = [item[1] for item in sorted_files]
            
            # Shorten file names if too long
            shortened_names = [name[-30:] if len(name) > 30 else name for name in file_names]
            
            plt.barh(shortened_names, issue_counts, color=sns.color_palette("Blues_d", len(sorted_files)))
            
            plt.title('Template Issues by File', fontsize=16)
            plt.xlabel('Number of Issues')
            plt.tight_layout()
            plt.savefig(output_dir / f"djlint_files_{timestamp}.png", dpi=300)
    
    # Generate an enhanced HTML report with the visualizations
    generate_enhanced_report(results_dir, output_dir, summary_data, timestamp)
    
    print(f"Visualizations and enhanced report generated in {output_dir}")
    return output_dir

def generate_enhanced_report(results_dir, output_dir, summary_data, timestamp):
    """Generate an enhanced HTML report with visualizations"""
    report_path = output_dir / f"enhanced_compliance_report_{timestamp}.html"
    
    # Get paths to visualization files
    pylint_score_img = f"pylint_score_{timestamp}.png"
    pylint_issues_img = f"pylint_issues_{timestamp}.png"
    pylint_modules_img = f"pylint_modules_{timestamp}.png"
    bandit_severity_img = f"bandit_severity_{timestamp}.png"
    safety_packages_img = f"safety_packages_{timestamp}.png"
    djlint_files_img = f"djlint_files_{timestamp}.png"
    
    # Create summary tables
    pylint_summary = ""
    if 'pylint' in summary_data:
        pylint_data = summary_data['pylint']
        score = pylint_data['score']
        issue_types = pylint_data['issue_types']
        total_issues = sum(issue_types.values())
        
        pylint_summary = f"""
        <div class="row">
            <div class="col-md-6">
                <div class="card mb-4">
                    <div class="card-header">
                        <h5 class="mb-0">Code Quality Score</h5>
                    </div>
                    <div class="card-body text-center">
                        <div class="score-display {get_score_class(score)}">
                            <div class="score-value">{score}/10</div>
                        </div>
                        <p class="mt-3">{get_score_description(score)}</p>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card mb-4">
                    <div class="card-header">
                        <h5 class="mb-0">Issue Breakdown</h5>
                    </div>
                    <div class="card-body">
                        <table class="table table-sm">
                            <thead>
                                <tr>
                                    <th>Issue Type</th>
                                    <th>Count</th>
                                    <th>Percentage</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr class="table-danger">
                                    <td>Errors (E)</td>
                                    <td>{issue_types.get('error', 0)}</td>
                                    <td>{get_percentage(issue_types.get('error', 0), total_issues)}</td>
                                </tr>
                                <tr class="table-warning">
                                    <td>Warnings (W)</td>
                                    <td>{issue_types.get('warning', 0)}</td>
                                    <td>{get_percentage(issue_types.get('warning', 0), total_issues)}</td>
                                </tr>
                                <tr class="table-info">
                                    <td>Convention (C)</td>
                                    <td>{issue_types.get('convention', 0)}</td>
                                    <td>{get_percentage(issue_types.get('convention', 0), total_issues)}</td>
                                </tr>
                                <tr class="table-primary">
                                    <td>Refactor (R)</td>
                                    <td>{issue_types.get('refactor', 0)}</td>
                                    <td>{get_percentage(issue_types.get('refactor', 0), total_issues)}</td>
                                </tr>
                                <tr class="table-secondary">
                                    <td>Fatal (F)</td>
                                    <td>{issue_types.get('fatal', 0)}</td>
                                    <td>{get_percentage(issue_types.get('fatal', 0), total_issues)}</td>
                                </tr>
                                <tr class="font-weight-bold">
                                    <td>Total</td>
                                    <td>{total_issues}</td>
                                    <td>100%</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
        <div class="row">
            <div class="col-md-12">
                <div class="card mb-4">
                    <div class="card-header">
                        <h5 class="mb-0">Code Quality Analysis</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                <img src="{pylint_issues_img}" class="img-fluid mb-3" alt="Code Issues by Type">
                            </div>
                            <div class="col-md-6">
                                <img src="{pylint_modules_img}" class="img-fluid mb-3" alt="Top Modules with Issues">
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """
    
    bandit_summary = ""
    if 'bandit' in summary_data:
        bandit_data = summary_data['bandit']
        total_issues = bandit_data['total_issues']
        severity_counts = bandit_data['severity_counts']
        
        if total_issues > 0:
            bandit_summary = f"""
            <div class="row">
                <div class="col-md-12">
                    <div class="card mb-4">
                        <div class="card-header">
                            <h5 class="mb-0">Security Analysis</h5>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <h6>Security Issues by Severity</h6>
                                    <table class="table table-sm">
                                        <thead>
                                            <tr>
                                                <th>Severity</th>
                                                <th>Count</th>
                                                <th>Percentage</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            <tr class="table-danger">
                                                <td>High</td>
                                                <td>{severity_counts.get('HIGH', 0)}</td>
                                                <td>{get_percentage(severity_counts.get('HIGH', 0), total_issues)}</td>
                                            </tr>
                                            <tr class="table-warning">
                                                <td>Medium</td>
                                                <td>{severity_counts.get('MEDIUM', 0)}</td>
                                                <td>{get_percentage(severity_counts.get('MEDIUM', 0), total_issues)}</td>
                                            </tr>
                                            <tr class="table-info">
                                                <td>Low</td>
                                                <td>{severity_counts.get('LOW', 0)}</td>
                                                <td>{get_percentage(severity_counts.get('LOW', 0), total_issues)}</td>
                                            </tr>
                                            <tr class="font-weight-bold">
                                                <td>Total</td>
                                                <td>{total_issues}</td>
                                                <td>100%</td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                                <div class="col-md-6">
                                    <img src="{bandit_severity_img}" class="img-fluid" alt="Security Issues by Severity">
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            """
        else:
            bandit_summary = """
            <div class="row">
                <div class="col-md-12">
                    <div class="card mb-4">
                        <div class="card-header">
                            <h5 class="mb-0">Security Analysis</h5>
                        </div>
                        <div class="card-body">
                            <div class="alert alert-success">
                                <i class="fas fa-check-circle"></i> No security issues detected by Bandit.
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            """
    
    djlint_summary = ""
    if 'djlint' in summary_data:
        djlint_data = summary_data['djlint']
        total_issues = djlint_data['total_issues']
        
        if total_issues > 0:
            djlint_summary = f"""
            <div class="row">
                <div class="col-md-12">
                    <div class="card mb-4">
                        <div class="card-header">
                            <h5 class="mb-0">Template Validation</h5>
                        </div>
                        <div class="card-body">
                            <p>Found {total_issues} template issues across {len(djlint_data['file_counts'])} files.</p>
                            <img src="{djlint_files_img}" class="img-fluid" alt="Template Issues by File">
                        </div>
                    </div>
                </div>
            </div>
            """
        else:
            djlint_summary = """
            <div class="row">
                <div class="col-md-12">
                    <div class="card mb-4">
                        <div class="card-header">
                            <h5 class="mb-0">Template Validation</h5>
                        </div>
                        <div class="card-body">
                            <div class="alert alert-success">
                                <i class="fas fa-check-circle"></i> No template issues detected by djLint.
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            """
    
    safety_summary = ""
    if 'safety' in summary_data:
        safety_data = summary_data['safety']
        total_issues = safety_data['total_issues']
        
        if total_issues > 0:
            severity_counts = safety_data['severity_counts']
            safety_summary = f"""
            <div class="row">
                <div class="col-md-12">
                    <div class="card mb-4">
                        <div class="card-header">
                            <h5 class="mb-0">Dependency Security</h5>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <h6>Vulnerabilities by Severity</h6>
                                    <table class="table table-sm">
                                        <thead>
                                            <tr>
                                                <th>Severity</th>
                                                <th>Count</th>
                                                <th>Percentage</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            <tr class="table-danger">
                                                <td>High</td>
                                                <td>{severity_counts.get('high', 0)}</td>
                                                <td>{get_percentage(severity_counts.get('high', 0), total_issues)}</td>
                                            </tr>
                                            <tr class="table-warning">
                                                <td>Medium</td>
                                                <td>{severity_counts.get('medium', 0)}</td>
                                                <td>{get_percentage(severity_counts.get('medium', 0), total_issues)}</td>
                                            </tr>
                                            <tr class="table-info">
                                                <td>Low</td>
                                                <td>{severity_counts.get('low', 0)}</td>
                                                <td>{get_percentage(severity_counts.get('low', 0), total_issues)}</td>
                                            </tr>
                                            <tr class="font-weight-bold">
                                                <td>Total</td>
                                                <td>{total_issues}</td>
                                                <td>100%</td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                                <div class="col-md-6">
                                    <img src="{safety_packages_img}" class="img-fluid" alt="Vulnerable Packages">
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            """
        else:
            safety_summary = """
            <div class="row">
                <div class="col-md-12">
                    <div class="card mb-4">
                        <div class="card-header">
                            <h5 class="mb-0">Dependency Security</h5>
                        </div>
                        <div class="card-body">
                            <div class="alert alert-success">
                                <i class="fas fa-check-circle"></i> No vulnerable dependencies detected by Safety.
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            """
    
    # Create recommendations based on data
    recommendations = generate_recommendations(summary_data)
    
    # Create the HTML report
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Enhanced Compliance Report - West Point Master Tracker</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                background-color: #f8f9fa;
            }}
            .header-section {{
                background-color: #00274c;
                color: white;
                padding: 20px 0;
                margin-bottom: 30px;
            }}
            .dashboard-summary {{
                margin-bottom: 30px;
            }}
            .score-display {{
                width: 150px;
                height: 150px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto;
            }}
            .score-value {{
                font-size: 2.5rem;
                font-weight: bold;
            }}
            .score-poor {{
                background-color: #ff6b6b;
                color: white;
            }}
            .score-fair {{
                background-color: #feca57;
                color: black;
            }}
            .score-good {{
                background-color: #1dd1a1;
                color: white;
            }}
            .priority-high {{
                border-left: 5px solid #ff6b6b;
            }}
            .priority-medium {{
                border-left: 5px solid #feca57;
            }}
            .priority-low {{
                border-left: 5px solid #1dd1a1;
            }}
            .img-fluid {{
                max-width: 100%;
                height: auto;
            }}
        </style>
    </head>
    <body>
        <div class="header-section">
            <div class="container">
                <div class="row">
                    <div class="col-md-8">
                        <h1>West Point Master Tracker</h1>
                        <h3>Enhanced Compliance Report</h3>
                    </div>
                    <div class="col-md-4 text-end">
                        <p class="mb-0">Generated on:</p>
                        <p class="lead">{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                    </div>
                </div>
            </div>
        </div>

        <div class="container">
            <div class="dashboard-summary">
                <div class="row">
                    <div class="col-md-12 mb-4">
                        <div class="alert alert-primary" role="alert">
                            <h4 class="alert-heading"><i class="fas fa-info-circle"></i> Summary</h4>
                            <p>This enhanced report provides detailed analysis of code quality, security, and dependency issues in the West Point Master Tracker application.</p>
                        </div>
                    </div>
                </div>
                
                {create_summary_cards(summary_data)}
            </div>

            <div class="detailed-analysis">
                <h2 class="mb-4">Code Quality Analysis</h2>
                {pylint_summary}
                
                <h2 class="mb-4">Security Analysis</h2>
                {bandit_summary}
                
                <h2 class="mb-4">Template Validation</h2>
                {djlint_summary}
                
                <h2 class="mb-4">Dependency Security</h2>
                {safety_summary}
                
                <h2 class="mb-4">Recommendations</h2>
                <div class="row">
                    <div class="col-md-12">
                        <div class="card mb-4">
                            <div class="card-header">
                                <h5 class="mb-0">Prioritized Action Items</h5>
                            </div>
                            <div class="card-body">
                                {recommendations}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <footer class="mt-5 mb-3 text-center text-muted">
                <p>West Point Master Tracker - Compliance Testing Report</p>
                <p><small>Generated with the Enhanced Compliance Visualization Tool</small></p>
            </footer>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    
    with open(report_path, 'w') as f:
        f.write(html_content)
    
    return report_path

def get_score_class(score):
    """Return CSS class based on score value"""
    if score < 3:
        return "score-poor"
    elif score < 7:
        return "score-fair"
    else:
        return "score-good"

def get_score_description(score):
    """Return description based on score value"""
    if score < 3:
        return "Poor code quality. Requires immediate attention."
    elif score < 7:
        return "Fair code quality. Improvements recommended."
    else:
        return "Good code quality. Continue maintaining standards."

def get_percentage(part, total):
    """Calculate and format percentage"""
    if total == 0:
        return "0%"
    return f"{(part / total) * 100:.1f}%"

def create_summary_cards(summary_data):
    """Create summary cards for the dashboard"""
    pylint_issues = sum(summary_data.get('pylint', {}).get('issue_types', {}).values()) if 'pylint' in summary_data else 0
    bandit_issues = summary_data.get('bandit', {}).get('total_issues', 0) if 'bandit' in summary_data else 0
    djlint_issues = summary_data.get('djlint', {}).get('total_issues', 0) if 'djlint' in summary_data else 0
    safety_issues = summary_data.get('safety', {}).get('total_issues', 0) if 'safety' in summary_data else 0
    
    pylint_score = summary_data.get('pylint', {}).get('score', 0) if 'pylint' in summary_data else 0
    score_class = get_score_class(pylint_score)
    
    return f"""
    <div class="row">
        <div class="col-md-3">
            <div class="card mb-4 text-center">
                <div class="card-header bg-primary text-white">
                    <h5 class="mb-0">Code Quality</h5>
                </div>
                <div class="card-body">
                    <div class="score-display {score_class}">
                        <div class="score-value">{pylint_score}/10</div>
                    </div>
                    <p class="mt-2">{get_score_description(pylint_score)}</p>
                </div>
                <div class="card-footer">
                    <span class="text-muted">{pylint_issues} issues found</span>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card mb-4 text-center">
                <div class="card-header bg-danger text-white">
                    <h5 class="mb-0">Security Issues</h5>
                </div>
                <div class="card-body">
                    <h1 class="display-4">{bandit_issues}</h1>
                    <p>potential vulnerabilities</p>
                </div>
                <div class="card-footer">
                    <span class="text-muted">From Bandit analysis</span>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card mb-4 text-center">
                <div class="card-header bg-warning text-dark">
                    <h5 class="mb-0">Template Issues</h5>
                </div>
                <div class="card-body">
                    <h1 class="display-4">{djlint_issues}</h1>
                    <p>template problems</p>
                </div>
                <div class="card-footer">
                    <span class="text-muted">From djLint analysis</span>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card mb-4 text-center">
                <div class="card-header bg-info text-dark">
                    <h5 class="mb-0">Vulnerable Deps</h5>
                </div>
                <div class="card-body">
                    <h1 class="display-4">{safety_issues}</h1>
                    <p>dependency issues</p>
                </div>
                <div class="card-footer">
                    <span class="text-muted">From Safety analysis</span>
                </div>
            </div>
        </div>
    </div>
    """

def generate_recommendations(summary_data):
    """Generate recommendations based on data"""
    recommendations = []
    
    # Check for high severity security issues
    if 'bandit' in summary_data and summary_data['bandit'].get('severity_counts', {}).get('HIGH', 0) > 0:
        recommendations.append({
            'priority': 'high',
            'title': 'Fix High Severity Security Issues',
            'description': 'Address all high severity security vulnerabilities identified by Bandit.'
        })
    
    # Check for high severity dependency issues
    if 'safety' in summary_data and summary_data['safety'].get('severity_counts', {}).get('high', 0) > 0:
        recommendations.append({
            'priority': 'high',
            'title': 'Update Vulnerable Dependencies',
            'description': 'Update dependencies with high severity vulnerabilities to secure versions.'
        })
    
    # Check for pylint errors
    if 'pylint' in summary_data and summary_data['pylint'].get('issue_types', {}).get('error', 0) > 0:
        recommendations.append({
            'priority': 'high',
            'title': 'Fix Code Errors',
            'description': f"Address {summary_data['pylint'].get('issue_types', {}).get('error', 0)} code errors identified by Pylint."
        })
    
    # Check for medium severity issues
    if 'bandit' in summary_data and summary_data['bandit'].get('severity_counts', {}).get('MEDIUM', 0) > 0:
        recommendations.append({
            'priority': 'medium',
            'title': 'Address Medium Severity Security Issues',
            'description': 'Review and fix medium severity security issues to improve overall security posture.'
        })
    
    # Check for pylint warnings
    if 'pylint' in summary_data and summary_data['pylint'].get('issue_types', {}).get('warning', 0) > 0:
        recommendations.append({
            'priority': 'medium',
            'title': 'Address Code Warnings',
            'description': f"Fix {summary_data['pylint'].get('issue_types', {}).get('warning', 0)} warning issues to improve code quality."
        })
    
    # Check for template issues
    if 'djlint' in summary_data and summary_data['djlint'].get('total_issues', 0) > 0:
        recommendations.append({
            'priority': 'medium',
            'title': 'Fix Template Issues',
            'description': f"Address {summary_data['djlint'].get('total_issues', 0)} template issues to ensure proper rendering and accessibility."
        })
    
    # Check for style/convention issues
    if 'pylint' in summary_data:
        convention_issues = summary_data['pylint'].get('issue_types', {}).get('convention', 0)
        refactor_issues = summary_data['pylint'].get('issue_types', {}).get('refactor', 0)
        if convention_issues > 0 or refactor_issues > 0:
            recommendations.append({
                'priority': 'low',
                'title': 'Improve Code Style',
                'description': f"Address {convention_issues + refactor_issues} style and convention issues to improve code consistency and readability."
            })
    
    # If no specific recommendations, add general ones
    if not recommendations:
        recommendations.append({
            'priority': 'low',
            'title': 'Maintain Code Quality',
            'description': 'Continue to maintain high code quality standards through regular testing and reviews.'
        })
    
    # Format recommendations as HTML
    html_recommendations = ""
    for rec in recommendations:
        html_recommendations += f"""
        <div class="card mb-3 priority-{rec['priority']}">
            <div class="card-body">
                <h5 class="card-title">
                    <span class="badge bg-{'danger' if rec['priority'] == 'high' else 'warning' if rec['priority'] == 'medium' else 'success'}">
                        {rec['priority'].upper()}
                    </span>
                    {rec['title']}
                </h5>
                <p class="card-text">{rec['description']}</p>
            </div>
        </div>
        """
    
    return html_recommendations

if __name__ == "__main__":
    # Get results directory from command line or use default
    import sys
    results_dir = sys.argv[1] if len(sys.argv) > 1 else "compliance_results"
    output_dir = generate_visualizations(results_dir)
    
    # Open the report in the browser if possible
    import webbrowser
    report_path = max(Path(output_dir).glob("enhanced_compliance_report_*.html"), key=os.path.getctime)
    webbrowser.open(f"file://{os.path.abspath(report_path)}")