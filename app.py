import streamlit as st
from pipeline import (
    search_videos,
    download_and_transcribe,
    summarize_with_gemini,
    synthesize_text_to_mp3,
)
import os

st.title("YouTube ゆっくり解説メーカー")

# API keys from environment variables
YT_KEY = os.environ.get("YT_KEY")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

if not YT_KEY or not GEMINI_KEY:
    st.info("環境変数 YT_KEY と GEMINI_API_KEY を設定してください。")

keyword = st.text_input("キーワードを入力")
lang = st.selectbox("言語", ["en", "ja", "es", "fr"])
length = st.selectbox("動画の長さ", ["short", "medium", "long"]) 

if st.button("検索") and YT_KEY:
    with st.spinner("検索中..."):
        results = search_videos(YT_KEY, keyword, lang, video_duration=length)

    for idx, vid in enumerate(results, 1):
        if st.button(vid["title"], key=idx):
            with st.spinner("ダウンロードと文字起こし..."):
                transcript = download_and_transcribe(vid["videoId"])

            with st.spinner("Gemini でスクリプト生成..."):
                script = summarize_with_gemini(GEMINI_KEY, transcript)
                st.text_area("生成されたスクリプト", script)

            with st.spinner("音声合成..."):
                audio = synthesize_text_to_mp3(script)
            st.audio(audio, format="audio/mp3")
            st.download_button(
                label="MP3を保存",
                data=audio,
                file_name=f"{vid['videoId']}.mp3",
                mime="audio/mpeg",
            )
            break
