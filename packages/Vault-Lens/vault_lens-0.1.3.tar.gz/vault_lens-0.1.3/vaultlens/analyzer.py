import os
import json
import requests # for Ollama

from openai import OpenAI
from dotenv import load_dotenv

# Load the API key from your .env file
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_prompt(audit_data):
    summarized_data = {}
    for col, info in audit_data.items():
        summarized_data[col] = {
            'dtype': info['dtype'],
            'nulls': info['nulls'],
            'null_row_indices': info['null_row_indices'][:10] if info['nulls'] > 10 else info['null_row_indices'],
            'flagged_inconsistency': info['flagged_inconsistency'],
            'inconsistent_row_indices': info['inconsistent_row_indices'][:10] if len(info['inconsistent_row_indices']) > 10 else info['inconsistent_row_indices'],
            'date_issue': info['date_issue'],
            'is_categorical': info['is_categorical']
        }


    # 2. Create the prompt for the AI
    prompt = f"""
    You are a senior data scientist doing inital analysis on uploaded CSV files. 
    NEVER MAKE UP INFORMATION. you were created to; 
    1. Perform statistical analysis (Null detection, Outlier analysis).
    2. use deterministic Python logic for 100% mathematical accuracy, 
    using AI only to *interpret* the findings and suggest remediation plans.
    YOU MUST NOT FABRICATE ANTYHING. ONLY USE THE PROVIDED JSON DATA.
    If the data is not in the JSON, say it is missing
    {json.dumps(summarized_data, indent=2)}
    

    BASED EXCLUSIVELY ON THE AUDIT DATA PROVIDED ABOVE, Provide a 3-bullet point summary :
    1. The biggest data quality issue found 
    (DO NOT mention all specific row numbers for each quality issue, instead
    output issues in each column, sending counts of each issue per column).
    2. Which columns are ready for use (zero nulls, zero inconsistencies).
    3. Which columns have inconsistencies, identify every row with issues ().
    4. Suggest what Pandas datatype inconsistent columns should be converted to. 
    """
    return prompt

def analyze_with_openai(json_path):
    #Checks to see if user has provided a API KEY
    if not os.getenv("OPENAI_API_KEY"):
        return """
==============================
ERROR: No OpenAI API key found.
==============================
Want to run locally instead?
==============================
Please either:
1. Create a .env file and add your key as 'OPENAI_API_KEY=your-key-here'
2. Run 'python main.py --model ollama' to use local AI instead.
"""

    # 1. Open the JSON report
    try:
        with open(json_path, 'r') as f:
            audit_data = json.load(f)
    except FileNotFoundError:
        return "Error: Could not find the audit_summary.json file."

    # 2. Get the prompt (now using our new function)
    prompt = get_prompt(audit_data)

    # 3. Call OpenAI and return the response
    response = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def analyze_with_ollama(json_path):
    # 1. Open the JSON report
    try:
        with open(json_path, 'r') as f:
            audit_data = json.load(f)
    except FileNotFoundError:
        return "Error: Could not find the audit_summary.json file."

    # 2. Get the prompt (same as openai)
    prompt = get_prompt(audit_data)

    # 3. Call Ollama on local server for max privacy of data and return the response
    ollama_payload = {
        "model": "llama3.2",
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 1500
        }    
    }
    
    try:
        response = requests.post("http://localhost:11434/api/generate", json=ollama_payload)
        
        if response.status_code == 200:
            return response.json()['response']
        else:
            return f"Error: Ollama API returned status code {response.status_code}"
    
    except requests.exceptions.ConnectionError:
        return "Error: Cannot connect to Ollama. Make sure it's running."
    
def analyze_audit_results(json_path, provider='openai'):
    """Main function - routes to correct provider"""
    if provider == 'openai':
        return analyze_with_openai(json_path)
    elif provider == 'ollama':
        return analyze_with_ollama(json_path)
    else:
        return "Error: Invalid provider specified."