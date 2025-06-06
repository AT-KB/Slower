"""Streamlit app that searches YouTube and generates narrated summaries."""

import streamlit as st
from pipeline import (
    search_videos,
    download_and_transcribe,
    summarize_with_gemini,
    synthesize_text_to_mp3,
)
import os
import calendar
from datetime import date

st.title("YouTube ゆっくり解説メーカー")

# API keys from environment variables
YT_KEY = os.environ.get("YT_KEY")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

if not YT_KEY or not GEMINI_KEY:
    st.info("環境変数 YT_KEY と GEMINI_API_KEY を設定してください。")

keyword = st.text_input("キーワードを入力")
lang = st.selectbox("言語", ["ja", "en", "es"])

# 公開日の範囲
current_year = date.today().year
years = list(range(2015, current_year + 1))
months = list(range(1, 13))

col1, col2 = st.columns(2)
with col1:
    after_year = st.selectbox("公開年以降", years, index=years.index(2022) if 2022 in years else 0)
    after_month = st.selectbox("公開月以降", months, index=0)
with col2:
    before_year = st.selectbox("公開年以前", years, index=len(years) - 1)
    before_month = st.selectbox("公開月以前", months, index=date.today().month - 1)

published_after = f"{after_year}-{after_month:02d}-01"
end_day = calendar.monthrange(before_year, before_month)[1]
published_before = f"{before_year}-{before_month:02d}-{end_day:02d}"


# 再生回数の範囲
views = st.slider("再生回数の範囲", 1000, 3000000, (0, 0), step=1000)
min_views, max_views = views


# チャンネル登録者数の範囲
subs = st.slider("チャンネル登録者数の範囲", 1000, 3000000, (0, 0), step=1000)
min_subs, max_subs = subs


# 動画長(秒)の範囲
video_len = st.slider("動画長(秒)の範囲", 0, 10_000, (0, 0), step=10)
min_length, max_length = video_len

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
            total_steps = 3

            status.write("ステップ1/3: ダウンロードと文字起こし")
            transcript = download_and_transcribe(vid["videoId"])
            progress.progress(1 / total_steps)

            status.write("ステップ2/3: Gemini でスクリプト生成")
            if not GEMINI_KEY:
                st.warning(
                    "環境変数 GEMINI_API_KEY が設定されていないため、スクリプト生成をスキップします。"
                )
                progress.progress(1.0)
                status.write("完了")
                break

            script = summarize_with_gemini(GEMINI_KEY, transcript)
            progress.progress(2 / total_steps)
            st.text_area("生成されたスクリプト", script)

            out_lang = st.selectbox("音声言語", ["ja-JP", "en-US", "es-ES"])
            rate = st.slider("読み上げ速度", 0.25, 2.0, 1.0, 0.05)

            status.write("ステップ3/3: 音声合成")
            audio = synthesize_text_to_mp3(
                script, language_code=out_lang, speaking_rate=rate
            )
            progress.progress(3 / total_steps)
            status.write("ステップ3/3: 音声合成完了！")

            st.audio(audio, format="audio/mp3")
            st.download_button(
                "MP3を保存",
                data=audio,
                file_name=f"{vid['videoId']}.mp3",
                mime="audio/mpeg",
            )
            break
