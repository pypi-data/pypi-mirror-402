# This file is a function that uses a discord webhook to receive feedback from users
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def send_feedback():
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    
    if not webhook_url:
        print("Feedback not configured.")
        return
    
    # Ask user if they want to send feedback
    response = input("""
    ======================================================================
    HEY, are you an Engineer or DataScientist? If so, send feedback! (y/n)
    ====================================================================== 
    : """).strip().lower()
    
    if response != 'y':
        print("Thanks for using VaultLens!")
        return
    
    # Get their feedback
    print("Type your feedback (press Enter to send):")
    feedback_text = input("> ")
    
    if not feedback_text.strip():
        print("No feedback entered.")
        return
    
    # Send to Discord
    payload = {
        "content": f"**VaultLens Feedback:**\n{feedback_text}"
    }
    
    try:
        result = requests.post(webhook_url, json=payload)
        if result.status_code == 204:
            print("Feedback sent! Thank you!")
        else:
            print(f"Failed to send feedback. Status: {result.status_code}")
    except requests.exceptions.RequestException:
        print("Error: Could not connect to send feedback.")