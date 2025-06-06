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
    audio_lang = request.GET.get("audio_lang", "ja-JP")
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
    error = None
    if "search" in request.GET:
        yt_key = os.environ.get("YT_KEY")
        if not yt_key:
            error = "YouTube API key (YT_KEY) is not configured."
        else:
            if video_url:
                vid = pipeline_proxy.extract_video_id(video_url)
                if vid:
                    info = pipeline_proxy.get_video_info(yt_key, vid)
                    if info:
                        results = [info]
                    else:
                        error = "Video not found."
                else:
                    error = "Invalid video URL or ID."
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
                if not results:
                    error = "No videos matched the search criteria."
    context = {
        "results": results,
        "keyword": keyword,
        "video_url": video_url,
        "lang": lang,
        "script_lang": script_lang,
        "audio_lang": audio_lang,
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
        "error": error,
    }
    return render(request, "summary/index.html", context)


def process_video(request, video_id):
    """Run pipeline on selected video."""
    transcript = pipeline_proxy.download_and_transcribe(video_id)
    script_lang = request.GET.get("lang", "ja")
    audio_lang = request.GET.get("audio", "ja-JP")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    credentials = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    errors = []
    if not gemini_key:
        errors.append("Gemini API key (GEMINI_API_KEY) is not configured.")
    if not credentials:
        errors.append("Google Cloud credentials are not configured.")

    script = (
        pipeline_proxy.summarize_with_gemini(gemini_key, transcript, lang=script_lang)
        if gemini_key
        else transcript
    )
    script = (
        pipeline_proxy.generate_discussion_script(gemini_key, script, lang=script_lang)
        if gemini_key
        else script
    )

    audio_b64 = None
    if credentials:
        audio = pipeline_proxy.synthesize_text_to_mp3(
            script, language_code=audio_lang
        )
        audio_b64 = base64.b64encode(audio).decode("utf-8")

    context = {
        "video_id": video_id,
        "script": script,
        "audio_b64": audio_b64,
        "error": " ".join(errors) if errors else None,
    }
    return render(request, "summary/process.html", context)


def process_multiple(request):
    """Process multiple videos selected from search results."""
    video_ids = request.POST.getlist("video_ids")
    script_lang = request.POST.get("script_lang", "ja")
    audio_lang = request.POST.get("audio_lang", "ja-JP")

    transcripts = []
    for vid in video_ids:
        transcripts.append(pipeline_proxy.download_and_transcribe(vid))
    combined = "\n".join(transcripts)

    gemini_key = os.environ.get("GEMINI_API_KEY")
    credentials = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    errors = []
    if not gemini_key:
        errors.append("Gemini API key (GEMINI_API_KEY) is not configured.")
    if not credentials:
        errors.append("Google Cloud credentials are not configured.")

    script = (
        pipeline_proxy.summarize_with_gemini(gemini_key, combined, lang=script_lang)
        if gemini_key
        else combined
    )
    script = (
        pipeline_proxy.generate_discussion_script(gemini_key, script, lang=script_lang)
        if gemini_key
        else script
    )

    audio_b64 = None
    if credentials:
        audio = pipeline_proxy.synthesize_text_to_mp3(
            script, language_code=audio_lang
        )
        audio_b64 = base64.b64encode(audio).decode("utf-8")

    context = {
        "video_ids": video_ids,
        "script": script,
        "audio_b64": audio_b64,
        "error": " ".join(errors) if errors else None,
    }
    return render(request, "summary/multi_process.html", context)
