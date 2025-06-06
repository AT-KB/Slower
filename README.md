# YouTube ゆっくり解説メーカー

このプロジェクトは、YouTube 動画を検索して選択し、その内容を文字起こし・要約した後、日本語音声を生成する Streamlit アプリです。初心者の方でも `streamlit run app.py` を実行するだけで試せます。

## 必要なもの
- YouTube Data API キー (`YT_KEY`)
- Google Gemini API キー (`GEMINI_API_KEY`)
- Google Cloud Text-to-Speech の認証情報

環境変数 `GOOGLE_APPLICATION_CREDENTIALS` はサービスアカウント JSON ファイルへのパスを指定してください。

これらの情報は環境変数として設定してください。

## セットアップ
1. 依存パッケージをインストールします。
   ```bash
   pip install -r requirements.txt
   ```
   これにより、音声認識ライブラリ `openai-whisper` も自動でインストールされます。
2. 環境変数を設定したら、次のコマンドでアプリを起動します。
   ```bash
   streamlit run app.py
   ```
3. ブラウザが開いたらキーワード・言語・動画の長さを入力して検索し、生成された MP3 を再生・保存できます。

## ライセンス
このプロジェクトは MIT ライセンスの下で公開されています。詳細は LICENSE ファイルを参照してください。

