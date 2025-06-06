import os
import subprocess
from typing import List

from googleapiclient.discovery import build
from google.cloud import texttospeech_v1 as texttospeech
import yt_dlp
import whisper
import google.generativeai as genai


def search_videos(api_key: str, keyword: str, lang: str, *, max_results: int = 5,
                  video_duration: str = "medium",
                  published_after: str = "2022-01-01T00:00:00Z") -> List[dict]:
    """Search YouTube videos and return list of results."""
    youtube = build("youtube", "v3", developerKey=api_key)
    response = youtube.search().list(
        part="snippet",
        q=keyword,
        type="video",
        relevanceLanguage=lang,
        videoDuration=video_duration,
        videoLicense="creativeCommon",
        publishedAfter=published_after,
        maxResults=max_results,
    ).execute()

    results = []
    for item in response.get("items", []):
        vid = item["id"]["videoId"]
        title = item["snippet"]["title"]
        results.append({
            "videoId": vid,
            "title": title,
            "url": f"https://youtu.be/{vid}",
        })
    return results


def download_and_transcribe(video_id: str, *, out_dir: str = "downloads",
                             whisper_model: str = "base") -> str:
    """Download audio from YouTube and transcribe with Whisper."""
    os.makedirs(out_dir, exist_ok=True)
    ydl_opts = {"outtmpl": os.path.join(out_dir, f"{video_id}.%(ext)s"), "format": "bestaudio/best"}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"https://youtu.be/{video_id}", download=True)
        file_path = ydl.prepare_filename(info)

    model = whisper.load_model(whisper_model)
    result = model.transcribe(file_path)
    return result["text"]


def summarize_with_gemini(api_key: str, text: str) -> str:
    """Summarize transcript in Japanese using Gemini."""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-pro")
    prompt = f"次の内容を日本語でゆっくり解説してください:\n{text}"
    response = model.generate_content(prompt)
    return response.text


def synthesize_text_to_mp3(text: str, *, voice: str = "ja-JP-Neural2-B") -> bytes:
    """Return MP3 audio bytes from given Japanese text."""
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice_params = texttospeech.VoiceSelectionParams(
        language_code="ja-JP",
        name=voice,
    )
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
    response = client.synthesize_speech(
        request={"input": synthesis_input, "voice": voice_params, "audio_config": audio_config}
    )
    return response.audio_content
