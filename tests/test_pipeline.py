import sys
import types
import os
root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root not in sys.path:
    sys.path.insert(0, root)

# Stub heavy external modules before importing pipeline

ga = types.ModuleType('googleapiclient')
discovery = types.ModuleType('googleapiclient.discovery')
discovery.build = lambda *args, **kwargs: None

ga.discovery = discovery
sys.modules['googleapiclient'] = ga
sys.modules['googleapiclient.discovery'] = discovery

# google.cloud.texttospeech_v1 stub
gc = types.ModuleType('google.cloud')
tts = types.ModuleType('google.cloud.texttospeech_v1')
class Dummy:
    pass

tts.TextToSpeechClient = Dummy
tts.SynthesisInput = Dummy
tts.VoiceSelectionParams = Dummy
tts.AudioConfig = Dummy
tts.AudioEncoding = types.SimpleNamespace(MP3=1)

gc.texttospeech_v1 = tts
sys.modules['google.cloud'] = gc
sys.modules['google.cloud.texttospeech_v1'] = tts

# Other stubs
sys.modules['yt_dlp'] = types.ModuleType('yt_dlp')
sys.modules['whisper'] = types.ModuleType('whisper')
google_pkg = types.ModuleType('google')
genai = types.ModuleType('google.generativeai')
google_pkg.generativeai = genai
sys.modules['google'] = google_pkg
sys.modules['google.generativeai'] = genai

import pipeline


def test_extract_video_id_direct():
    vid = 'dQw4w9WgXcQ'
    assert pipeline.extract_video_id(vid) == vid


def test_extract_video_id_short_url():
    url = 'https://youtu.be/dQw4w9WgXcQ'
    assert pipeline.extract_video_id(url) == 'dQw4w9WgXcQ'


def test_extract_video_id_watch_url():
    url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
    assert pipeline.extract_video_id(url) == 'dQw4w9WgXcQ'


def test_iso_duration_to_seconds():
    assert pipeline._iso_duration_to_seconds('PT15M33S') == 15 * 60 + 33
    assert pipeline._iso_duration_to_seconds('PT2H') == 2 * 3600
    assert pipeline._iso_duration_to_seconds('PT1H2M3S') == 3600 + 2 * 60 + 3
    assert pipeline._iso_duration_to_seconds('PT45S') == 45
    assert pipeline._iso_duration_to_seconds('invalid') == 0
