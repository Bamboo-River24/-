import requests
from fake_useragent import UserAgent

def search_song(song_name):
    """改进的搜索函数"""
    url = 'https://music.163.com/api/search/get/web'
    ua = UserAgent()

    try:
        response = requests.post(
            url,
            headers={
                'User-Agent': ua.random,
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            data={
                's': song_name,
                'type': 1,
                'limit': 8,
                'offset': 0
            },
            timeout=15
        )
        response.raise_for_status()

        result = response.json()
        if result.get('code', 404) != 200:
            raise Exception("API返回错误")

        songs = result.get('result', {}).get('songs', [])
        names = []
        artists = []
        ids = []

        for song in songs:
            names.append(song.get('name', '未知歌曲'))
            artists.append(song.get('artists', [{}])[0].get('name', '未知歌手'))
            ids.append(str(song.get('id', '')))

        return names, artists, ids
    except Exception as e:
        raise Exception(f"搜索失败: {str(e)}")