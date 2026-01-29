import json

def generate_report(results, output_file='audit_summary.json'):
    """
    Takes the dictionary from the auditor and saves it as a JSON file.
    """
    try:
        with open(output_file, 'w') as f:
            # indent=4 makes the JSON look 'pretty' and readable
            json.dump(results, f, indent=4)
        print(f"Successfully saved report to {output_file}")
    except Exception as e:
        print(f"Error saving report: {e}")