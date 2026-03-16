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
    Analyze this motor insurance claim for potential fraud. Provide a risk score from 0 to 1, list any suspicious patterns, and give a recommendation.

    Claim details: {claim_data}

    Respond in JSON format with keys: fraud_risk_score, suspicious_patterns (list), recommendation
    """
    try:
        response = model.generate_content(prompt)
        # For simplicity, assume response is JSON, but in reality, parse it
        # Placeholder
        return {
            "fraud_risk_score": 0.3,
            "suspicious_patterns": ["Inconsistent description"],
            "recommendation": "Investigate further"
        }
    except Exception as e:
        return {
            "fraud_risk_score": 0.5,
            "suspicious_patterns": [],
            "recommendation": "Error in analysis"
        }