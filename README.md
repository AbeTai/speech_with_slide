# スライド音声プレゼン動画生成システム

## 概要
スライド(PDF)から各ページのプレゼン音声を自動生成し、最終的にプレゼン動画を作成するシステムです。

## 背景
プレゼン動画を人が作成するのは労力がかかるため、AIで代替できるシステムを構築しています。スライドを入力するだけで、プレゼン動画を自動生成する仕組みを提供します。

## 機能
1. **原稿生成**: LLMにスライド1枚を入力し、それを説明する原稿を出力
2. **音声生成**: 原稿を入力し、それを読み上げた音声を出力
3. **動画作成**: スライドのあるページを表示し、そのページの説明音声を組み合わせた動画を作成
4. **結合**: 各ページの動画をページ順に結合して全体のプレゼン動画を生成
5. **プロンプト管理**: 設定ファイルによる柔軟なプロンプト管理

## 技術仕様
- **言語**: 日本語
- **原稿生成**: Claude 3.7 Sonnet
- **音声合成**: Gemini TTS
- **パッケージ管理**: uv
- **API KEY**: .envファイルで管理
- **プロンプト管理**: YAML形式の設定ファイル

## セットアップ
1. 仮想環境の作成と依存関係のインストール:
```bash
uv sync
```

2. 環境変数の設定:
`.env`ファイルに以下のAPI KEYを設定してください:
```
ANTHROPIC_API_KEY=your_anthropic_api_key
GOOGLE_API_KEY=your_google_api_key
```

## 使用方法
```bash
uv run python main.py <pdf_path>
```

例:
```bash
uv run python main.py slides/presentation.pdf
```

## プロンプト設定
`prompts.yaml`ファイルでプロンプトやモデル設定をカスタマイズできます:

### 設定項目
- **script_generation**: 原稿生成用のプロンプト
- **model_config**: Claude/Geminiの設定
- **customization**: プレゼンテーションスタイルの設定

### 設定例
```yaml
script_generation:
  system_prompt: |
    あなたは優秀なプレゼンテーション原稿作成の専門家です。
  
  user_prompt: |
    このPDFの{page_num}ページ目の内容を説明する原稿を作成してください。

model_config:
  claude:
    model: "claude-3-7-sonnet-20250219"
    max_tokens: 1000
    temperature: 0.1
  
  gemini_tts:
    model: "gemini-2.5-flash-preview-tts"
    voice_name: "Kore"
```

## プロジェクト構成
```
├── main.py              # メインプログラム
├── prompt_manager.py    # プロンプト管理システム
├── prompts.yaml         # プロンプト設定ファイル
├── pyproject.toml       # プロジェクト設定
├── uv.lock             # 依存関係ロック
├── .env                # 環境変数（API KEY等）
├── slides/             # 入力PDFファイル
├── output/             # 生成された動画・音声・原稿
│   └── <project_name>/
│       ├── txt/        # 原稿ファイル
│       ├── wav/        # 音声ファイル
│       ├── mp4/        # 個別動画ファイル
│       └── <project_name>.mp4  # 最終動画
└── README.md           # このファイル
```

## 出力ファイル
システムは以下のファイルを生成します:
- `output/<project_name>/txt/slide_XXX_script.txt`: 各スライドの原稿
- `output/<project_name>/wav/slide_XXX_audio.wav`: 各スライドの音声
- `output/<project_name>/mp4/slide_XXX_video.mp4`: 各スライドの動画
- `output/<project_name>/<project_name>.mp4`: 最終的なプレゼン動画

## 開発状況
現在開発中のプロジェクトです。各機能の実装を順次進めています。