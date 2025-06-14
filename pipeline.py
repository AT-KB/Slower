"""Utility helpers for YouTube search, transcription, summarization,
and audio synthesis."""

import os
import threading
import gc
from typing import List, Optional, Dict
import re
from urllib.parse import urlparse, parse_qs

from googleapiclient.discovery import build
from google.cloud import texttospeech_v1 as texttospeech
import yt_dlp
import whisper

import google.generativeai as genai

_MODEL_CACHE: Dict[str, object] = {}
_MODEL_CACHE_LOCK = threading.Lock()


def _get_whisper_model(name: str):
    """Return cached Whisper model or load and store it.

    The backend is selected via the ``WHISPER_BACKEND`` environment variable
    (``"openai"`` by default). When set to ``"faster"``, ``faster_whisper`` is
    used instead of ``openai-whisper``.
    """
    backend = os.getenv("WHISPER_BACKEND", "openai").lower()
    compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
    use_cache = os.getenv("WHISPER_CACHE", "1") != "0"
    cache_key = f"{backend}:{compute_type}:{name}" if backend == "faster" else f"{backend}:{name}"
    with _MODEL_CACHE_LOCK:
        model = _MODEL_CACHE.get(cache_key) if use_cache else None
        if model is None:
            if backend == "faster":
                from faster_whisper import WhisperModel

                model = WhisperModel(name, compute_type=compute_type)
            else:
                model = whisper.load_model(name)
            if use_cache:
                _MODEL_CACHE[cache_key] = model
        return model




def _iso_duration_to_seconds(duration: str) -> int:
    """Convert ISO 8601 duration to seconds."""
    pattern = re.compile(
        r"PT(?:(?P<h>\d+)H)?(?:(?P<m>\d+)M)?(?:(?P<s>\d+)S)?",
        re.I,
    )
    match = pattern.match(duration)
    if not match:
        return 0
    hours = int(match.group("h") or 0)
    minutes = int(match.group("m") or 0)
    seconds = int(match.group("s") or 0)
    return hours * 3600 + minutes * 60 + seconds


def extract_video_id(url: str) -> Optional[str]:
    """Extract a YouTube video ID from a URL or return None."""
    if not url:
        return None

    # direct video id
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url):
        return url

    parsed = urlparse(url)
    host = parsed.hostname or ""

    if host in {"youtu.be"}:
        vid = parsed.path.lstrip("/")
        return vid if vid else None

    if host.endswith("youtube.com"):
        if parsed.path == "/watch":
            qs = parse_qs(parsed.query)
            return qs.get("v", [None])[0]
        segments = parsed.path.split("/")
        if len(segments) >= 2 and segments[1] in {"embed", "shorts"}:
            return segments[2] if len(segments) > 2 else None

    return None


def get_video_info(api_key: str, video_id: str) -> Optional[dict]:
    """Retrieve basic video information by ID."""
    youtube = build("youtube", "v3", developerKey=api_key)
    resp = youtube.videos().list(part="snippet", id=video_id).execute()
    items = resp.get("items", [])
    if not items:
        return None
    title = items[0]["snippet"].get("title", "")
    return {
        "videoId": video_id,
        "title": title,
        "url": f"https://youtu.be/{video_id}",
    }


def search_videos(
    api_key: str,
    keyword: str,
    lang: str,
    *,
    max_results: int = 5,
    video_duration: str = "any",
    published_after: Optional[str] = None,
    published_before: Optional[str] = None,
    min_view_count: int = 0,
    max_view_count: Optional[int] = None,
    min_subscribers: int = 0,
    max_subscribers: Optional[int] = None,
    min_duration: int = 0,
    max_duration: Optional[int] = None,
) -> List[dict]:
    """Search YouTube videos and return list of results filtered by criteria.

    Each result dictionary contains ``videoId``, ``title``, ``url``,
    ``viewCount`` and ``subscriberCount``.
    """
    youtube = build("youtube", "v3", developerKey=api_key)

    search_params: Dict[str, str] = {
        "part": "snippet",
        "q": keyword,
        "type": "video",
        "videoLicense": "creativeCommon",
        "maxResults": 50,
    }
    if lang != "any":
        search_params["relevanceLanguage"] = lang
    if video_duration:
        search_params["videoDuration"] = video_duration
    if published_after:
        search_params["publishedAfter"] = published_after
    if published_before:
        search_params["publishedBefore"] = published_before

    response = youtube.search().list(**search_params).execute()

    video_ids = [item["id"]["videoId"] for item in response.get("items", [])]
    if not video_ids:
        return []

    details = (
        youtube.videos()
        .list(
            part="contentDetails,statistics,snippet",
            id=",".join(video_ids),
        )
        .execute()
    )

    channel_ids = list(
        {item["snippet"]["channelId"] for item in details.get("items", [])}
    )
    channel_stats: Dict[str, int] = {}
    for i in range(0, len(channel_ids), 50):
        ch_resp = (
            youtube.channels()
            .list(
                part="statistics",
                id=",".join(channel_ids[i : i + 50]),  # noqa: E203
            )
            .execute()
        )
        for ch in ch_resp.get("items", []):
            count = int(ch["statistics"].get("subscriberCount", 0))
            channel_stats[ch["id"]] = count

    results = []
    for item in details.get("items", []):
        vid = item["id"]
        title = item["snippet"]["title"]
        url = f"https://youtu.be/{vid}"
        stats = item.get("statistics", {})
        views = int(stats.get("viewCount", 0))
        channel_id = item["snippet"].get("channelId", "")
        subs = channel_stats.get(channel_id, 0)
        duration = _iso_duration_to_seconds(item["contentDetails"]["duration"])

        if views < min_view_count:
            continue
        if max_view_count is not None and views > max_view_count:
            continue
        if subs < min_subscribers:
            continue
        if max_subscribers is not None and subs > max_subscribers:
            continue
        if duration < min_duration:
            continue
        if max_duration is not None and duration > max_duration:
            continue

        results.append(
            {
                "videoId": vid,
                "title": title,
                "url": url,
                "viewCount": views,
                "subscriberCount": subs,
            }
        )
        if len(results) >= max_results:
            break

    return results


