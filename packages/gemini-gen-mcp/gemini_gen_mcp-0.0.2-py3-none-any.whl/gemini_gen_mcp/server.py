"""MCP Server for Gemini Image and Audio generation using fastmcp."""

import os
import base64
import io
import json
import time
import wave

from enum import StrEnum
from datetime import datetime
from typing import Annotated, Optional
from google import genai
from google.genai import types
from fastmcp import FastMCP
from fastmcp.utilities.types import Image, Audio

# Initialize FastMCP server
mcp = FastMCP("gemini-gen-mcp")


def get_download_path(sub_dir: str) -> str:
    """Get the download path for generated files."""
    download_path = os.path.join(
        os.environ.get("GEMINI_DOWNLOAD_PATH", "/tmp/gemini_gen_mcp"), sub_dir
    )
    os.makedirs(download_path, exist_ok=True)
    return download_path


def get_api_key() -> str:
    """Get Gemini API key from environment."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY environment variable is required. "
            "Get your API key from https://aistudio.google.com/apikey"
        )
    return api_key


def create_client() -> genai.Client:
    """Create and return a Gemini API client."""
    return genai.Client(api_key=get_api_key())


class ImageModels(StrEnum):
    """Supported Gemini image generation models."""

    NANO_BANANA = "gemini-2.5-flash-image"
    NANO_BANANA_PRO = "gemini-3-pro-image-preview"


class AspectRatio(StrEnum):
    """Supported aspect ratios for image generation."""

    SQUARE = "1:1"
    PORTRAIT_2_3 = "2:3"
    LANDSCAPE_3_2 = "3:2"
    PORTRAIT_3_4 = "3:4"
    LANDSCAPE_4_3 = "4:3"
    PORTRAIT_4_5 = "4:5"
    LANDSCAPE_5_4 = "5:4"
    PORTRAIT_9_16 = "9:16"
    LANDSCAPE_16_9 = "16:9"
    LANDSCAPE_21_9 = "21:9"


class AudioModels(StrEnum):
    """Supported Gemini image generation models."""

    GEMINI_2_5_FLASH_PREVIEW_TTS = "gemini-2.5-flash-preview-tts"
    GEMINI_2_5_PRO_PREVIEW_TTS = "gemini-2.5-pro-preview-tts"


# | Column 1               | Column 2                     | Column 3                   |
# | ---------------------- | ---------------------------- | -------------------------- |
# | Zephyr – *Bright*      | Puck – *Upbeat*              | Charon – *Informative*     |
# | Kore – *Firm*          | Fenrir – *Excitable*         | Leda – *Youthful*          |
# | Orus – *Firm*          | Aoede – *Breezy*             | Callirrhoe – *Easy-going*  |
# | Autonoe – *Bright*     | Enceladus – *Breathy*        | Iapetus – *Clear*          |
# | Umbriel – *Easy-going* | Algieba – *Smooth*           | Despina – *Smooth*         |
# | Erinome – *Clear*      | Algenib – *Gravelly*         | Rasalgethi – *Informative* |
# | Laomedeia – *Upbeat*   | Achernar – *Soft*            | Alnilam – *Firm*           |
# | Schedar – *Even*       | Gacrux – *Mature*            | Pulcherrima – *Forward*    |
# | Achird – *Friendly*    | Zubenelgenubi – *Casual*     | Vindemiatrix – *Gentle*    |
# | Sadachbia – *Lively*   | Sadaltager – *Knowledgeable* | Sulafat – *Warm*           |


class VoiceName(StrEnum):
    """TTS models voice names."""

    ZEPHYR = "Zephyr"
    KORE = "Kore"
    ORUS = "Orus"
    AUTONOE = "Autonoe"
    UMBRIEL = "Umbriel"
    ERINOME = "Erinome"
    LAOMEDEIA = "Laomedeia"
    SCHEDAR = "Schedar"
    ACHIRD = "Achird"
    SADACHBIA = "Sadachbia"
    PUCK = "Puck"
    FENRIR = "Fenrir"
    AOEDE = "Aoede"
    ENCELADUS = "Enceladus"
    ALGIEBA = "Algieba"
    ALGENIB = "Algenib"
    ACHERNAR = "Achernar"
    GACRUX = "Gacrux"
    ZUBENELGENUBI = "Zubenelgenubi"
    SADALTAGER = "Sadaltager"
    CHARON = "Charon"
    LEDA = "Leda"
    CALLIRRHOE = "Callirrhoe"
    IAPETUS = "Iapetus"
    DESPINA = "Despina"
    RASALGETHI = "Rasalgethi"
    ALNILAM = "Alnilam"
    PULCHERRIMA = "Pulcherrima"
    VINDEMIATRIX = "Vindemiatrix"
    SULAFAT = "Sulafat"


@mcp.tool()
async def text_to_image(
    prompt: Annotated[str, "Text description of the image to generate"],
    model: ImageModels = ImageModels.NANO_BANANA,
    aspect_ratio: AspectRatio = AspectRatio.SQUARE,
    temperature: Annotated[
        float, "Sampling temperature for image generation (default: 1.0)"
    ] = 1.0,
    top_p: Annotated[
        Optional[float], "Nucleus sampling parameter for image generation (optional)"
    ] = None,
) -> Image:
    """Generate images from text using Gemini's Flash (Nano Banana) Image models."""

    # Configure Gemini API
    # https://ai.google.dev/gemini-api/docs/image-generation
    client = create_client()

    # Generate image with the prompt
    response = client.models.generate_content(
        model=model,
        contents=f"Generate an image: {prompt}",
        config=types.GenerateContentConfig(
            response_modalities=["image"],
            temperature=temperature,
            top_p=top_p,
            image_config=types.ImageConfig(
                aspect_ratio=str(aspect_ratio) if aspect_ratio else "1:1",
            ),
        ),
    )

    if not response.candidates:
        raise ValueError("No images were generated")

    download_path = get_download_path(
        os.path.join("images", datetime.now().strftime("%Y-%m-%d"))
    )
    timestamp = int(time.time() * 1000)
    info = {
        "model": model,
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "temperature": temperature,
        "top_p": top_p,
    }
    info_path = os.path.join(download_path, f"{timestamp}.info.json")
    with open(info_path, "w") as f:
        json.dump(info, f, indent=4)

    # Extract images from response
    images: list[Image] = []
    if response.candidates:
        for part in response.candidates[0].content.parts:
            if hasattr(part, "inline_data") and part.inline_data:
                image_data = part.inline_data.data
                mime_type = part.inline_data.mime_type

                # Ensure we have bytes
                if isinstance(image_data, bytes):
                    data = image_data
                else:
                    # If it's base64 string, decode it
                    data = base64.b64decode(image_data)

                # Extract format from mime_type (e.g., "image/png" -> "png")
                fmt = mime_type.split("/")[1] if "/" in mime_type else "png"

                try:
                    idx = len(images)
                    suffix = f"_{idx + 1}" if len(images) > 1 else ""
                    file_path = os.path.join(
                        download_path, f"{timestamp}{suffix}.{fmt}"
                    )
                    with open(file_path, "wb") as f:
                        f.write(data)
                except Exception as e:
                    print(f"Failed to save image: {e}")

                images.append(Image(data=data, format=fmt))

    if not images:
        raise ValueError("No images were generated")

    return images[0]


