import os
import json
from typing import List, Dict
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# TeamBuilders Cost Code Structure
TEAMBUILDERS_COST_CODES = {
  "01 General Conditions": {
    "1100": "Permit",
    "1200": "Project Oversight (Management, Coordination, Procurement)",
    "1600": "Tool & Equipment Rental"
  },
  "02 Site/Demo": {
    "1700": "Dump & Trash Removal",
    "1800": "Demolition (Wall, Deck, Roof, Flooring, Kitchen)",
    "1900": "Prep Work & Dust Protection"
  },
  "03 Excavation/Landscape": {
    "2100": "Landscaping"
  },
  "04 Concrete/Masonry": {
    "2200": "Concrete Footings & Foundations",
    "2250": "Concrete Flatwork",
    "2299": "Concrete/Masonry Specialties"
  },
  "05 Rough Carpentry": {
    "3000": "Floor & Stair Framing",
    "3100": "Wall Framing",
    "3200": "Roof Framing"
  },
  "06 Doors/Windows": {
    "3500": "Exterior Doors",
    "3600": "Windows"
  },
  "07 Mechanical": {
    "4000": "HVAC System"
  },
  "08 Electrical": {
    "4100": "Electrical System"
  },
  "09 Plumbing": {
    "4200": "Plumbing System",
    "4250": "Plumbing Fixtures"
  },
  "10 Wall/Ceiling Coverings": {
    "5000": "Insulation",
    "5100": "Drywall",
    "5200": "Paint"
  },
  "11 Finish Carpentry": {
    "5300": "Interior Doors",
    "5350": "Interior Door Hardware",
    "5400": "Interior Trim",
    "5450": "Interior Trim Specialties"
  },
  "12 Cabinets/Vanities/Tops": {
    "5600": "Kitchen Cabinets",
    "5650": "Bathroom Vanities",
    "5680": "Built-In Cabinetry",
    "5699": "Cabinet Hardware Specialties",
    "5700": "Countertops"
  },
  "13 Flooring/Tile": {
    "5800": "Flooring"
  },
  "14 Specialties": {
    "6000": "Closet Shelving",
    "6200": "Appliances",
    "6300": "Specialty Glass"
  },
  "15 Decking": {
    "7000": "Decking"
  },
  "16 Fencing": {},
  "17 Exterior Facade": {
    "7200": "House Wrap",
    "7220": "Vinyl Siding",
    "7240": "Luxury Siding"
  },
  "18 Soffit/Fascia/Gutters": {
    "7300": "Soffit/Fascia",
    "7340": "Gutters"
  },
  "19 Roofing": {
    "7400": "Asphalt Roofing"
  }
}

