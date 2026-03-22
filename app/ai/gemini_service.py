import google.generativeai as genai
import os
from typing import Dict, Any

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def analyze_claim(claim_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze claim for fraud using Gemini AI
    """
    model = genai.GenerativeModel("gemini-1.0-pro")
    prompt = f"""
    You are an expert insurance fraud analyst AI. Analyze the following motor insurance claim and return a JSON object with:
    - fraud_risk_score: float between 0 (no risk) and 1 (certain fraud)
    - explanation: a clear, human-readable summary of why you gave this score
    - incoherences: a list of detected incoherences or suspicious points, each as an object with 'field', 'issue', and 'suggestion'.
    - recommendation: a short action recommendation (e.g. 'Approve', 'Investigate', 'Reject')

    Claim details: {claim_data}

    Example output:
    {{
      "fraud_risk_score": 0.8,
      "explanation": "The claim contains inconsistencies in the accident date and location. The description is vague.",
      "incoherences": [
        {{"field": "date_of_accident", "issue": "Date is in the future", "suggestion": "Verify with claimant"}},
        {{"field": "description", "issue": "Too short", "suggestion": "Request more details"}}
      ],
      "recommendation": "Investigate"
    }}

    Respond ONLY with the JSON object.
    """
    try:
        # response = model.generate_content(prompt)
        # parsed = json.loads(response.text)  # In real use, parse Gemini output
        # For now, return a realistic, structured placeholder
        return {
            "fraud_risk_score": 0.7,
            "explanation": "The claim description is vague and the location is unusual for the driver.",
            "incoherences": [
                {"field": "description", "issue": "Too generic", "suggestion": "Ask for more details"},
                {"field": "gps_latitude", "issue": "Unusual location", "suggestion": "Verify accident location with GPS data"}
            ],
            "recommendation": "Investigate"
        }
    except Exception as e:
        return {
            "fraud_risk_score": 0.5,
            "explanation": "Error in analysis.",
            "incoherences": [],
            "recommendation": "Error"
        }