"""
Claude Vision service for photo analysis
Analyzes construction site photos for materials, conditions, and scope items
"""
import anthropic
from anthropic import Anthropic
from config.settings import settings
import logging
import json
from typing import Dict, List
import base64
import httpx

logger = logging.getLogger(__name__)

# Initialize Anthropic client
client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)


class VisionService:
    """Analyze construction photos using Claude Vision"""

    def __init__(self):
        self.client = client

    async def analyze_photo(
        self,
        image_url: str,
        context: str = ""
    ) -> Dict:
        """
        Analyze a construction photo using Claude Vision

        Args:
            image_url: URL to the image (can be Supabase Storage URL)
            context: Optional context about the project

        Returns:
            Dict with caption, materials, conditions, risks, and scope_category
        """
        try:
            logger.info(f"Analyzing photo: {image_url}")

            # Download image and convert to base64
            async with httpx.AsyncClient() as client_http:
                response = await client_http.get(image_url)
                response.raise_for_status()
                image_data = response.content
                image_base64 = base64.b64encode(image_data).decode('utf-8')

            # Determine media type from URL
            media_type = "image/jpeg"
            if image_url.lower().endswith('.png'):
                media_type = "image/png"
            elif image_url.lower().endswith('.webp'):
                media_type = "image/webp"

            # Build prompt
            prompt = f"""You are an expert construction inspector analyzing a construction site photo.

{f"PROJECT CONTEXT: {context}" if context else ""}

Please analyze this photo and provide:

1. **Caption**: A brief 1-2 sentence description of what's shown
2. **Materials**: List of materials visible (wood, drywall, concrete, tile, etc.)
3. **Conditions**: Current state/condition observations (damaged, new, existing, etc.)
4. **Risks**: Any safety concerns, quality issues, or potential problems
5. **Scope Category**: Which construction category this relates to (Plumbing, Electrical, Framing, Flooring, etc.)

Return your analysis as JSON:
{{
  "caption": "...",
  "materials": ["...", "..."],
  "conditions": ["...", "..."],
  "risks": ["...", "..."],
  "scope_category": "..."
}}

Be specific and professional. Note anything that might affect cost, timeline, or quality."""

            # Call Claude Vision API
            message = self.client.messages.create(
                model=settings.CLAUDE_MODEL,
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_base64
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )

            # Extract response
            response_text = message.content[0].text

            # Parse JSON
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            result = json.loads(response_text)

            # Calculate cost
            input_tokens = message.usage.input_tokens
            output_tokens = message.usage.output_tokens
            cost_usd = (input_tokens / 1_000_000 * 3.0) + (output_tokens / 1_000_000 * 15.0)

            result["metadata"] = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": round(cost_usd, 4)
            }

            logger.info(f"Photo analysis completed. Cost: ${cost_usd:.4f}")

            return result

        except Exception as e:
            logger.error(f"Error analyzing photo: {e}")
            raise

    async def analyze_multiple_photos(
        self,
        image_urls: List[str],
        context: str = ""
    ) -> List[Dict]:
        """
        Analyze multiple photos

        Args:
            image_urls: List of image URLs
            context: Optional project context

        Returns:
            List of analysis results
        """
        try:
            logger.info(f"Analyzing {len(image_urls)} photos...")

            results = []
            total_cost = 0.0

            for i, url in enumerate(image_urls, 1):
                logger.info(f"Processing photo {i}/{len(image_urls)}")

                result = await self.analyze_photo(url, context)
                results.append(result)

                total_cost += result.get("metadata", {}).get("cost_usd", 0)

            logger.info(f"All photos analyzed. Total cost: ${total_cost:.4f}")

            return results

        except Exception as e:
            logger.error(f"Error analyzing multiple photos: {e}")
            raise


# Global instance
vision_service = VisionService()


async def analyze_construction_photo(image_url: str, context: str = "") -> Dict:
    """Convenience function to analyze a single photo"""
    return await vision_service.analyze_photo(image_url, context)


async def analyze_construction_photos(image_urls: List[str], context: str = "") -> List[Dict]:
    """Convenience function to analyze multiple photos"""
    return await vision_service.analyze_multiple_photos(image_urls, context)
