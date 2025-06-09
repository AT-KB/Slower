# YouTube ゆっくり解説メーカー

このプロジェクトは、YouTube 動画を検索して選択し、その内容を文字起こし・要約した後、日本語音声を生成する Django Web アプリです。初心者の方でも `python manage.py runserver` を実行するだけで試せます。

## 必要なもの
- YouTube Data API キー (`YT_KEY`)
- Google Gemini API キー (`GEMINI_API_KEY`)
- 使用する Gemini モデル名 (`GEMINI_MODEL`, デフォルト `models/gemini-pro`)
  - 省略可。別のモデルを使う場合はこの値を変更してください
- Google Cloud Text-to-Speech の認証情報
- yt-dlp で利用する cookie ファイル (`YTDLP_COOKIES`, 任意)
  - 年齢制限付き動画をダウンロードする際に使用
- Whisper のモデル名 (`WHISPER_MODEL`, デフォルト `tiny`)
  - 文字起こしに使う Whisper モデルを指定
- Gunicorn のタイムアウト秒数 (`GUNICORN_TIMEOUT`, デフォルト `120`)
  - デプロイ時の処理時間に合わせて調整

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
GEMINI_MODEL=models/gemini-pro
GOOGLE_APPLICATION_CREDENTIALS=ここを上書きしてください
YTDLP_COOKIES=
WHISPER_MODEL=tiny
WHISPER_BACKEND=openai      # use 'faster' for faster-whisper
WHISPER_COMPUTE_TYPE=int8   # compute type for faster-whisper
GUNICORN_TIMEOUT=120
```

`YTDLP_COOKIES` には、年齢制限やログインが必要な動画を処理するときに使用する cookie ファイルへのパスを指定します。
`WHISPER_MODEL` を指定すると Whisper のモデルサイズを変更できます。デフォルトは `tiny` です。より大きなモデルを使うと精度は上がりますが、処理時間も長くなります。
`WHISPER_BACKEND` で文字起こしバックエンドを選択できます。`WHISPER_COMPUTE_TYPE` は faster-whisper の精度を決める値で、CPU では `int8` のままにしてください。
`GUNICORN_TIMEOUT` で Gunicorn のタイムアウト秒数を調整できます。Whisper モデルを低スペックのハードウェアで使用する際は、処理に時間がかかるためより長いタイムアウトが必要になることがあります。
## Performance Tips

CPU 環境でもデフォルトの Whisper モデル `tiny` なら比較的速く処理できます。
`.env` で `WHISPER_MODEL=tiny` または `WHISPER_MODEL=small` を設定すると処理が速くなります。
必要に応じて `GUNICORN_TIMEOUT` も長めに設定してください。
```
WHISPER_MODEL=tiny
GUNICORN_TIMEOUT=300
```
`faster-whisper` を使う場合は `WHISPER_BACKEND=faster` を指定します。Tiny モデルとの組み合わせで高速に動作します。
```
WHISPER_MODEL=tiny
WHISPER_BACKEND=faster
```
`WHISPER_COMPUTE_TYPE` を設定すると `faster-whisper` の compute_type を変更できます。デフォルトは `int8` で、GPU 環境では `float16` などを指定します。

GPU 非搭載の PC では、以下のように設定すると高速に処理できます。`GUNICORN_TIMEOUT` も長めに調整してください。
```
WHISPER_MODEL=tiny
WHISPER_BACKEND=faster
WHISPER_COMPUTE_TYPE=int8
GUNICORN_TIMEOUT=300
```

## セットアップ
1. 依存パッケージをインストールします。
   ```bash
   pip install -r requirements.txt
   ```
   これにより、音声認識ライブラリ `openai-whisper` も自動でインストールされます。
2. 音声のダウンロードや文字起こしには `ffmpeg` のインストールが必要です。Debian/Ubuntu では次のコマンドを実行してください。
   ```bash
   sudo apt-get install ffmpeg
   ```
   その他のプラットフォームは [公式サイト](https://ffmpeg.org/download.html) を参照してください。
3. Django のマイグレーションを適用します。
   ```bash
   python manage.py migrate
   ```
4. 環境変数を設定したら、次のコマンドでアプリを起動します。
   ```bash
   python manage.py runserver
   ```
5. ブラウザが開いたらキーワード・言語・動画の長さを入力し、スクリプトの出力言語も選択して検索すると、生成された MP3 を再生・保存できます。
6. 複数の動画をチェックボックスで選択し、**Process Selected** を押すと、各動画の文字起こしをダウンロードして 1 つにまとめます。それを Gemini に送信して、1 つのスクリプトと MP3 を生成できます。
7. 検索の代わりに YouTube の動画 URL を入力すると、その動画から直接要約と音声を生成できます。
8. 取得した文字起こしを Gemini に渡し、ゆっくり解説用のスクリプトを生成します。
9. さらにそのスクリプトから、2 人の登場人物による要約ディスカッション台本を Gemini で作成し、画面に表示します。音声合成もこの台本を使用します。
10. 各ステップの完了後に進捗が `<pre>` ブロックに表示されます。エラーが起きた場合も、どの段階まで処理されたか確認できます。

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

## トラブルシューティング
`WORKER TIMEOUT` は CPU のみの環境で Whisper の処理が遅いときに発生することがあります。
以下のように小さいモデルと `faster` バックエンドを指定するとタイムアウトを防げます。

```bash
WHISPER_MODEL=tiny
WHISPER_BACKEND=faster
WHISPER_COMPUTE_TYPE=int8
GUNICORN_TIMEOUT=300
```

これらの設定は GPU を搭載していない PC でも動作し、Railway などのホスティング環境で
タイムアウトを回避できます。

## ライセンス
このプロジェクトは MIT ライセンスの下で公開されています。詳細は LICENSE ファイルを参照してください。

