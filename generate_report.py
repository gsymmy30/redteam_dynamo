#!/usr/bin/env python3
"""
Generate detailed analysis report from test results
Supports both console output and markdown export
"""

import json
import sys
from collections import defaultdict
from pathlib import Path
from datetime import datetime

def load_latest_results(results_dir='results'):
    """Load the most recent results file"""
    results_path = Path(results_dir)
    
    if not results_path.exists():
        print(f"❌ Results directory '{results_dir}' not found")
        return None
    
    result_files = sorted(results_path.glob('results_*.json'), reverse=True)
    
    if not result_files:
        print(f"❌ No results files found in '{results_dir}'")
        return None
    
    latest_file = result_files[0]
    print(f"📂 Loading results from: {latest_file}\n")
    
    with open(latest_file, 'r') as f:
        return json.load(f)

def generate_markdown_report(results_data, output_file='report.md'):
    """Generate markdown version of the report"""
    
    if not results_data:
        return
    
    metadata = results_data.get('metadata', {})
    results = results_data.get('results', [])
    
    if not results:
        return
    
    md_lines = []
    
    # Header
    md_lines.append("# Financial Advice Guardrail Red-Team Report")
    md_lines.append("")
    md_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if metadata:
        md_lines.append(f"**Test Run:** {metadata.get('timestamp', 'Unknown')}")
        config = metadata.get('config', {})
        md_lines.append(f"**Model ID:** {config.get('model_id', 'Unknown')}")
        md_lines.append(f"**Total Tests:** {metadata.get('total_tests', len(results))}")
    
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")
    
    # Overall stats
    total = len(results)
    passed = sum(1 for r in results if r.get('result') == 'PASS')
    failed = sum(1 for r in results if r.get('result') == 'FAIL')
    errors = sum(1 for r in results if r.get('result') == 'ERROR')
    
    # Separate failures
    all_failures = [r for r in results if r.get('result') == 'FAIL']
    confirmed_bypasses = [
        r for r in all_failures 
        if r.get('expected_block', True) 
        and 'timeout' not in r.get('final_action', '').lower()
        and r.get('full_api_response') is not None
    ]
    timeout_bypasses = [
        r for r in all_failures 
        if r.get('expected_block', True)
        and 'timeout' in r.get('final_action', '').lower()
    ]
    false_positives = [
        r for r in all_failures 
        if not r.get('expected_block', False)
    ]
    
    md_lines.append("## 📊 Overall Metrics")
    md_lines.append("")
    md_lines.append(f"- **Total Tests:** {total}")
    md_lines.append(f"- **✅ Passed:** {passed} ({passed/total*100:.1f}%)")
    md_lines.append(f"- **❌ Failed:** {failed} ({failed/total*100:.1f}%)")
    if errors > 0:
        md_lines.append(f"- **⚠️ Errors:** {errors}")
    md_lines.append("")
    md_lines.append("### Failure Breakdown")
    md_lines.append("")
    md_lines.append(f"- **🚨 Confirmed Bypasses:** {len(confirmed_bypasses)}")
    md_lines.append(f"- **⏱️ Timeout Bypasses:** {len(timeout_bypasses)}")
    md_lines.append(f"- **❌ False Positives:** {len(false_positives)}")
    md_lines.append("")
    
    # By category
    md_lines.append("## 🎯 Results by Attack Category")
    md_lines.append("")
    
    category_stats = defaultdict(lambda: {'total': 0, 'pass': 0, 'fail': 0})
    for r in results:
        cat = r.get('category', 'unknown')
        category_stats[cat]['total'] += 1
        if r.get('result') == 'PASS':
            category_stats[cat]['pass'] += 1
        elif r.get('result') == 'FAIL':
            category_stats[cat]['fail'] += 1
    
    sorted_cats = sorted(category_stats.items(), key=lambda x: x[1]['fail'], reverse=True)
    
    md_lines.append("| Category | Total | Pass | Fail | Fail Rate |")
    md_lines.append("|----------|-------|------|------|-----------|")
    for cat, stats in sorted_cats:
        fail_rate = stats['fail'] / stats['total'] * 100 if stats['total'] > 0 else 0
        status = "🚨" if fail_rate > 20 else "⚠️" if fail_rate > 10 else "✅"
        md_lines.append(f"| {status} {cat} | {stats['total']} | {stats['pass']} | {stats['fail']} | {fail_rate:.1f}% |")
    
    md_lines.append("")
    
    # By tactic
    md_lines.append("## 🔧 Results by Attack Tactic")
    md_lines.append("")
    
    tactic_stats = defaultdict(lambda: {'total': 0, 'pass': 0, 'fail': 0})
    for r in results:
        if r.get('expected_block', True):
            tactic = r.get('tactic', 'unknown')
            tactic_stats[tactic]['total'] += 1
            if r.get('result') == 'PASS':
                tactic_stats[tactic]['pass'] += 1
            elif r.get('result') == 'FAIL':
                tactic_stats[tactic]['fail'] += 1
    
    sorted_tactics = sorted(tactic_stats.items(), key=lambda x: x[1]['fail'], reverse=True)
    
    md_lines.append("| Tactic | Bypasses | Total | Bypass Rate |")
    md_lines.append("|--------|----------|-------|-------------|")
    for tactic, stats in sorted_tactics:
        if stats['total'] > 0:
            fail_rate = stats['fail'] / stats['total'] * 100
            status = "🚨" if fail_rate > 50 else "⚠️" if fail_rate > 20 else "✅"
            md_lines.append(f"| {status} {tactic} | {stats['fail']} | {stats['total']} | {fail_rate:.1f}% |")
    
    md_lines.append("")
    
    # Confirmed bypasses
    if confirmed_bypasses:
        md_lines.append("## 🚨 Confirmed Bypasses")
        md_lines.append("")
        md_lines.append("Attacks that successfully bypassed guardrails:")
        md_lines.append("")
        
        for i, fail in enumerate(confirmed_bypasses, 1):
            md_lines.append(f"### {i}. {fail.get('id', 'unknown')} - {fail.get('category', 'unknown')}/{fail.get('subcategory', 'unknown')}")
            md_lines.append("")
            md_lines.append(f"- **Tactic:** {fail.get('tactic', 'N/A')}")
            md_lines.append(f"- **Prompt:** `{fail.get('prompt', '')}`")
            md_lines.append(f"- **Expected:** BLOCK")
            md_lines.append(f"- **Actual:** {fail.get('final_action', 'NONE')}")
            md_lines.append(f"- **Guard Score:** {fail.get('max_guard_score', 0):.4f}")
            md_lines.append("")
            
            # Model response
            if fail.get('full_api_response'):
                api_response = fail['full_api_response']
                chat_response = api_response.get('chat', {}).get('response', '')
                
                if chat_response:
                    md_lines.append("**Model Response:**")
                    md_lines.append("")
                    md_lines.append("```")
                    # Limit to 1000 chars in markdown
                    if len(chat_response) > 1000:
                        md_lines.append(chat_response[:1000])
                        md_lines.append("...")
                        md_lines.append("(truncated - see full results file)")
                    else:
                        md_lines.append(chat_response)
                    md_lines.append("```")
                    md_lines.append("")
    
    # Timeout bypasses
    if timeout_bypasses:
        md_lines.append("## ⏱️ Likely Bypasses (API Timeouts)")
        md_lines.append("")
        md_lines.append("These timed out while generating responses (indicating guardrail didn't block):")
        md_lines.append("")
        
        for fail in timeout_bypasses:
            md_lines.append(f"- **{fail.get('id', 'unknown')}** ({fail.get('category', 'unknown')}/{fail.get('subcategory', 'unknown')})")
            md_lines.append(f"  - Tactic: {fail.get('tactic', 'N/A')}")
            md_lines.append(f"  - Prompt: `{fail.get('prompt', '')[:100]}...`")
        
        md_lines.append("")
    
    # False positives
    if false_positives:
        md_lines.append("## ❌ False Positives")
        md_lines.append("")
        md_lines.append("Benign queries that were incorrectly blocked:")
        md_lines.append("")
        
        for fp in false_positives:
            md_lines.append(f"- **{fp.get('id', 'unknown')}:** `{fp.get('prompt', '')}`")
            if fp.get('violated_policies'):
                md_lines.append(f"  - Blocked by: {', '.join(fp['violated_policies'])}")
        
        md_lines.append("")
    
    # Write to file
    with open(output_file, 'w') as f:
        f.write('\n'.join(md_lines))
    
    return output_file

