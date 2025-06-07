# YouTube ゆっくり解説メーカー

このプロジェクトは、YouTube 動画を検索して選択し、その内容を文字起こし・要約した後、日本語音声を生成する Django Web アプリです。初心者の方でも `python manage.py runserver` を実行するだけで試せます。

## 必要なもの
- YouTube Data API キー (`YT_KEY`)
- Google Gemini API キー (`GEMINI_API_KEY`)
- Google Cloud Text-to-Speech の認証情報

環境変数 `GOOGLE_APPLICATION_CREDENTIALS` はサービスアカウント JSON ファイルへのパスを指定してください。

これらの情報は環境変数として設定してください。

## 環境変数の設定
`.env.example` を `.env` にコピーして、以下の値を編集します。

```bash
cp .env.example .env
# .env の例 (ここを上書きしてください)
SECRET_KEY=ここを上書きしてください
DEBUG=True
DATABASE_URL=
YT_KEY=ここを上書きしてください
GEMINI_API_KEY=ここを上書きしてください
GOOGLE_APPLICATION_CREDENTIALS=ここを上書きしてください
```

## セットアップ
1. 依存パッケージをインストールします。
   ```bash
   pip install -r requirements.txt
   ```
   これにより、音声認識ライブラリ `openai-whisper` も自動でインストールされます。
2. Django のマイグレーションを適用します。
   ```bash
   python manage.py migrate
   ```
3. 環境変数を設定したら、次のコマンドでアプリを起動します。
   ```bash
   python manage.py runserver
   ```
4. ブラウザが開いたらキーワード・言語・動画の長さを入力し、スクリプトの出力言語も選択して検索すると、生成された MP3 を再生・保存できます。
5. 複数の動画をチェックボックスで選択し、**Process Selected** を押すと、各動画の文字起こしをダウンロードして 1 つにまとめます。それを Gemini に送信して、1 つのスクリプトと MP3 を生成できます。
6. 検索の代わりに YouTube の動画 URL を入力すると、その動画から直接要約と音声を生成できます。
7. 取得した文字起こしを Gemini に渡し、ゆっくり解説用のスクリプトを生成します。
8. さらにそのスクリプトから、2 人の登場人物による要約ディスカッション台本を Gemini で作成し、画面に表示します。音声合成もこの台本を使用します。

## 検索対象動画のライセンス制限
デフォルトでは、YouTube 検索は Creative Commons ライセンスの動画だけに限られます。
`pipeline.search_videos` 関数の `search_params` に `"videoLicense": "creativeCommon"` が
設定されているためです。

すべての動画を対象にしたい場合は、`pipeline.py` を開いてこの行を削除するか、
値を `"any"` などに変更してください。変更後にアプリを再起動すれば、より広い範囲から
検索できます。

## Railway でのデプロイ
1. Railway のシェルで依存パッケージをインストールします。
   ```bash
   pip install -r requirements.txt
   ```
2. 次のコマンドを実行してデータベースを準備します。
   ```bash
   python manage.py migrate
   python manage.py collectstatic --noinput
   ```
3. `.env.example` を参考に環境変数を Railway の設定画面で追加します。
4. Docker を利用する場合は次のコマンドでイメージをビルドして実行できます。
   ```bash
   docker build -t slower .
   docker run -p 8000:8000 slower
   ```

## ライセンス
このプロジェクトは MIT ライセンスの下で公開されています。詳細は LICENSE ファイルを参照してください。