def parse_scope(transcript: str) -> List[Dict[str, str]]:
    """
    Parse transcript into scope items using GPT-4 with TeamBuilders cost codes.
    
    Args:
        transcript: The transcribed text from the video/audio
        
    Returns:
        List[Dict[str, str]]: List of scope items with TeamBuilders cost code structure
        
    Raises:
        Exception: If parsing fails
    """
    try:
        # Get OpenAI API key from environment
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY in your .env file.")
        
        # Set up OpenAI client (new v1.0+ API)
        client = OpenAI(api_key=api_key)
        
        # Create the system prompt
        system_prompt = f"""
You are a highly accurate construction estimator working with structured data.
Your output MUST be a valid JSON array ONLY, with no extra text, explanations, or commentary.

You are an expert construction estimator specializing in TeamBuilders cost code classification. Analyze the following transcript from a job site video and extract scope items organized by TeamBuilders cost codes.

TeamBuilders Cost Code Structure:
{json.dumps(TEAMBUILDERS_COST_CODES, indent=2)}

Instructions:
1. CAREFULLY analyze the transcript for construction activities, materials, and work being performed
2. Match each identified item to the MOST SPECIFIC TeamBuilders subcode (4-digit) when possible
3. If an exact subcode match isn't clear, use the main category code (01-19)
4. Extract SPECIFIC details mentioned including:
   - Quantities (if mentioned)
   - Materials specified
   - Dimensions or measurements
   - Location in the building
   - Any special requirements or notes
5. Be comprehensive - capture ALL construction-related items mentioned
6. Do NOT invent or assume items not clearly stated or shown in the transcript

Key Matching Guidelines:
- Permits, inspections, project management → 01 General Conditions
- Any demolition or removal work → 02 Site/Demo
- Foundation, footings, slabs → 04 Concrete/Masonry
- Framing (floor, wall, roof) → 05 Rough Carpentry
- Door and window installation → 06 Doors/Windows
- HVAC, furnace, ductwork → 07 Mechanical
- Electrical wiring, fixtures, outlets → 08 Electrical
- Plumbing pipes, fixtures, water heaters → 09 Plumbing
- Insulation, drywall, painting → 10 Wall/Ceiling Coverings
- Interior doors, trim, molding → 11 Finish Carpentry
- Cabinets, countertops, vanities → 12 Cabinets/Vanities/Tops
- Flooring materials (LVT, carpet, tile) → 13 Flooring/Tile
- Appliances, mirrors, shelving → 14 Specialties
- Deck construction → 15 Decking
- Siding, house wrap → 17 Exterior Facade
- Soffit, fascia, gutters → 18 Soffit/Fascia/Gutters
- Roofing materials and work → 19 Roofing

Return ONLY a valid JSON array with the following format:
[
  {{
    "mainCode": "05",
    "mainCategory": "Rough Carpentry",
    "subCode": "3100",
    "subCategory": "Wall Framing",
    "description": "Installing 2x6 wall studs for exterior walls on main level",
    "details": {{
      "material": "2x6x8 precut studs",
      "location": "Main level exterior walls",
      "quantity": "Not specified",
      "notes": "Standard 16-inch on center spacing mentioned"
    }}
  }}
]

IMPORTANT: Return ONLY the JSON array. No explanatory text before or after.
"""

        user_prompt = f"Transcript to analyze:\n\n{transcript}"
        
        # Call GPT-4 using the new API structure
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=2000
        )
        
        # Extract the response content
        response_text = response.choices[0].message.content.strip()
        
        # Parse the JSON response
        try:
            scope_items = json.loads(response_text)
            
            # Validate the structure
            if not isinstance(scope_items, list):
                raise ValueError("Response is not a list")
            
            for item in scope_items:
                required_keys = ['mainCode', 'mainCategory', 'subCode', 'subCategory', 'description', 'details']
                if not all(key in item for key in required_keys):
                    raise ValueError("Missing required keys in scope item")
            
            return scope_items
            
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse GPT-4 response as JSON: {str(e)}\nResponse: {response_text}")
            
    except Exception as e:
        raise Exception(f"Scope parsing failed: {str(e)}")

def format_scope_items_for_display(scope_items: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Format scope items for display in Streamlit dataframe.
    
    Args:
        scope_items: List of scope items from parse_scope()
        
    Returns:
        List[Dict[str, str]]: Formatted items with TeamBuilders structure
    """
    formatted_items = []
    
    for item in scope_items:
        formatted_items.append({
            'Main Code': item.get('mainCode', ''),
            'Main Category': item.get('mainCategory', ''),
            'Sub Code': item.get('subCode', ''),
            'Sub Category': item.get('subCategory', ''),
            'Description': item.get('description', ''),
            'Material': item.get('details', {}).get('material', ''),
            'Location': item.get('details', {}).get('location', ''),
            'Quantity': item.get('details', {}).get('quantity', ''),
            'Notes': item.get('details', {}).get('notes', '')
        })
    
    # Sort by main code, then sub code
    formatted_items.sort(key=lambda x: (x['Main Code'], x['Sub Code']))
    
    return formatted_items 