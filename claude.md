# 目的
スライド(pdf)から，各ページのプレゼン音声を作成し，最終的にプレゼン動画を作成する

# 背景
- プレゼン動画を人が作成するのは労力がかかるので，AIで代替したい
- スライドを入力したら，プレゼン動画を生成する仕組みを作りたい

# 方法
1. LLMにスライド1枚を入力し，それを説明する原稿を出力します
2. 原稿を入力し，それを読み上げた音声を出力します
3. スライドのあるページを表示し，そのページの説明音声を読み上げた動画を作成します
4. 3を各ページについて行い，それをページ順に結合して全体のプレゼン動画とします．

# 条件
- 資料は日本語です
- 原稿出力にはclaude 3.7 sonnetを使ってください
- TTSにはgeminiを使ってください．以下に例があります．
- API KEYは.envファイルにあります
- 仮想環境はuvを用いてください

# gemini TTSのコード例
```python
from google import genai
from google.genai import types
import wave

# 出力を保存するためのwaveファイルを設定
def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
   with wave.open(filename, "wb") as wf:
      wf.setnchannels(channels)
      wf.setsampwidth(sample_width)
      wf.setframerate(rate)
      wf.writeframes(pcm)

# クライアントの準備
client = genai.Client(api_key="GEMINI_API_KEY")

# 音声の生成
response = client.models.generate_content(
   model="gemini-2.5-flash-preview-tts", # モデル
   contents="明るく言いましょう: 素敵な一日をお過ごしください!", # コンテンツ
   config=types.GenerateContentConfig(
      response_modalities=["AUDIO"],
      speech_config=types.SpeechConfig(
         voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(
               voice_name='Kore', # 音声名
            )
         )
      ),
   )
)

# 音声ファイルの保存
data = response.candidates[0].content.parts[0].inline_data.data
file_name='out.wav'
wave_file(file_name, data) # ファイルを現在のディレクトリに保存
```