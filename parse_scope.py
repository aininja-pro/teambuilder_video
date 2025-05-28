import openai
import os
import json
from typing import List, Dict
import streamlit as st

# Cost code mapping for construction divisions (01-19)
COST_CODE_MAPPING = {
    "01": "General Requirements",
    "02": "Existing Conditions", 
    "03": "Concrete",
    "04": "Masonry",
    "05": "Metals",
    "06": "Wood, Plastics, and Composites",
    "07": "Thermal and Moisture Protection",
    "08": "Openings",
    "09": "Finishes",
    "10": "Specialties",
    "11": "Equipment",
    "12": "Furnishings",
    "13": "Special Construction",
    "14": "Conveying Equipment",
    "21": "Fire Suppression",
    "22": "Plumbing",
    "23": "HVAC",
    "26": "Electrical",
    "27": "Communications",
    "28": "Electronic Safety and Security"
}

def parse_scope(transcript: str, mapping: Dict[str, str] = None) -> List[Dict[str, str]]:
    """
    Parse transcript into structured scope items using GPT-4.
    
    Args:
        transcript: The transcribed text from the video/audio
        mapping: Optional custom cost code mapping (defaults to standard construction codes)
        
    Returns:
        List[Dict]: List of scope items with 'code', 'title', and 'details' keys
        
    Raises:
        Exception: If parsing fails
    """
    try:
        # Get OpenAI API key from environment
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY in your .env file.")
        
        # Use provided mapping or default
        if mapping is None:
            mapping = COST_CODE_MAPPING
        
        # Set up OpenAI client
        openai.api_key = api_key
        
        # Create the system prompt
        system_prompt = f"""You are a construction project analyst. Your task is to analyze a transcript from a job site video and extract scope items organized by cost codes.

Cost Code Mapping:
{json.dumps(mapping, indent=2)}

Instructions:
1. Analyze the transcript and identify specific work items, materials, or tasks mentioned
2. Categorize each item according to the appropriate cost code division
3. Extract a clear title and detailed description for each scope item
4. Return ONLY a valid JSON array with this exact structure:
[
  {{
    "code": "XX",
    "title": "Brief descriptive title",
    "details": "Detailed description of the work item"
  }}
]

Requirements:
- Use only the cost codes provided in the mapping
- Each scope item must have all three fields: code, title, details
- Be specific and actionable in descriptions
- If no relevant scope items are found, return an empty array []
- Return ONLY the JSON array, no other text or formatting"""

        # Create the user prompt with the transcript
        user_prompt = f"Analyze this job site transcript and extract scope items:\n\n{transcript}"
        
        # Call GPT-4
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,  # Low temperature for consistent output
            max_tokens=2000
        )
        
        # Extract the response content
        response_content = response.choices[0].message.content.strip()
        
        # Parse the JSON response
        try:
            scope_items = json.loads(response_content)
            
            # Validate the structure
            if not isinstance(scope_items, list):
                raise ValueError("Response is not a list")
            
            for item in scope_items:
                if not isinstance(item, dict):
                    raise ValueError("Scope item is not a dictionary")
                if not all(key in item for key in ['code', 'title', 'details']):
                    raise ValueError("Scope item missing required fields")
                if item['code'] not in mapping:
                    raise ValueError(f"Invalid cost code: {item['code']}")
            
            return scope_items
            
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse GPT-4 response as JSON: {str(e)}")
        except ValueError as e:
            raise Exception(f"Invalid scope item structure: {str(e)}")
            
    except Exception as e:
        raise Exception(f"Scope parsing failed: {str(e)}")

def format_scope_items_for_display(scope_items: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Format scope items for display in Streamlit dataframe.
    
    Args:
        scope_items: List of scope items from parse_scope()
        
    Returns:
        List[Dict]: Formatted scope items with division names
    """
    formatted_items = []
    
    for item in scope_items:
        formatted_item = {
            "Code": item['code'],
            "Division": COST_CODE_MAPPING.get(item['code'], "Unknown"),
            "Title": item['title'],
            "Details": item['details']
        }
        formatted_items.append(formatted_item)
    
    # Sort by cost code
    formatted_items.sort(key=lambda x: x['Code'])
    
    return formatted_items 