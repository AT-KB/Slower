# YouTube ゆっくり解説メーカー

このプロジェクトは、YouTube 動画を検索して選択し、その内容を文字起こし・要約した後、日本語音声を生成する Streamlit アプリです。初心者の方でも `streamlit run app.py` を実行するだけで試せます。

## 必要なもの
- YouTube Data API キー (`YT_KEY`)
- Google Gemini API キー (`GEMINI_API_KEY`)
- Google Cloud Text-to-Speech の認証情報

これらの情報は環境変数として設定してください。

## セットアップ
1. 依存パッケージをインストールします。
   ```bash
   pip install -r requirements.txt