@mcp.tool()
async def text_to_audio(
    text: Annotated[str, "Text to convert to speech"],
    model: AudioModels = AudioModels.GEMINI_2_5_FLASH_PREVIEW_TTS,
    voice: VoiceName = VoiceName.KORE,
) -> Audio:
    """Generate audio from text using Gemini Flash TTS model."""

    # Configure Gemini API
    # https://ai.google.dev/gemini-api/docs/speech-generation
    client = create_client()

    speech_config = None
    if voice:
        speech_config = types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name=str(voice),
                )
            )
        )

    # Generate audio with the text
    response = client.models.generate_content(
        model=model,
        contents=f"Read this text: {text}",
        config=types.GenerateContentConfig(
            response_modalities=["audio"], speech_config=speech_config
        ),
    )

    # Extract audio from response
    audio_data = None
    # mime_type = None

    if response.candidates:
        for part in response.candidates[0].content.parts:
            if hasattr(part, "inline_data") and part.inline_data:
                audio_data = part.inline_data.data
                # mime_type = part.inline_data.mime_type
                break

    if not audio_data:
        raise ValueError("No audio was generated")

    try:
        # Ensure we have bytes
        if isinstance(audio_data, bytes):
            pcm_data = audio_data
        else:
            # If it's base64 string, decode it
            import base64

            pcm_data = base64.b64decode(audio_data)

        # mime_type audio/L16;codec=pcm;rate=24000
        # ext = mime_type.split("/")[1].split(";")[0]

        # Convert PCM to WAV
        wav_io = io.BytesIO()
        with wave.open(wav_io, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            wf.writeframes(pcm_data)
        wav_data = wav_io.getvalue()

        info = {
            "text": text,
            "model": model,
            "voice": voice,
        }
        download_path = get_download_path(
            os.path.join("audios", datetime.now().strftime("%Y-%m-%d"))
        )
        timestamp = int(time.time() * 1000)
        info_path = os.path.join(download_path, f"{timestamp}.info.json")
        with open(info_path, "w") as f:
            json.dump(info, f, indent=4)

        with open(os.path.join(download_path, f"{timestamp}.wav"), "wb") as f:
            f.write(wav_data)
    except Exception as e:
        print(f"Failed to save audio: {e}")

    return Audio(data=wav_data, format="wav")


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
