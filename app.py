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
lang = st.selectbox("言語", ["ja", "en", "es"])

published_after = st.text_input("公開日以降 (YYYY-MM-DD)", "2022-01-01")
published_before = st.text_input("公開日以前 (YYYY-MM-DD)")
min_views = st.number_input("最小再生回数", min_value=0, value=0)
max_views = st.number_input("最大再生回数", min_value=0, value=0)
min_subs = st.number_input("最小チャンネル登録者数", min_value=0, value=0)
max_subs = st.number_input("最大チャンネル登録者数", min_value=0, value=0)
min_length = st.number_input("最短動画長(秒)", min_value=0, value=0)
max_length = st.number_input("最長動画長(秒)", min_value=0, value=0)
length = st.selectbox("動画の長さ", ["any", "short", "medium", "long"])

if st.button("検索") and YT_KEY:
    with st.spinner("検索中..."):
        results = search_videos(
            YT_KEY,
            keyword,
            lang,
            max_results=20,
            video_duration=length,
            published_after=f"{published_after}T00:00:00Z" if published_after else None,
            published_before=f"{published_before}T00:00:00Z" if published_before else None,
            min_view_count=int(min_views),
            max_view_count=int(max_views) if max_views else None,
            min_subscribers=int(min_subs),
            max_subscribers=int(max_subs) if max_subs else None,
            min_duration=int(min_length),
            max_duration=int(max_length) if max_length else None,
        )

    for idx, vid in enumerate(results, 1):
        st.markdown(f"[{vid['title']}]({vid['url']})")
        if st.button("この動画で生成", key=vid["videoId"]):
            progress = st.progress(0)
            status = st.empty()

            status.write("ダウンロードと文字起こし...")
            transcript = download_and_transcribe(vid["videoId"])
            progress.progress(0.33)

            status.write("Gemini でスクリプト生成...")
            script = summarize_with_gemini(GEMINI_KEY, transcript)
            progress.progress(0.66)
            st.text_area("生成されたスクリプト", script)

            out_lang = st.selectbox("音声言語", ["ja-JP", "en-US", "es-ES"])
            rate = st.slider("読み上げ速度", 0.25, 2.0, 1.0, 0.05)

            status.write("音声合成...")
            audio = synthesize_text_to_mp3(
                script, language_code=out_lang, speaking_rate=rate
            )
            progress.progress(1.0)
            status.write("生成完了！")

            st.audio(audio, format="audio/mp3")
            st.download_button(
                "MP3を保存",
                data=audio,
                file_name=f"{vid['videoId']}.mp3",
                mime="audio/mpeg",
            )
            break
