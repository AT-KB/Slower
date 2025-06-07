import os
import base64
from django.shortcuts import render
from . import pipeline_proxy


def index(request):
    """Search YouTube videos and display results."""
    keyword = request.GET.get("keyword", "")
    video_url = request.GET.get("video_url", "")
    lang = request.GET.get("lang", "any")
    script_lang = request.GET.get("script_lang", "ja")
    after = request.GET.get("after", "")
    before = request.GET.get("before", "")
    min_views = request.GET.get("min_views", "")
    max_views = request.GET.get("max_views", "")
    min_subs = request.GET.get("min_subs", "")
    max_subs = request.GET.get("max_subs", "")
    min_length = request.GET.get("min_length", "")
    max_length = request.GET.get("max_length", "")
    length = request.GET.get("length", "any")
    max_results = request.GET.get("max_results", "5")

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
                results = pipeline_proxy.search_videos(
                    yt_key,
                    keyword,
                    lang,
                    max_results=int(max_results or 5),
                    video_duration=length,
                    published_after=f"{after}T00:00:00Z" if after else None,
                    published_before=f"{before}T00:00:00Z" if before else None,
                    min_view_count=int(min_views or 0),
                    max_view_count=int(max_views) if max_views else None,
                    min_subscribers=int(min_subs or 0),
                    max_subscribers=int(max_subs) if max_subs else None,
                    min_duration=int(min_length or 0) * 60,
                    max_duration=int(max_length) * 60 if max_length else None,
                )
    context = {
        "results": results,
        "keyword": keyword,
        "video_url": video_url,
        "lang": lang,
        "script_lang": script_lang,
        "after": after,
        "before": before,
        "min_views": min_views,
        "max_views": max_views,
        "min_subs": min_subs,
        "max_subs": max_subs,
        "min_length": min_length,
        "max_length": max_length,
        "length": length,
        "max_results": max_results,
    }
    return render(request, "summary/index.html", context)


def process_video(request, video_id):
    """Run pipeline on selected video."""
    transcript = pipeline_proxy.download_and_transcribe(video_id)
    script_lang = request.GET.get("lang", "ja")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    script = (
        pipeline_proxy.summarize_with_gemini(gemini_key, transcript, lang=script_lang)
        if gemini_key
        else transcript
    )
    audio_b64 = None
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        audio = pipeline_proxy.synthesize_text_to_mp3(script)
        audio_b64 = base64.b64encode(audio).decode("utf-8")
    context = {"video_id": video_id, "script": script, "audio_b64": audio_b64}
    return render(request, "summary/process.html", context)
