import os
import requests
from mutagen.mp3 import MP3

def download_music(song_id, song_name):
    """下载音乐文件并返回本地路径"""
    music_dir = "music"
    os.makedirs(music_dir, exist_ok=True)
    safe_name = "".join(c for c in song_name if c.isalnum() or c in (' ', '_')).rstrip()
    file_path = os.path.join(music_dir, f"{safe_name}.mp3")

    if os.path.exists(file_path):
        return file_path

    music_url = f'https://music.163.com/song/media/outer/url?id={song_id}.mp3'
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(music_url, headers=headers, stream=True, timeout=20)
        if response.url == 'https://music.163.com/404' or response.status_code != 200:
            raise Exception("该歌曲受版权保护或不存在")

        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024*1024):
                if chunk:
                    f.write(chunk)
        return file_path
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise e

def get_duration(file_path):
    """获取音乐时长（秒）"""
    try:
        audio = MP3(file_path)
        return audio.info.length
    except Exception as e:
        raise Exception(f"无法解析音频时长: {str(e)}")

