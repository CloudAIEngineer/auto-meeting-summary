from pytubefix import YouTube
from pydub import AudioSegment
import os
import re

# Function to sanitize filenames
def sanitize_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "", filename)

# Array of URLs
urls = ['https://www.youtube.com/watch?v=1j0X9QMF--M']

for url in urls:
    try:
        yt = YouTube(url)
        stream = yt.streams.filter(only_audio=True).first()
        
        # Sanitize the title for a valid filename
        filename = f"{sanitize_filename(yt.title)}.mp4"
        
        stream.download(filename=filename)

        audio = AudioSegment.from_file(filename, format='mp4')
        audio.export(f'{sanitize_filename(yt.title)}.mp3', format='mp3')

        os.remove(filename)

        print(f"Conversion for {yt.title} completed!")

    except Exception as e:
        print(f"Error processing {url}: {e}")

