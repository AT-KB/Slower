"""Utility helpers for YouTube search, transcription, summarization,
and audio synthesis."""

import os
from typing import List, Optional, Dict
import re
from urllib.parse import urlparse, parse_qs

from googleapiclient.discovery import build
from google.cloud import texttospeech_v1 as texttospeech
import yt_dlp
import whisper
import google.generativeai as genai


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


def download_and_transcribe(
    video_id: str, *, out_dir: str = "downloads", whisper_model: str = "base"
) -> str:
    """Download audio from YouTube and transcribe with Whisper."""
    os.makedirs(out_dir, exist_ok=True)
    ydl_opts = {
        "outtmpl": os.path.join(out_dir, f"{video_id}.%(ext)s"),
        "format": "bestaudio/best",
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"https://youtu.be/{video_id}", download=True)
        file_path = ydl.prepare_filename(info)

    model = whisper.load_model(whisper_model)
    try:
        result = model.transcribe(file_path)
    finally:
        try:
            os.remove(file_path)
        except OSError:
            pass
    return result["text"]


def summarize_with_gemini(api_key: str, text: str, *, lang: str = "ja") -> str:
    """Summarize transcript in the specified language using Gemini."""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-pro")
    prompt = f"次の内容を{lang}でゆっくり解説してください:\n{text}"
    response = model.generate_content(prompt)
    return response.text


def generate_discussion_script(api_key: str, summary: str, *, lang: str = "ja") -> str:
    """Create a two-person discussion script from summary using Gemini."""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-pro")
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