def generate_report(results_data):
    """Generate comprehensive report"""
    
    if not results_data:
        return
    
    metadata = results_data.get('metadata', {})
    results = results_data.get('results', [])
    
    if not results:
        print("❌ No test results found in file")
        return
    
    # Overall stats
    total = len(results)
    passed = sum(1 for r in results if r.get('result') == 'PASS')
    failed = sum(1 for r in results if r.get('result') == 'FAIL')
    errors = sum(1 for r in results if r.get('result') == 'ERROR')
    
    # Separate failures by type
    all_failures = [r for r in results if r.get('result') == 'FAIL']
    
    # Confirmed bypasses (got full response showing it wasn't blocked)
    confirmed_bypasses = [
        r for r in all_failures 
        if r.get('expected_block', True) 
        and 'timeout' not in r.get('final_action', '').lower()
        and r.get('full_api_response') is not None
    ]
    
    # Likely bypasses (API timed out while generating response)
    timeout_bypasses = [
        r for r in all_failures 
        if r.get('expected_block', True)
        and 'timeout' in r.get('final_action', '').lower()
    ]
    
    # False positives (benign queries incorrectly blocked)
    false_positives = [
        r for r in all_failures 
        if not r.get('expected_block', False)
    ]
    
    # Print report header
    print("=" * 80)
    print("FINANCIAL ADVICE GUARDRAIL RED-TEAM REPORT")
    print("=" * 80)
    
    if metadata:
        print(f"\n📅 Test Run: {metadata.get('timestamp', 'Unknown')}")
        config = metadata.get('config', {})
        print(f"🔧 Model ID: {config.get('model_id', 'Unknown')}")
        print(f"📝 Total Tests: {metadata.get('total_tests', total)}")
    
    print(f"\n{'='*80}")
    print("📊 OVERALL METRICS")
    print(f"{'='*80}")
    print(f"  Total Tests:        {total}")
    print(f"  ✅ Passed:          {passed} ({passed/total*100:.1f}%)")
    print(f"  ❌ Failed:          {failed} ({failed/total*100:.1f}%)")
    if errors > 0:
        print(f"  ⚠️  Errors:          {errors}")
    
    print(f"\n  Failure Breakdown:")
    print(f"    🚨 Confirmed Bypasses:  {len(confirmed_bypasses)}")
    print(f"    ⏱️  Timeout Bypasses:    {len(timeout_bypasses)}")
    print(f"    ❌ False Positives:     {len(false_positives)}")
    
    # By category
    print(f"\n{'='*80}")
    print("🎯 RESULTS BY ATTACK CATEGORY")
    print(f"{'='*80}")
    
    category_stats = defaultdict(lambda: {'total': 0, 'pass': 0, 'fail': 0})
    for r in results:
        cat = r.get('category', 'unknown')
        category_stats[cat]['total'] += 1
        if r.get('result') == 'PASS':
            category_stats[cat]['pass'] += 1
        elif r.get('result') == 'FAIL':
            category_stats[cat]['fail'] += 1
    
    sorted_cats = sorted(category_stats.items(), key=lambda x: x[1]['fail'], reverse=True)
    
    for cat, stats in sorted_cats:
        fail_rate = stats['fail'] / stats['total'] * 100 if stats['total'] > 0 else 0
        status = "🚨" if fail_rate > 20 else "⚠️" if fail_rate > 10 else "✅"
        
        print(f"\n  {status} {cat}")
        print(f"      Total: {stats['total']}, Pass: {stats['pass']}, "
              f"Fail: {stats['fail']}, Fail Rate: {fail_rate:.1f}%")
    
    # By tactic
    print(f"\n{'='*80}")
    print("🔧 RESULTS BY ATTACK TACTIC")
    print(f"{'='*80}")
    
    tactic_stats = defaultdict(lambda: {'total': 0, 'pass': 0, 'fail': 0})
    for r in results:
        if r.get('expected_block', True):  # Only count attack tactics
            tactic = r.get('tactic', 'unknown')
            tactic_stats[tactic]['total'] += 1
            if r.get('result') == 'PASS':
                tactic_stats[tactic]['pass'] += 1
            elif r.get('result') == 'FAIL':
                tactic_stats[tactic]['fail'] += 1
    
    sorted_tactics = sorted(tactic_stats.items(), 
                           key=lambda x: x[1]['fail'], reverse=True)
    
    for tactic, stats in sorted_tactics:
        if stats['total'] > 0:
            fail_rate = stats['fail'] / stats['total'] * 100
            status = "🚨" if fail_rate > 50 else "⚠️" if fail_rate > 20 else "✅"
            print(f"  {status} {tactic:35s}: {stats['fail']:2d}/{stats['total']:2d} bypasses ({fail_rate:5.1f}%)")
    
    # Show confirmed bypasses
    if confirmed_bypasses:
        print(f"\n{'='*80}")
        print(f"🚨 CONFIRMED BYPASSES ({len(confirmed_bypasses)})")
        print(f"{'='*80}")
        print("  Attacks that successfully bypassed guardrails:\n")
        
        for i, fail in enumerate(confirmed_bypasses, 1):
            print(f"  [{i}] {fail.get('id', 'unknown')} - {fail.get('category', 'unknown')}/{fail.get('subcategory', 'unknown')}")
            print(f"      Tactic:     {fail.get('tactic', 'N/A')}")
            print(f"      Prompt:     {fail.get('prompt', '')[:70]}{'...' if len(fail.get('prompt', '')) > 70 else ''}")
            print(f"      Action:     Expected BLOCK, Got {fail.get('final_action', 'NONE')}")
            print(f"      Score:      {fail.get('max_guard_score', 0):.4f}")
            
            # Show ONLY the model's chat response
            if fail.get('full_api_response'):
                api_response = fail['full_api_response']
                chat_response = api_response.get('chat', {}).get('response', '')
                
                if chat_response:
                    print(f"      Model Response:")
                    # Show first 500 chars
                    if len(chat_response) > 500:
                        print(f"        {chat_response[:500]}...")
                        print(f"        (truncated - full response in results file)")
                    else:
                        # Indent each line for readability
                        for line in chat_response.split('\n')[:20]:  # Max 20 lines
                            print(f"        {line}")
                        if len(chat_response.split('\n')) > 20:
                            print(f"        (truncated - full response in results file)")
            print()
    
    # Show timeout bypasses
    if timeout_bypasses:
        print(f"{'='*80}")
        print(f"⏱️  LIKELY BYPASSES - API TIMEOUTS ({len(timeout_bypasses)})")
        print(f"{'='*80}")
        print("  These timed out while generating responses (indicating guardrail didn't block):\n")
        
        for i, fail in enumerate(timeout_bypasses, 1):
            print(f"  [{i}] {fail.get('id', 'unknown')} - {fail.get('category', 'unknown')}/{fail.get('subcategory', 'unknown')}")
            print(f"      Tactic:     {fail.get('tactic', 'N/A')}")
            print(f"      Prompt:     {fail.get('prompt', '')[:70]}{'...' if len(fail.get('prompt', '')) > 70 else ''}")
            print()
    
    # Show false positives
    if false_positives:
        print(f"{'='*80}")
        print(f"❌ FALSE POSITIVES ({len(false_positives)})")
        print(f"{'='*80}")
        print("  Benign queries that were incorrectly blocked:\n")
        
        for fp in false_positives:
            print(f"  • [{fp.get('id', 'unknown')}] {fp.get('prompt', '')[:60]}...")
            if fp.get('violated_policies'):
                print(f"    Blocked by: {', '.join(fp['violated_policies'])}")
            print()
    
    # Errors
    error_list = [r for r in results if r.get('result') == 'ERROR']
    if error_list:
        print(f"{'='*80}")
        print(f"⚠️  ERRORS ({len(error_list)})")
        print(f"{'='*80}")
        print("  Tests that encountered errors:\n")
        
        for err in error_list:
            print(f"  • [{err.get('id', 'unknown')}] {err.get('prompt', '')[:60]}...")
            print(f"    Notes: {err.get('notes', 'No notes')}")
            print()
    
    print(f"{'='*80}\n")

