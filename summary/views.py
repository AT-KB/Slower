import os
import base64
from django.shortcuts import render
from . import pipeline_proxy


def index(request):
    """Search YouTube videos and display results."""
    keyword = request.GET.get("keyword", "")
    video_url = request.GET.get("video_url", "")
    results = []
    if "search" in request.GET:
        yt_key = os.environ.get("YT_KEY")
        if yt_key:
            if video_url:
                vid = pipeline_proxy.extract_video_id(video_url)
                if vid:
                    info = pipeline_proxy.get_video_info(yt_key, vid)
                    if info:
                        results = [info]
            elif keyword:
                results = pipeline_proxy.search_videos(yt_key, keyword, "any")
    context = {"results": results, "keyword": keyword, "video_url": video_url}
    return render(request, "summary/index.html", context)


def process_video(request, video_id):
    """Run pipeline on selected video."""
    transcript = pipeline_proxy.download_and_transcribe(video_id)
    gemini_key = os.environ.get("GEMINI_API_KEY")
    script = (
        pipeline_proxy.summarize_with_gemini(gemini_key, transcript)
        if gemini_key
        else transcript
    )
    audio_b64 = None
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        audio = pipeline_proxy.synthesize_text_to_mp3(script)
        audio_b64 = base64.b64encode(audio).decode("utf-8")
    context = {"video_id": video_id, "script": script, "audio_b64": audio_b64}
    return render(request, "summary/process.html", context)
