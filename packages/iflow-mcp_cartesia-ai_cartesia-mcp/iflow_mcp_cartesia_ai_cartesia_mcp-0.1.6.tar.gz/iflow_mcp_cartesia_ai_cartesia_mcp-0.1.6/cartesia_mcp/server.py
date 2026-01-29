"""
Cartesia MCP Server
"""

import os
import typing
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from cartesia_mcp.custom_types import GeneratedAudioResult, DeleteVoiceResult
from cartesia import Cartesia
from cartesia.core.pagination import SyncPager
from cartesia.voices.requests import LocalizeDialectParams
from cartesia.voices.types import VoiceMetadata, GenderPresentation, Gender, CloneMode, Voice
from cartesia.voice_changer.types import OutputFormatContainer
from cartesia.tts.types import SupportedLanguage, RawEncoding
from cartesia.tts.requests import OutputFormatParams, TtsRequestVoiceSpecifierParams
from cartesia.core.request_options import RequestOptions

from cartesia_mcp.utils import create_output_file

load_dotenv()

CARTESIA_API_KEY = os.getenv("CARTESIA_API_KEY")

if not CARTESIA_API_KEY:
    raise ValueError("CARTESIA_API_KEY is required")

OUTPUT_DIRECTORY = os.getenv("OUTPUT_DIRECTORY", ".")

client = Cartesia(api_key=CARTESIA_API_KEY)
mcp = FastMCP("Cartesia")

@mcp.tool(description="""
        Convert text to speech using Cartesia's text-to-speech API.

        Parameters
        ----------
        transcript : str
            The text to convert to speech

        voice : dict
            Voice specification parameters

        output_format : dict
            Output format parameters (container, encoding, sample_rate, etc.)

        model_id : str
            The ID of the model to use for the generation (default: "sonic-3")

        language : typing.Optional[str]
            The language for speech synthesis

        duration : typing.Optional[float]
            The maximum duration of the audio in seconds

        request_options : typing.Optional[dict]
            Request-specific configuration options

          """)
def text_to_speech(
    transcript: str,
    voice: dict,
    output_format: dict,
    model_id: typing.Optional[str] = "sonic-3",
    language: typing.Optional[str] = None,
    duration: typing.Optional[float] = None,
    request_options: typing.Optional[dict] = None,
) -> GeneratedAudioResult:
    result = client.tts.bytes(transcript=transcript,
                            voice=voice,
                            output_format=output_format,
                            model_id=model_id,
                            language=language,
                            duration=duration,
                            request_options=request_options)

    output_file = create_output_file(OUTPUT_DIRECTORY, "text_to_speech",
                                        output_format["container"])

    audio_bytes = b"".join(result)
    with output_file.open("wb") as f:
        f.write(audio_bytes)

        return GeneratedAudioResult(file_path=str(output_file))


@mcp.tool(description="""
        Generate audio that smoothly connects two existing audio segments.

        **The cost is 1 credit per character of the infill text plus a fixed cost of 300 credits.**

        At least one of `left_audio` or `right_audio` must be provided.

        Parameters
        ----------
        language : str
            The language of the transcript

        transcript : str
            The infill text to generate

        voice_id : str
            The ID of the voice to use for generating audio

        output_format_container : str
            The format of the output audio

        output_format_sample_rate : int
            The sample rate of the output audio

        output_format_encoding : typing.Optional[str]
            Required for `raw` and `wav` containers.

        output_format_bit_rate : typing.Optional[int]
            Required for `mp3` containers.

        left_audio_file_path : typing.Optional[str]
            The absolute path to the left audio file to infill.

        right_audio_file_path : typing.Optional[str]
            The absolute path to the right audio file to infill.

        request_options : typing.Optional[dict]
            Request-specific configuration.
          """)
def infill(
    language: str,
    transcript: str,
    voice_id: str,
    output_format_container: str,
    output_format_sample_rate: int,
    output_format_encoding: typing.Optional[str] = None,
    output_format_bit_rate: typing.Optional[int] = None,
    left_audio_file_path: typing.Optional[str] = None,
    right_audio_file_path: typing.Optional[str] = None,
    request_options: typing.Optional[dict] = None,
) -> GeneratedAudioResult:
    left_audio = open(left_audio_file_path,
                        "rb") if left_audio_file_path else None
    right_audio = open(right_audio_file_path,
                        "rb") if right_audio_file_path else None

    result = client.infill.bytes(
        model_id="sonic-3",
        language=language,
        transcript=transcript,
        voice_id=voice_id,
        output_format_container=output_format_container,
        output_format_sample_rate=output_format_sample_rate,
        output_format_encoding=output_format_encoding,
        output_format_bit_rate=output_format_bit_rate,
        left_audio=left_audio,
        right_audio=right_audio,
        request_options=request_options)

    output_file = create_output_file(OUTPUT_DIRECTORY, "infill",
                                        output_format_container)

    audio_bytes = b"".join(result)
    with output_file.open("wb") as f:
        f.write(audio_bytes)

    return GeneratedAudioResult(file_path=str(output_file))


@mcp.tool(description="""
        Takes an audio file of speech, and returns an audio file of speech spoken with the same intonation, but with a different voice.

        Parameters
        ----------
        file_path : str
            The absolute path to the audio file to change.

        voice_id : str
            The ID of the voice to use

        output_format_container : str
            The container format for output audio

        output_format_sample_rate : int
            The sample rate for output audio

        output_format_encoding : typing.Optional[str]
            Required for `raw` and `wav` containers.

        output_format_bit_rate : typing.Optional[int]
            Required for `mp3` containers.

        request_options : typing.Optional[dict]
            Request-specific configuration.
          
        """)