def main():
    """Main entry point"""
    
    # Parse arguments
    export_md = '--md' in sys.argv or '--markdown' in sys.argv
    
    # Remove flags from argv to get filename
    args = [arg for arg in sys.argv[1:] if not arg.startswith('--')]
    
    # Check if specific results file provided
    if len(args) > 0:
        results_file = args[0]
        print(f"📂 Loading results from: {results_file}\n")
        try:
            with open(results_file, 'r') as f:
                results_data = json.load(f)
        except FileNotFoundError:
            print(f"❌ File not found: {results_file}")
            return
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON in file: {results_file}")
            return
    else:
        # Load latest results
        results_data = load_latest_results()
    
    if results_data:
        # Generate console report
        generate_report(results_data)
        
        # Generate markdown if requested
        if export_md:
            # Get base name from results file
            if len(args) > 0:
                base_name = Path(args[0]).stem
            else:
                base_name = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            md_file = f"results/{base_name}.md"
            output_path = generate_markdown_report(results_data, md_file)
            print(f"\n📄 Markdown report saved to: {output_path}")
    else:
        print("\n❌ No results to analyze. Run 'python run_tests.py' first.")
        print("\nUsage:")
        print("  python generate_report.py                    # Latest results, console only")
        print("  python generate_report.py --md               # Latest results, console + markdown")
        print("  python generate_report.py results/file.json  # Specific file, console only")
        print("  python generate_report.py results/file.json --md  # Specific file, console + markdown")

if __name__ == "__main__":
    main()