def download_and_transcribe(video_id: str, *, out_dir: str = "downloads") -> str:
    """Download audio from YouTube and transcribe with Whisper.

    The model name is read from the ``WHISPER_MODEL`` environment variable
    (default ``"tiny"``).
    """
    os.makedirs(out_dir, exist_ok=True)
    model_name = os.getenv("WHISPER_MODEL", "tiny")
    cookies = os.getenv("YTDLP_COOKIES")
    ydl_opts = {
        "outtmpl": os.path.join(out_dir, f"{video_id}.%(ext)s"),
        "format": "bestaudio/best",
    }

    # Use cookies for age-restricted or authenticated videos
    if cookies and os.path.exists(cookies):
        ydl_opts["cookiefile"] = cookies
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"https://youtu.be/{video_id}", download=True)
        file_path = ydl.prepare_filename(info)

    backend = os.getenv("WHISPER_BACKEND", "openai").lower()
    compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
    use_cache = os.getenv("WHISPER_CACHE", "1") != "0"
    model = _get_whisper_model(model_name)
    try:
        if backend == "faster":
            segments, _info = model.transcribe(file_path)
            result_text = "".join(seg.text for seg in segments)
        else:
            result = model.transcribe(file_path)
            result_text = result["text"]
    finally:
        try:
            os.remove(file_path)
        except OSError:
            pass
        if not use_cache:
            cache_key = (
                f"{backend}:{compute_type}:{model_name}"
                if backend == "faster"
                else f"{backend}:{model_name}"
            )
            with _MODEL_CACHE_LOCK:
                _MODEL_CACHE.pop(cache_key, None)
            del model
            gc.collect()
    return result_text


def summarize_with_gemini(api_key: str, text: str, *, lang: str = "ja") -> str:
    """Summarize transcript in the specified language using Gemini."""
    genai.configure(api_key=api_key)
    model_name = os.getenv("GEMINI_MODEL", "models/gemini-pro")
    model = genai.GenerativeModel(model_name)
    prompt = f"次の内容を{lang}でゆっくり解説してください:\n{text}"
    response = model.generate_content(prompt)
    return response.text


def generate_discussion_script(api_key: str, summary: str, *, lang: str = "ja") -> str:
    """Create a two-person discussion script from summary using Gemini."""
    genai.configure(api_key=api_key)
    model_name = os.getenv("GEMINI_MODEL", "models/gemini-pro")
    model = genai.GenerativeModel(model_name)
    prompt = (
        f"以下の要約をもとに、登場人物AとBが交互に解説する台本を{lang}で書いてください。\n"
        f"{summary}"
    )
    response = model.generate_content(prompt)
    return response.text


def synthesize_text_to_mp3(
    text: str,
    *,
    language_code: str = "ja-JP",
    voice: Optional[str] = None,
    speaking_rate: float = 1.0,
) -> bytes:
    """Return MP3 audio bytes from given text."""
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)

    default_voices = {
        "ja-JP": "ja-JP-Neural2-B",
        "en-US": "en-US-Neural2-J",
        "es-ES": "es-ES-Neural2-B",
    }
    voice_params = texttospeech.VoiceSelectionParams(
        language_code=language_code,
        name=voice or default_voices.get(language_code, "ja-JP-Neural2-B"),
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=speaking_rate,
    )
    response = client.synthesize_speech(
        request={
            "input": synthesis_input,
            "voice": voice_params,
            "audio_config": audio_config,
        }
    )
    return response.audio_content
