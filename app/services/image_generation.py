import logging
import urllib.parse
from app.services.llm_service import SafetyModeration
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class ImageGenerationService:
    """Generate Christian-themed images with safety checks."""

    def __init__(self):
        self.safety = SafetyModeration()

    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        style: str = "realistic"
    ) -> Tuple[Optional[str], bool]:
        """Generate Christian-themed image."""

        if not prompt or len(prompt) < 5:
            return None, False

        safety_result = await self.safety.check_content_safety(prompt)

        if not safety_result.is_safe:
            logger.warning(
                f"Unsafe image prompt: {safety_result.reason}"
            )
            return None, False

        enhanced_prompt = self._enhance_prompt(
            prompt,
            style
        )

        try:

            encoded_prompt = urllib.parse.quote(
                enhanced_prompt
            )

            image_url = (
                "https://image.pollinations.ai/prompt/"
                f"{encoded_prompt}"
            )

            logger.info(
                "Image URL generated successfully"
            )

            return image_url, True

        except Exception as e:
            logger.error(
                f"Error generating image: {e}"
            )

            return None, False

    def _enhance_prompt(
        self,
        prompt: str,
        style: str
    ) -> str:
        """Enhance prompt."""

        style_mappings = {
            "realistic":
                "photorealistic, highly detailed",

            "artistic":
                "digital painting, cinematic art",

            "symbolic":
                "symbolic spiritual illustration",

            "abstract":
                "abstract spiritual art"
        }

        style_desc = style_mappings.get(
            style,
            "high quality"
        )

        enhanced = (
            f"{prompt}, "
            f"{style_desc}, "
            "Christian themed, "
            "respectful, "
            "spiritually uplifting"
        )

        return enhanced

    async def validate_image_safety(
        self,
        image_url: str
    ) -> bool:
        return True





# 
# 
# import logging
# from openai import AsyncOpenAI
# from app.config import get_settings
# from app.services.llm_service import SafetyModeration
# from typing import Tuple, Optional

# logger = logging.getLogger(__name__)
# settings = get_settings()


# class ImageGenerationService:
#     """Generate Christian-themed images with safety checks."""
    
#     def __init__(self):
#         self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
#         self.settings = get_settings()
#         self.safety = SafetyModeration()
    
#     async def generate_image(
#         self,
#         prompt: str,
#         size: str = "1024x1024",
#         style: str = "realistic"
#     ) -> Tuple[Optional[str], bool]:
#         """Generate Christian-themed image."""
        
#         if not prompt or len(prompt) < 10:
#             return None, False
        
#         safety_result = await self.safety.check_content_safety(prompt)
#         if not safety_result.is_safe:
#             logger.warning(f"Image prompt flagged as unsafe: {safety_result.reason}")
#             return None, False
        
#         enhanced_prompt = self._enhance_prompt(prompt, style)
        
#         try:
#             response = await self.client.images.generate(
#                 model=self.settings.IMAGE_GENERATION_MODEL,
#                 prompt=enhanced_prompt,
#                 size=size,
#                 quality="standard",
#                 n=1
#             )
            
#             image_url = response.data[0].url
#             logger.info(f"Generated image successfully")
#             return image_url, True
#         except Exception as e:
#             logger.error(f"Error generating image: {e}")
#             return None, False
    
#     def _enhance_prompt(self, prompt: str, style: str) -> str:
#         """Enhance prompt with Christian context and style."""
        
#         style_mappings = {
#             "realistic": "photorealistic, high quality, detailed",
#             "artistic": "artistic illustration, painted, expressive",
#             "symbolic": "symbolic representation, meaningful, spiritual",
#             "abstract": "abstract art, modern, conceptual"
#         }
        
#         style_desc = style_mappings.get(style, "high quality")
        
#         enhanced = f"{prompt}, {style_desc}, Christian themed, respectful, spiritually uplifting"
#         return enhanced
    
#     async def validate_image_safety(self, image_url: str) -> bool:
#         """Validate generated image doesn't violate policies."""
#         return True
