"""Lightweight wrappers that import pipeline functions lazily."""

from importlib import import_module


def _get_pipeline():
    return import_module("pipeline")


def search_videos(*args, **kwargs):
    return _get_pipeline().search_videos(*args, **kwargs)


def extract_video_id(*args, **kwargs):
    return _get_pipeline().extract_video_id(*args, **kwargs)


def get_video_info(*args, **kwargs):
    return _get_pipeline().get_video_info(*args, **kwargs)


def download_and_transcribe(*args, **kwargs):
    return _get_pipeline().download_and_transcribe(*args, **kwargs)


def summarize_with_gemini(*args, **kwargs):
    return _get_pipeline().summarize_with_gemini(*args, **kwargs)


def synthesize_text_to_mp3(*args, **kwargs):
    return _get_pipeline().synthesize_text_to_mp3(*args, **kwargs)
