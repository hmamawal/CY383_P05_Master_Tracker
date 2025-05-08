#!/usr/bin/env python3
"""
Generate enhanced visualizations from existing compliance test results.
"""

import argparse
from visualize_compliance import generate_visualizations

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate enhanced visualizations from compliance test results")
    parser.add_argument("--results-dir", default="compliance_results", 
                        help="Directory containing compliance test results (default: compliance_results)")
    args = parser.parse_args()
    
    output_dir = generate_visualizations(args.results_dir)
    print(f"Enhanced visualizations and report generated in {output_dir}")