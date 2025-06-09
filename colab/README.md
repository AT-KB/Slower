# Google Colab での実行手順

このディレクトリでは、`DL2Summary.ipynb` と `Text2MP3.ipynb` を Google Colab で実行する方法を説明します。

## Colab でノートブックを開く
1. GitHub のリポジトリページから各ノートブックへのリンクを選択し、`Open in Colab` を押します。
2. 新しいブラウザタブで Colab が開いたら、メニューの **Runtime > Run all** を選択して全セルを実行できます。

## Google ドライブのマウント
- ノートブック内で次のコードを実行し、表示される認証フローを完了してください。
  ```python
  from google.colab import drive
  drive.mount('/content/drive')
  ```
- ドライブをマウントすると、作業ファイルを `/content/drive/MyDrive/` 以下に保存できます。

## API キーの設定 (Secrets)
1. Colab 画面右上の鍵アイコンから **Secrets** を開きます。
2. `.env.example` と同じ名前で環境変数を登録します。
   - 例: `SECRET_KEY`, `YT_KEY`, `GEMINI_API_KEY`, `GOOGLE_APPLICATION_CREDENTIALS` など
3. ノートブックでは次のように読み込みます。
   ```python
   import os
   import google.colab.userdata as ud
   os.environ['YT_KEY'] = ud.get('YT_KEY')
   ```

登録した環境変数は Colab セッション中のみ有効です。`.env` ファイルをアップロードして利用することもできます。その場合はドライブに配置し `python-dotenv` などで読み込んでください。

必要な環境変数一覧は `.env.example` を参照してください。主な項目は以下のとおりです。
```
SECRET_KEY
DEBUG
DATABASE_URL
YT_KEY
GEMINI_API_KEY
GEMINI_MODEL
GOOGLE_APPLICATION_CREDENTIALS
YTDLP_COOKIES
WHISPER_MODEL
WHISPER_BACKEND
WHISPER_COMPUTE_TYPE
WHISPER_CACHE
GUNICORN_TIMEOUT
PORT
```

## 実行手順
1. `DL2Summary.ipynb` を開き、上から順にすべてのセルを実行します。動画の文字起こしと要約が生成されます。
2. 続いて同じ Colab セッションで `Text2MP3.ipynb` を開き、前のノートブックで作成されたテキストから音声合成を行います。
3. 実行後、`/content/drive/MyDrive/` 配下に transcript、summary、MP3 ファイルが保存されます。

GPU がなくても問題ありません。デフォルトで tiny Whisper モデルを使うため、CPU のみの Colab インスタンスでも動作します。
