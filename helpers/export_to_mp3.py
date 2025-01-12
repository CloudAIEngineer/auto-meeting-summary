from pytubefix import YouTube
from pydub import AudioSegment
import os
import re

# Function to sanitize filenames
def sanitize_filename(filename):
    filename = re.sub(r'[\\/*?:"<>|]', "", filename)
    filename = filename.replace(" ", "-")
    return filename

# Array of URLs - publicly available meetings from YouTube
urls = [
    'https://www.youtube.com/watch?v=lBVtvOpU80Q',
    'https://www.youtube.com/watch?v=k8K6wQLxooU',
    'https://www.youtube.com/watch?v=qGFoZ8yodc4'
]

for url in urls:
    try:
        yt = YouTube(url)
        stream = yt.streams.filter(only_audio=True).first()
        
        # Sanitize the title for a valid filename
        filename = f"meetings/{sanitize_filename(yt.title)}.mp4"
        
        stream.download(filename=filename)

        audio = AudioSegment.from_file(filename, format='mp4')
        audio.export(f'meetings/{sanitize_filename(yt.title)}.mp3', format='mp3')

        os.remove(filename)

        print(f"Conversion for {yt.title} completed!")

    except Exception as e:
        print(f"Error processing {url}: {e}")

