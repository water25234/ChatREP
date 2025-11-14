import os
import openai
import yt_dlp
import argparse

from dotenv import load_dotenv
import os
from pydub import AudioSegment
from urllib.parse import urlparse, parse_qs

class CHATREP:
    def __init__(self, url: str, openai_api_key: str):
        self.url = url
        self.openai_api_key = openai_api_key

        openai.api_key = openai_api_key

    def execute(self):
        video_id = self.extract_video_id(url)

        sound = self.makeYTDlp(url, video_id)

        video_array = self.makeSplitVidoe(sound)

        transcript_array = self.makeWordByWhisper(video_array, video_id)

        self.makeReadingExperienceByChatGPT(transcript_array)
    
    def extract_video_id(self, url: str) -> str:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        return query_params['v'][0]

    def makeYTDlp(self, url: str, video_id: str) -> AudioSegment:
        print('execute YT DLP')

        # setting yt_dlp
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': video_id,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        # downland video by yt_dlp 
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # setting video .mp3
        sound = AudioSegment.from_file(video_id + '.mp3', format='mp3')
        return sound
    
    def makeSplitVidoe(self, sound: AudioSegment) -> list:
        print('execute split video')
        # split video by millisecond
        segment_length = 1000000

        video_array = []
        # split video 
        for i, chunk in enumerate(sound[::segment_length]):
            video_array.append(i)
            chunk.export(f'output_{i}.mp3', format='mp3')
        
        return video_array
    
    # download word form video by whisper
    def makeWordByWhisper(self, video_array: list, video_id: str) -> list:
        print('execute whisper')
        transcript = ''
        for i in video_array:

            audio_file = open(f'output_{i}.mp3', "rb")

            transcript_whisper = openai.Audio.transcribe("whisper-1", audio_file)

            transcript = transcript + ' ' + transcript_whisper.to_dict().get('text')

        with open(video_id + '.txt', 'w') as file:
            file.write(transcript)

        ret = ''
        transcript_array = []
        for script in transcript.split():
            ret = ret + ' ' + script
            if len(ret) > 50000:
                transcript_array.append(ret)
                ret = ''
        transcript_array.append(ret)

        return transcript_array
    
    # call chatGPT 
    def makeReadingExperienceByChatGPT(self, transcript_array: list) -> None:
        print('execute chatGPT')

        result_array = []
        for t in transcript_array:
            completion = openai.ChatCompletion.create(
                model="gpt-5-mini",
                messages=[
                    {"role": "system", "content": "你現在是閱讀書籍者，請寫出文章的摘要，並且以繁體中文輸出"},
                    {"role": "user", "content": t}
                ]
            )
            result_array.append(completion.choices[0].message)

        print()
        print('Hey ChatGPT, 你現在是閱讀書籍者，請寫出文章的摘要，並且以繁體中文輸出: ')

        for res in result_array:
            print()
            print(res.get('content'))


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--openai_key",
        dest="openai_key",
        type=str,
        default="",
        help="openai api key",
    )

    parser.add_argument(
        "--youtube_url",
        dest="youtube_url",
        type=str,
        default="",
        help="youtube url",
    )

    options = parser.parse_args()

    load_dotenv()
    OPENAI_API_KEY = options.openai_key or os.getenv("OPENAI_API_KEY")

    url = options.youtube_url
    if not url:
        raise ValueError("YouTube URL is required.")
    if not OPENAI_API_KEY:
        raise ValueError("OpenAI API key is required.")

    chatREP = CHATREP(url, OPENAI_API_KEY)

    chatREP.execute()
