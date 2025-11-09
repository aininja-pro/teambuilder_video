"""
Claude (Anthropic) scope parsing service
Replaces OpenAI GPT-4 for construction scope analysis
"""
import anthropic
from anthropic import Anthropic
from config.settings import settings
import logging
import json
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Initialize Anthropic client
client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)


# Default construction cost codes (fallback if client has none)
# Standard industry categories - clients can define their own custom codes
DEFAULT_COST_CODES = [
    {"code": "01", "name": "General Conditions"},
    {"code": "02", "name": "Site Preparation / Demolition"},
    {"code": "03", "name": "Excavation / Grading / Landscape"},
    {"code": "04", "name": "Concrete & Masonry"},
    {"code": "05", "name": "Rough Carpentry / Framing"},
    {"code": "06", "name": "Doors, Windows, Trim"},
    {"code": "07", "name": "Mechanical (HVAC)"},
    {"code": "08", "name": "Electrical"},
    {"code": "09", "name": "Plumbing"},
    {"code": "10", "name": "Wall & Ceiling Coverings (Drywall, Plaster)"},
    {"code": "11", "name": "Finish Carpentry"},
    {"code": "12", "name": "Cabinets, Vanities, Countertops"},
    {"code": "13", "name": "Flooring / Tile"},
    {"code": "14", "name": "Specialties (Appliances, Fixtures)"},
    {"code": "15", "name": "Decking"},
    {"code": "16", "name": "Fencing"},
    {"code": "17", "name": "Exterior Facade (Siding, Brick, Stone)"},
    {"code": "18", "name": "Soffit, Fascia, Gutters"},
    {"code": "19", "name": "Roofing"},
]


class ScopeParsingService:
    """Parse construction scope from transcripts using Claude"""

    def __init__(self):
        self.client = client

    def _build_prompt(
        self,
        transcript: str,
        cost_codes: Optional[List[Dict]] = None,
        photo_descriptions: Optional[List[str]] = None
    ) -> str:
        """
        Build construction-expert prompt for Claude

        Args:
            transcript: Video/audio transcript or text input
            cost_codes: Client-specific cost codes (or None for default)
            photo_descriptions: Descriptions of photos from Claude Vision

        Returns:
            Formatted prompt string
        """
        codes = cost_codes if cost_codes else DEFAULT_COST_CODES

        # Format cost codes for prompt
        codes_text = "\n".join([
            f"- {c['code']}: {c['name']}"
            for c in codes
        ])

        # Add photo context if available
        photo_context = ""
        if photo_descriptions:
            photo_context = "\n\nPHOTO ANALYSIS:\n"
            for i, desc in enumerate(photo_descriptions, 1):
                photo_context += f"\nPhoto {i}: {desc}\n"

        prompt = f"""You are an expert construction estimator and scope analyst with 20+ years of experience. Your job is to analyze construction project information and extract a comprehensive scope of work.

COST CODE SYSTEM:
{codes_text}

TRANSCRIPT/PROJECT INFORMATION:
{transcript}
{photo_context}

Please analyze this construction project and extract:

1. **Project Summary**:
   - Overview: A 2-3 sentence description of the overall project
   - Key Requirements: List of main project requirements (bulleted)
   - Concerns: Any challenges, risks, or concerns identified (bulleted)
   - Decision Points: Questions or decisions that need client input (bulleted)
   - Important Notes: Other critical information (bulleted)

2. **Scope Items**:
   For each distinct work item mentioned, extract:
   - cost_code: The 2-digit code from the list above
   - category: The category name
   - description: Clear description of the work
   - location: Where in the building (e.g., "Kitchen", "Master Bathroom", "Exterior")
   - materials: Specific materials mentioned (or "To be determined")
   - quantity: Quantities mentioned (or "To be determined")
   - notes: Any special requirements or considerations
   - risk_level: "low", "medium", or "high" based on complexity/cost/risk

3. **Scope Completeness Score** (0-100):
   Rate how complete and detailed this scope is. Consider:
   - Are all major building systems addressed?
   - Are quantities and materials specified?
   - Are there obvious gaps or missing information?
   - Is location information clear?

Return your analysis as a JSON object with this structure:
{{
  "project_summary": {{
    "overview": "...",
    "key_requirements": ["...", "..."],
    "concerns": ["...", "..."],
    "decision_points": ["...", "..."],
    "important_notes": ["...", "..."]
  }},
  "scope_items": [
    {{
      "cost_code": "01",
      "category": "General Conditions",
      "sub_code": null,
      "sub_category": null,
      "description": "...",
      "location": "...",
      "materials": "...",
      "quantity": "...",
      "notes": "...",
      "risk_level": "medium"
    }}
  ],
  "scope_completeness_score": 75
}}

Be thorough and extract every work item mentioned. If something is unclear, note it in decision_points. If materials/quantities aren't specified, write "To be determined" rather than guessing."""

        return prompt

    async def parse_scope(
        self,
        transcript: str,
        cost_codes: Optional[List[Dict]] = None,
        photo_descriptions: Optional[List[str]] = None
    ) -> Dict:
        """
        Parse construction scope from transcript using Claude

        Args:
            transcript: Video/audio transcript or text input
            cost_codes: Client-specific cost codes (or None for default)
            photo_descriptions: Optional photo descriptions for context

        Returns:
            Dict with project_summary, scope_items, and score
        """
        try:
            logger.info("Starting scope parsing with Claude...")

            prompt = self._build_prompt(transcript, cost_codes, photo_descriptions)

            # Call Claude API
            message = self.client.messages.create(
                model=settings.CLAUDE_MODEL,
                max_tokens=settings.CLAUDE_MAX_TOKENS,
                temperature=settings.CLAUDE_TEMPERATURE,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Extract response
            response_text = message.content[0].text

            # Parse JSON response
            # Claude sometimes wraps JSON in markdown code blocks, so clean it
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            result = json.loads(response_text)

            # Calculate cost (Claude pricing: ~$3 per million input tokens, $15 per million output)
            # This is approximate
            input_tokens = message.usage.input_tokens
            output_tokens = message.usage.output_tokens
            cost_usd = (input_tokens / 1_000_000 * 3.0) + (output_tokens / 1_000_000 * 15.0)

            logger.info(f"Scope parsing completed. Items: {len(result.get('scope_items', []))}")
            logger.info(f"Cost: ${cost_usd:.4f}")

            # Add metadata
            result["metadata"] = {
                "model": settings.CLAUDE_MODEL,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": round(cost_usd, 4)
            }

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response as JSON: {e}")
            logger.error(f"Response: {response_text}")
            raise Exception("Failed to parse AI response. Please try again.")

        except Exception as e:
            logger.error(f"Error parsing scope with Claude: {e}")
            raise


# Global instance
scope_parsing_service = ScopeParsingService()


async def parse_construction_scope(
    transcript: str,
    cost_codes: Optional[List[Dict]] = None,
    photo_descriptions: Optional[List[str]] = None
) -> Dict:
    """Convenience function to parse scope"""
    return await scope_parsing_service.parse_scope(transcript, cost_codes, photo_descriptions)