def voice_change(
    file_path: str,
    voice_id: str,
    output_format_container: str,
    output_format_sample_rate: int,
    output_format_encoding: typing.Optional[str] = None,
    output_format_bit_rate: typing.Optional[int] = None,
    request_options: typing.Optional[dict] = None,
) -> GeneratedAudioResult:
    result = client.voice_changer.bytes(
        clip=open(file_path, "rb"),
        voice_id=voice_id,
        output_format_container=output_format_container,
        output_format_sample_rate=output_format_sample_rate,
        output_format_encoding=output_format_encoding,
        output_format_bit_rate=output_format_bit_rate,
        request_options=request_options)

    output_file = create_output_file(OUTPUT_DIRECTORY, "voice_change",
                                        output_format_container)

    audio_bytes = b"".join(result)
    with output_file.open("wb") as f:
        f.write(audio_bytes)

    return GeneratedAudioResult(file_path=str(output_file))

@mcp.tool(description="""
        Create a new voice from an existing voice localized to a new language and dialect.

        Parameters
        ----------
        voice_id : str
            The ID of the voice to localize.

        name : str
            The name of the new localized voice.

        description : str
            The description of the new localized voice.

        language : str
            The target language

        original_speaker_gender : str
            The gender of the original speaker

        dialect : typing.Optional[dict]
            Dialect parameters for localization

        request_options : typing.Optional[dict]
            Request-specific configuration.
        """)
def localize_voice(
    voice_id: str,
    name: str,
    description: str,
    language: str,
    original_speaker_gender: str,
    dialect: typing.Optional[dict] = None,
    request_options: typing.Optional[dict] = None,
) -> dict:
    result = client.voices.localize(
        voice_id=voice_id,
        name=name,
        description=description,
        language=language,
        original_speaker_gender=original_speaker_gender,
        dialect=dialect,
        request_options=request_options)
    return dict(result)


@mcp.tool(description="""
        Delete a voice by its ID.

        Parameters
        ----------
        voice_id : str
            The ID of the voice to delete.

        request_options : typing.Optional[dict]
            Request-specific configuration.
        """)
def delete_voice(
    voice_id: str,
    request_options: typing.Optional[dict] = None
) -> DeleteVoiceResult:
    result = client.voices.delete(id=voice_id,
                                request_options=request_options)
    return DeleteVoiceResult(success=True)


@mcp.tool(description="""
        Get a voice by its ID.

        Parameters
        ----------
        voice_id : str
            The ID of the voice to get.

        request_options : typing.Optional[dict]
            Request-specific configuration.
        """)
def get_voice(
        voice_id: str,
        request_options: typing.Optional[dict] = None
) -> dict:
    result = client.voices.get(id=voice_id, request_options=request_options)
    return dict(result)


@mcp.tool(description="""
        Update a voice's name and description.

        Parameters
        ----------
        voice_id : str
            The ID of the voice to update.

        name : str
            The new name of the voice.

        description : str
            The new description of the voice.

        request_options : typing.Optional[dict]
            Request-specific configuration.
        """)
def update_voice(
        voice_id: str,
        name: str,
        description: str,
        request_options: typing.Optional[dict] = None
) -> dict:
    result = client.voices.update(id=voice_id,
                                name=name,
                                description=description,
                                request_options=request_options)
    return dict(result)

@mcp.tool(description="""
        Clone a voice from an audio clip.

        Parameters
        ----------
        file_path : str
            The absolute path to the audio file to clone.

        name : str
            The name of the voice.

        language : str
            The language of the voice.

        mode : str
            Tradeoff between similarity and stability. Options: "similarity" or "stability"

        description : typing.Optional[str]
            A description for the voice.

        request_options : typing.Optional[dict]
            Request-specific configuration.
        """)
def clone_voice(
    file_path: str,
    name: str,
    language: str,
    mode: str,
    description: typing.Optional[str] = None,
    request_options: typing.Optional[dict] = None,
) -> dict:
    result = client.voices.clone(clip=open(file_path, "rb"),
                                name=name,
                                language=language,
                                mode=mode,
                                description=description,
                                request_options=request_options)
    return dict(result)


@mcp.tool(description="""
        List available voices with optional filtering.

        Parameters
        ----------
        limit : typing.Optional[int]
            The number of Voices to return per page, ranging between 1 and 100.

        starting_after : typing.Optional[str]
            A cursor to use in pagination.

        ending_before : typing.Optional[str]
            A cursor to use in pagination.

        is_owner : typing.Optional[bool]
            Whether to only return voices owned by the current user.

        is_starred : typing.Optional[bool]
            Whether to only return starred voices.

        gender : typing.Optional[str]
            The gender presentation of the voices to return.

        request_options : typing.Optional[dict]
            Request-specific configuration.
        """)
def list_voices(
    limit: typing.Optional[int] = 10,
    starting_after: typing.Optional[str] = None,
    ending_before: typing.Optional[str] = None,
    is_owner: typing.Optional[bool] = None,
    is_starred: typing.Optional[bool] = None,
    gender: typing.Optional[str] = None,
    request_options: typing.Optional[dict] = None,
) -> dict:
    result = client.voices.list(limit=limit,
                                gender=gender,
                                is_owner=is_owner,
                                is_starred=is_starred,
                                starting_after=starting_after,
                                ending_before=ending_before,
                                request_options=request_options)
    return {"voices": [dict(v) for v in result]}

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()