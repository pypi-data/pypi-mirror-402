"""OpenRouter provider for OCR transcription."""

import logging
from typing import Optional

import openai

from .base import BaseProvider
from ..utils import handle_error, _encode_image


class OpenRouterProvider(BaseProvider):
    """OpenRouter provider for OCR transcription.

    Routes requests to various models through OpenRouter's API.
    Uses the OpenAI SDK with a custom base URL.

    Top performer from Inkbench: qwen/qwen3-vl-235b (89% accuracy).
    """

    name = "openrouter"
    requires_api_key = True
    default_model = "qwen/qwen3-vl-235b"  # Top Inkbench performer: 89% accuracy

    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

    def transcribe(
        self,
        image_path: str,
        prompt: str,
        model: str,
        api_key: Optional[str] = None,
        debug: bool = False,
        **kwargs,
    ) -> str:
        """Transcribe text from an image using OpenRouter.

        Args:
            image_path: Path to the image file.
            prompt: The prompt to use for transcription.
            model: The model identifier (e.g., qwen/qwen3-vl-235b).
            api_key: OpenRouter API key.
            debug: Enable debug logging.
            **kwargs: Additional options (unused for OpenRouter).

        Returns:
            Raw transcribed text.
        """
        if debug:
            logging.info(f"Transcribing with OpenRouter, model: {model}")

        try:
            client = openai.OpenAI(
                base_url=self.OPENROUTER_BASE_URL,
                api_key=api_key,
            )
            base64_image = _encode_image(image_path)
            media_type = self._get_media_type(image_path)

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{media_type};base64,{base64_image}"
                                },
                            },
                        ],
                    }
                ],
                stream=False,
            )
            return response.choices[0].message.content.strip()

        except openai.OpenAIError as e:
            handle_error(f"OpenRouter API error: {e}", e)
        except Exception as e:
            handle_error("Error during OpenRouter transcription", e)
