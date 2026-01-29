import argparse
import vaultlens.auditor as auditor
import vaultlens.reporter as reporter
import vaultlens.analyzer as analyzer
import vaultlens.feedback as feedback

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='AI-Powered Data Auditor')
    parser.add_argument('--model', choices=['openai', 'ollama'], default='openai',
                        help='Choose AI provider: openai (needs API key) or ollama (local, free)')
    parser.add_argument('--file', default='test_data.csv',
                        help='Path to CSV file to audit')
    args = parser.parse_args()

    print(f"Using AI provider: {args.model}")
    print(f"Auditing file: {args.file}")

    print("\nStep 1: Auditing...") 
    results = auditor.run_audit(args.file)

    print("Step 2: Saving Report...")
    reporter.generate_report(results)

    print("Step 3: AI is Analyzing...")
    ai_summary = analyzer.analyze_audit_results('audit_summary.json', provider=args.model)
    
    print("\n" + "="*30)
    print("AI-Powered Analysis")
    print("="*30)
    print(ai_summary)
    print("="*30)

    feedback.send_feedback()

if __name__ == "__main__":
    main()