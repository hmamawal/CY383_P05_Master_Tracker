import os
import subprocess
import json
from datetime import datetime
import argparse

def run_command(command, output_file=None):
    """Run a command and return its output"""
    result = subprocess.run(command, capture_output=True, text=True)
    if output_file:
        with open(output_file, 'w') as f:
            f.write(result.stdout)
    return result.stdout, result.stderr

def main():
    # Create results directory
    results_dir = "compliance_results"
    os.makedirs(results_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Run Bandit security check
    print("Running Bandit security check...")
    bandit_output, _ = run_command(
        ["bandit", "-r", ".", "-f", "json", "-x", ".venv,*/migrations/*"],
        f"{results_dir}/bandit_results_{timestamp}.json"
    )
    
    # Run djLint on templates
    print("Running djLint template check...")
    djlint_output, _ = run_command(
        ["djlint", "--check", "templates", "content/templates", "accounts/templates"],
        f"{results_dir}/djlint_results_{timestamp}.txt"
    )
    
    # Run Pylint
    print("Running Pylint code quality check...")
    pylint_output, _ = run_command(
        ["pylint", "content", "accounts", "FitFrenzy"],
        f"{results_dir}/pylint_results_{timestamp}.txt"
    )
    
    # Run Safety check
    print("Running Safety dependency check...")
    safety_output, _ = run_command(
        ["safety", "check", "--json"],
        f"{results_dir}/safety_results_{timestamp}.json"
    )
    
    # Generate summary report
    generate_summary_report(results_dir, timestamp)
    
    print(f"All compliance tests completed. Results saved in {results_dir}")

def generate_summary_report(results_dir, timestamp):
    """Generate a summary HTML report of all test results"""
    report_path = f"{results_dir}/compliance_summary_{timestamp}.html"
    
    # Simple HTML template for the report
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Master Tracker Compliance Test Results</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2 {{ color: #333; }}
            .section {{ margin-bottom: 30px; }}
            .issue {{ margin-left: 20px; padding: 10px; border-left: 3px solid #f44336; }}
            .warning {{ background-color: #fff3cd; }}
            .error {{ background-color: #f8d7da; }}
            .summary {{ font-weight: bold; margin-top: 10px; }}
        </style>
    </head>
    <body>
        <h1>Master Tracker Compliance Test Results</h1>
        <p>Test run completed on: {timestamp}</p>
        
        <div class="section">
            <h2>Security Analysis (Bandit)</h2>
            {bandit_results}
        </div>
        
        <div class="section">
            <h2>Template Validation (djLint)</h2>
            {djlint_results}
        </div>
        
        <div class="section">
            <h2>Code Quality (Pylint)</h2>
            {pylint_results}
        </div>
        
        <div class="section">
            <h2>Dependency Security (Safety)</h2>
            {safety_results}
        </div>
        
        <div class="section">
            <h2>Recommendations</h2>
            <ol>
                <li>Address all high severity security issues first</li>
                <li>Fix template validation errors to ensure proper rendering</li>
                <li>Address code quality issues to improve maintainability</li>
                <li>Update dependencies with known vulnerabilities</li>
            </ol>
        </div>
    </body>
    </html>
    """
    
    # Process results for each test
    bandit_summary = process_bandit_results(f"{results_dir}/bandit_results_{timestamp}.json")
    djlint_summary = process_djlint_results(f"{results_dir}/djlint_results_{timestamp}.txt")
    pylint_summary = process_pylint_results(f"{results_dir}/pylint_results_{timestamp}.txt")
    safety_summary = process_safety_results(f"{results_dir}/safety_results_{timestamp}.json")
    
    # Fill in the template
    html_content = html_content.format(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        bandit_results=bandit_summary,
        djlint_results=djlint_summary,
        pylint_results=pylint_summary,
        safety_results=safety_summary
    )
    
    # Write the report
    with open(report_path, 'w') as f:
        f.write(html_content)
    
    print(f"Summary report generated: {report_path}")

def process_bandit_results(json_file):
    try:
        with open(json_file) as f:
            data = json.load(f)
            results = data.get('results', [])
            
            if not results:
                return "<p>No security issues found.</p>"
            
            html = f"<p class='summary'>Found {len(results)} potential security issues:</p><ul>"
            for issue in results:
                severity = issue.get('issue_severity', 'Unknown')
                confidence = issue.get('issue_confidence', 'Unknown')
                issue_text = issue.get('issue_text', 'Unknown issue')
                filename = issue.get('filename', 'Unknown file')
                line_number = issue.get('line_number', 0)
                
                html += f"""
                <li class="issue {'error' if severity == 'HIGH' else 'warning'}">
                    <strong>{severity} severity ({confidence} confidence)</strong><br>
                    {issue_text}<br>
                    Location: {filename}, line {line_number}
                </li>
                """
            html += "</ul>"
            return html
    except Exception as e:
        return f"<p>Error processing Bandit results: {str(e)}</p>"

# Similar processing functions for other tools
def process_djlint_results(txt_file):
    # Process djLint results
    try:
        with open(txt_file) as f:
            content = f.read()
            if "No errors found" in content:
                return "<p>No template issues found.</p>"
            
            lines = content.strip().split('\n')
            html = f"<p class='summary'>Found template issues:</p><ul>"
            for line in lines:
                if line.strip():
                    html += f"<li class='issue warning'>{line}</li>"
            html += "</ul>"
            return html
    except Exception as e:
        return f"<p>Error processing djLint results: {str(e)}</p>"

def process_pylint_results(txt_file):
    # Process Pylint results
    try:
        with open(txt_file) as f:
            content = f.read()
            if not content or "Your code has been rated at 10.00/10" in content:
                return "<p>No code quality issues found.</p>"
            
            # Extract final score
            score = "Unknown"
            for line in content.split('\n'):
                if "Your code has been rated at" in line:
                    score = line.strip()
                    break
            
            lines = content.strip().split('\n')
            html = f"<p class='summary'>Code quality issues found. {score}</p><ul>"
            for line in lines:
                if ":" in line and any(t in line for t in ["E:", "W:", "C:", "R:"]):
                    html += f"<li class='issue {'error' if 'E:' in line else 'warning'}'>{line}</li>"
            html += "</ul>"
            return html
    except Exception as e:
        return f"<p>Error processing Pylint results: {str(e)}</p>"

def process_safety_results(json_file):
    try:
        with open(json_file) as f:
            data = json.load(f)
            if not data:
                return "<p>No vulnerable dependencies found.</p>"
            
            html = f"<p class='summary'>Found {len(data)} vulnerable dependencies:</p><ul>"
            for issue in data:
                name = issue.get('name', 'Unknown')
                version = issue.get('installed', 'Unknown')
                vulnerability = issue.get('vulnerabilities', [{}])[0]
                severity = vulnerability.get('severity', 'Unknown')
                description = vulnerability.get('advisory', 'No description available')
                
                html += f"""
                <li class="issue {'error' if severity == 'high' else 'warning'}">
                    <strong>{name} ({version}) - {severity} severity</strong><br>
                    {description}
                </li>
                """
            html += "</ul>"
            return html
    except Exception as e:
        return f"<p>Error processing Safety results: {str(e)}</p>"


def test_report_generation():
    """Test the report generation with mock data to verify formatting works correctly"""
    print("Testing report generation with mock data...")
    
    # Create test directory
    test_dir = "test_compliance_results"
    os.makedirs(test_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create mock result files
    mock_bandit = {
        "results": [
            {
                "issue_severity": "HIGH",
                "issue_confidence": "MEDIUM",
                "issue_text": "Mock security issue",
                "filename": "mock_file.py",
                "line_number": 42
            }
        ]
    }
    
    with open(f"{test_dir}/bandit_results_{timestamp}.json", 'w') as f:
        json.dump(mock_bandit, f)
    
    with open(f"{test_dir}/djlint_results_{timestamp}.txt", 'w') as f:
        f.write("templates/base.html:10:10: H006 HTML attribute should be lowercase\n")
    
    with open(f"{test_dir}/pylint_results_{timestamp}.txt", 'w') as f:
        f.write("mock_file.py:25: E0001 Syntax error\nYour code has been rated at 7.50/10\n")
    
    mock_safety = [
        {
            "name": "django",
            "installed": "3.2.0",
            "vulnerabilities": [
                {
                    "severity": "high",
                    "advisory": "Mock vulnerability in Django"
                }
            ]
        }
    ]
    
    with open(f"{test_dir}/safety_results_{timestamp}.json", 'w') as f:
        json.dump(mock_safety, f)
    
    try:
        # Generate report using mock data
        generate_summary_report(test_dir, timestamp)
        print(f"Test successful! Report generated at {test_dir}/compliance_summary_{timestamp}.html")
        print("Open this file to verify the formatting is correct.")
    except Exception as e:
        print(f"Test failed with error: {str(e)}")
        # Show what line caused the error for easier debugging
        import traceback
        traceback.print_exc()

def generate_visualizations(results_dir, timestamp):
    """Generate visualizations for the compliance results"""
    try:
        # Import the visualization module
        from visualize_compliance import generate_visualizations
        print(f"Generating enhanced visualizations for compliance results...")
        output_dir = generate_visualizations(results_dir)
        print(f"Enhanced visualizations and report generated in {output_dir}")
        return True
    except ImportError:
        print("Visualization module not found. Run without enhanced visualizations.")
        return False
    except Exception as e:
        print(f"Error generating visualizations: {str(e)}")
        return False

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Run compliance tests on code')
    parser.add_argument('--test-only', action='store_true', help='Only test report generation with mock data')
    parser.add_argument('--visualize', action='store_true', help='Generate enhanced visualizations and report')
    args = parser.parse_args()
    
    if args.test_only:
        test_report_generation()
    else:
        main()
        if args.visualize:
            results_dir = "compliance_results"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            generate_visualizations(results_dir, timestamp)