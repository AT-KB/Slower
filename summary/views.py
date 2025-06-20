import os
import base64
from django.shortcuts import render, redirect
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
    error = ""
    if "search" in request.GET:
        yt_key = os.environ.get("YT_KEY")
        if not yt_key:
            error += "YouTube API key (YT_KEY) is not configured."
        else:
            if video_url:
                vid = pipeline_proxy.extract_video_id(video_url)
                if vid:
                    try:
                        info = pipeline_proxy.get_video_info(yt_key, vid)
                        if info:
                            results = [info]
                        else:
                            error += "Video not found."
                    except Exception as e:
                        results = []
                        error += str(e)
                else:
                    error += "Invalid video URL or ID."
            elif keyword:
                try:
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
                        error += "No videos matched the search criteria."
                except Exception as e:
                    results = []
                    error += str(e)
    error = error.strip()
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
        "error": error if error else None,
    }
    return render(request, "summary/index.html", context)


def process_video(request, video_id):
    """Run pipeline on selected video."""
    errors = []
    steps = []
    transcript = ""
    try:
        transcript = pipeline_proxy.download_and_transcribe(video_id)
        steps.append("transcribed")
    except Exception as e:
        errors.append(str(e))
    script_lang = request.GET.get("lang", "ja")
    audio_lang = request.GET.get("audio", "ja-JP")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    credentials = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not gemini_key:
        errors.append("Gemini API key (GEMINI_API_KEY) is not configured.")
    if not credentials:
        errors.append("Google Cloud credentials are not configured.")

    script = transcript
    if not errors and gemini_key and transcript:
        try:
            script = pipeline_proxy.summarize_with_gemini(
                gemini_key, transcript, lang=script_lang
            )
            steps.append("summarized")
        except Exception as e:
            errors.append(str(e))
    if not errors and gemini_key and script:
        try:
            script = pipeline_proxy.generate_discussion_script(
                gemini_key, script, lang=script_lang
            )
            steps.append("script generated")
        except Exception as e:
            errors.append(str(e))

    audio_b64 = None
    if not errors and credentials and script:
        try:
            audio = pipeline_proxy.synthesize_text_to_mp3(
                script, language_code=audio_lang
            )
            audio_b64 = base64.b64encode(audio).decode("utf-8")
            steps.append("audio created")
        except Exception as e:
            errors.append(str(e))

    context = {
        "video_id": video_id,
        "script": script,
        "audio_b64": audio_b64,
        "error": " ".join(errors) if errors else None,
        "steps": "\n".join(steps) if steps else None,
    }
    return render(request, "summary/process.html", context)


def process_multiple(request):
    """Process multiple videos selected from search results."""
    video_ids = request.POST.getlist("video_ids")
    script_lang = request.POST.get("script_lang", "ja")
    audio_lang = request.POST.get("audio_lang", "ja-JP")

    transcripts = []
    errors = []
    steps = []
    for vid in video_ids:
        try:
            transcripts.append(pipeline_proxy.download_and_transcribe(vid))
            steps.append("transcribed")
        except Exception as e:
            errors.append(str(e))
            break
    combined = "\n".join(transcripts)

    gemini_key = os.environ.get("GEMINI_API_KEY")
    credentials = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not gemini_key:
        errors.append("Gemini API key (GEMINI_API_KEY) is not configured.")
    if not credentials:
        errors.append("Google Cloud credentials are not configured.")

    script = combined
    if not errors and gemini_key and combined:
        try:
            script = pipeline_proxy.summarize_with_gemini(
                gemini_key, combined, lang=script_lang
            )
            steps.append("summarized")
        except Exception as e:
            errors.append(str(e))
    if not errors and gemini_key and script:
        try:
            script = pipeline_proxy.generate_discussion_script(
                gemini_key, script, lang=script_lang
            )
            steps.append("script generated")
        except Exception as e:
            errors.append(str(e))

    audio_b64 = None
    if not errors and credentials and script:
        try:
            audio = pipeline_proxy.synthesize_text_to_mp3(
                script, language_code=audio_lang
            )
            audio_b64 = base64.b64encode(audio).decode("utf-8")
            steps.append("audio created")
        except Exception as e:
            errors.append(str(e))

    context = {
        "video_ids": video_ids,
        "script": script,
        "audio_b64": audio_b64,
        "error": " ".join(errors) if errors else None,
        "steps": "\n".join(steps) if steps else None,
    }
    return render(request, "summary/multi_process.html", context)


# New step-by-step endpoints
def show_process(request, video_id):
    """Display processing page with current session data."""
    context = {
        "video_id": video_id,
        "script": request.session.get("script"),
        "audio_b64": request.session.get("audio_b64"),
        "error": request.session.get("error"),
        "steps": "\n".join(request.session.get("steps", [])) or None,
    }
    return render(request, "summary/process.html", context)


def transcribe_step(request, video_id):
    """Run transcription step."""
    steps = request.session.get("steps", [])
    try:
        transcript = pipeline_proxy.download_and_transcribe(video_id)
        request.session["transcript"] = transcript
        steps.append("transcribed")
        request.session["error"] = ""
    except Exception as e:
        request.session["error"] = str(e)
    request.session["steps"] = steps
    return redirect("show_process", video_id=video_id)


def summarize_step(request, video_id):
    """Run summarization step."""
    steps = request.session.get("steps", [])
    transcript = request.session.get("transcript")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        request.session["error"] = "Gemini API key (GEMINI_API_KEY) is not configured."
    elif not transcript:
        request.session["error"] = "No transcript to summarize."
    else:
        try:
            summary = pipeline_proxy.summarize_with_gemini(
                gemini_key,
                transcript,
                lang=request.GET.get("lang", "ja"),
            )
            request.session["summary"] = summary
            steps.append("summarized")
            request.session["error"] = ""
        except Exception as e:
            request.session["error"] = str(e)
    request.session["steps"] = steps
    return redirect("show_process", video_id=video_id)


def generate_script_step(request, video_id):
    """Create discussion script from summary."""
    steps = request.session.get("steps", [])
    summary = request.session.get("summary")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        request.session["error"] = "Gemini API key (GEMINI_API_KEY) is not configured."
    elif not summary:
        request.session["error"] = "No summary to convert into script."
    else:
        try:
            script = pipeline_proxy.generate_discussion_script(
                gemini_key,
                summary,
                lang=request.GET.get("lang", "ja"),
            )
            request.session["script"] = script
            steps.append("script generated")
            request.session["error"] = ""
        except Exception as e:
            request.session["error"] = str(e)
    request.session["steps"] = steps
    return redirect("show_process", video_id=video_id)


def synthesize_step(request, video_id):
    """Generate MP3 audio from script."""
    steps = request.session.get("steps", [])
    script = request.session.get("script")
    credentials = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not credentials:
        request.session["error"] = "Google Cloud credentials are not configured."
    elif not script:
        request.session["error"] = "No script to synthesize."
    else:
        try:
            audio = pipeline_proxy.synthesize_text_to_mp3(
                script,
                language_code=request.GET.get("audio", "ja-JP"),
            )
            request.session["audio_b64"] = base64.b64encode(audio).decode("utf-8")
            steps.append("audio created")
            request.session["error"] = ""
        except Exception as e:
            request.session["error"] = str(e)
    request.session["steps"] = steps
    return redirect("show_process", video_id=video_id)


def clear_process(request, video_id):
    """Clear session data for a video."""
    for key in ["transcript", "summary", "script", "audio_b64", "steps", "error"]:
        request.session.pop(key, None)
    return redirect("show_process", video_id=video_id)
