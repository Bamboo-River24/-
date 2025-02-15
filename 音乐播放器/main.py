import os
from PyQt5.QtCore import Qt, QUrl, QSize
from PyQt5.QtWidgets import (QApplication, QMessageBox, QFileDialog,
                             QListWidgetItem, QStyledItemDelegate)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.uic import loadUi
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, error as ID3Error
import music_get
from fun import download_music, get_duration


class MusicApp:
    def __init__(self):
        self.ui = loadUi('UI/main.ui')
        self.media_player = QMediaPlayer()
        self.current_file = None
        self.favorites = []
        self.playlist = []
        self.current_index = -1

        # 初始化设置
        self.init_ui()
        self.setup_media_player()
        self.setup_list_style()

    def init_ui(self):
        """初始化UI连接和状态"""
        # 页面切换
        self.ui.btnHome.clicked.connect(lambda: self.switch_page(0))
        self.ui.btnFavorites.clicked.connect(lambda: self.switch_page(1))
        self.ui.btnLocal.clicked.connect(lambda: self.switch_page(2))

        # 控制按钮
        self.ui.btnPlay.clicked.connect(self.toggle_play)
        self.ui.btnPrevious.clicked.connect(self.play_previous)
        self.ui.btnNext.clicked.connect(self.play_next)
        self.ui.btnLike.clicked.connect(self.toggle_like)
        self.ui.btnImport.clicked.connect(self.import_local_music)

        # 进度条
        self.ui.progressSlider.sliderPressed.connect(self.pause_for_seek)
        self.ui.progressSlider.sliderReleased.connect(self.seek_position)

        # 搜索功能
        self.ui.searchButton.clicked.connect(self.search)
        self.ui.searchBar.returnPressed.connect(self.search)

        # 列表双击播放
        self.ui.songList.itemDoubleClicked.connect(self.play_selected)
        self.ui.favoritesList.itemDoubleClicked.connect(self.play_selected)
        self.ui.localList.itemDoubleClicked.connect(self.play_selected)

        # 初始化状态
        self.ui.btnLike.setText("🤍 收藏")
        self.switch_page(0)

    def setup_media_player(self):
        """配置媒体播放器"""
        self.media_player.setNotifyInterval(500)
        self.media_player.positionChanged.connect(self.update_position)
        self.media_player.durationChanged.connect(self.update_duration)
        self.media_player.stateChanged.connect(self.update_play_state)
        self.media_player.mediaStatusChanged.connect(self.handle_media_status)

    def setup_list_style(self):
        """设置统一列表样式"""

        class MusicItemDelegate(QStyledItemDelegate):
            def sizeHint(self, option, index):
                size = super().sizeHint(option, index)
                return QSize(size.width(), 40)

        delegate = MusicItemDelegate()
        self.ui.songList.setItemDelegate(delegate)
        self.ui.favoritesList.setItemDelegate(delegate)
        self.ui.localList.setItemDelegate(delegate)

    def switch_page(self, index):
        """切换主页面"""
        self.ui.stackedWidget.setCurrentIndex(index)
        buttons = [self.ui.btnHome, self.ui.btnFavorites, self.ui.btnLocal]
        for btn in buttons:
            btn.setChecked(False)
        buttons[index].setChecked(True)

    def play_selected(self, item):
        """播放索引"""
        current_list = self.get_current_list()
        self.current_index = current_list.row(item)
        self.start_music()

    def get_current_list(self):
        """获取当前显示的列表控件"""
        return [
            self.ui.songList,
            self.ui.favoritesList,
            self.ui.localList
        ][self.ui.stackedWidget.currentIndex()]

    def start_music(self):

        try:
            current_list = self.get_current_list()
            item = current_list.currentItem()
            song_data = item.data(Qt.UserRole)

            # 确保本地路径存在
            if 'path' not in song_data and 'id' in song_data:
                song_data['path'] = download_music(song_data['id'], song_data['name'])

            # 验证文件路径
            if not os.path.exists(song_data['path']):
                raise FileNotFoundError("音乐文件不存在，请重新下载")

            media = QMediaContent(QUrl.fromLocalFile(song_data['path']))
            self.media_player.setMedia(media)
            self.media_player.play()
            self.update_metadata(song_data)

        except Exception as e:
            QMessageBox.critical(self.ui, "播放错误", str(e))

    def update_metadata(self, data):
        """更新当前播放信息"""
        self.ui.lblTitle.setText(f"正在播放: {data.get('name', '未知曲目')}    艺术家: {data.get('artist', '未知艺术家')}")

    def toggle_play(self):
        """切换播放/暂停状态"""
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
        else:
            if self.media_player.mediaStatus() == QMediaPlayer.NoMedia:
                self.start_music()
            else:
                self.media_player.play()

    def update_play_state(self, state):
        """更新播放按钮状态"""
        if state == QMediaPlayer.PlayingState:
            self.ui.btnPlay.setText("⏸️ 暂停")
        else:
            self.ui.btnPlay.setText("▶️ 播放")

    def update_position(self, position):
        """更新播放进度"""
        seconds = position // 1000
        self.ui.progressSlider.setValue(seconds)
        self.update_time_display(seconds, self.media_player.duration() // 1000)

    def update_duration(self, duration):
        """更新总时长"""
        self.ui.progressSlider.setMaximum(duration // 1000)

    def update_time_display(self, current, total):
        """更新时间显示"""
        current_str = f"{current // 60:02}:{current % 60:02}"
        total_str = f"{total // 60:02}:{total % 60:02}"
        self.ui.timeLabel.setText(f"{current_str} / {total_str}")

    def pause_for_seek(self):
        """准备定位时暂停播放"""
        self.was_playing = self.media_player.state() == QMediaPlayer.PlayingState
        if self.was_playing:
            self.media_player.pause()

    def seek_position(self):
        """定位播放位置"""
        target = self.ui.progressSlider.value() * 1000
        self.media_player.setPosition(target)
        if self.was_playing:
            self.media_player.play()

    def toggle_like(self):
        """修复收藏歌曲路径问题"""
        current_item = self.get_current_list().currentItem()
        if not current_item:
            return
        song_data = current_item.data(Qt.UserRole)
        # 如果是在线歌曲，需要下载并存储路径
        if 'id' in song_data and 'path' not in song_data:
            try:
                file_path = download_music(song_data['id'], song_data['name'])
                song_data['path'] = file_path
            except Exception as e:
                QMessageBox.critical(self.ui, "错误", f"收藏失败: {str(e)}")
                return
        # 检查是否已存在相同ID的收藏
        existing = next((s for s in self.favorites if s.get('id') == song_data.get('id')), None)
        if existing:
            self.remove_from_favorites(song_data)
            self.ui.btnLike.setText("🤍 收藏")
        else:
            self.add_to_favorites(song_data.copy())  # 使用副本避免数据污染
            self.ui.btnLike.setText("🤍 收藏")

    def add_to_favorites(self, song_data):
        """添加到收藏列表"""
        self.favorites.append(song_data)
        item = QListWidgetItem(f"{song_data['name']} - {song_data['artist']}")
        item.setData(Qt.UserRole, song_data)
        self.ui.favoritesList.addItem(item)

    def remove_from_favorites(self, song_data):
        """从收藏列表移除"""
        self.favorites = [s for s in self.favorites if s.get('id') != song_data.get('id')]
        for i in range(self.ui.favoritesList.count()):
            item = self.ui.favoritesList.item(i)
            if item.data(Qt.UserRole).get('id') == song_data.get('id'):
                self.ui.favoritesList.takeItem(i)
                break

    def import_local_music(self):
        """导入本地音乐"""
        files, _ = QFileDialog.getOpenFileNames(
            None, "选择音乐文件", "",
            "音频文件 (*.mp3 *.wav *.flac)"
        )

        for path in files:
            try:
                # 解析元数据
                audio = MP3(path, ID3=ID3)
                title = audio.tags.get('TIT2', ['未知标题'])[0]
                artist = audio.tags.get('TPE1', ['未知艺术家'])[0]
                duration = audio.info.length

                song_data = {
                    'name': title,
                    'artist': artist,
                    'path': path,
                    'duration': duration
                }

                # 添加到列表
                item = QListWidgetItem(f"{title} - {artist}")
                item.setData(Qt.UserRole, song_data)
                self.ui.localList.addItem(item)

            except (ID3Error, AttributeError) as e:
                print(f"解析失败 {path}: {str(e)}")
                base_name = os.path.basename(path)
                item = QListWidgetItem(f"未知信息 - {base_name}")
                item.setData(Qt.UserRole, {'path': path})
                self.ui.localList.addItem(item)
            except Exception as e:
                QMessageBox.warning(self.ui, "错误", f"无法读取文件: {path}\n{str(e)}")

    def search(self):
        """搜索在线音乐"""
        keyword = self.ui.searchBar.text().strip()
        if not keyword:
            QMessageBox.warning(self.ui, "提示", "请输入搜索关键词")
            return
        try:
            self.ui.songList.clear()
            names, artists, ids = music_get.search_song(keyword)
            for name, artist, song_id in zip(names, artists, ids):
                item = QListWidgetItem(f"{name} - {artist}")
                item.setData(Qt.UserRole, {
                    'name': name,
                    'artist': artist,
                    'id': song_id
                })
                self.ui.songList.addItem(item)
        except Exception as e:
            QMessageBox.critical(self.ui, "搜索失败", str(e))

    def handle_media_status(self, status):
        """处理媒体状态变化"""
        if status == QMediaPlayer.LoadedMedia:
            self.ui.btnPlay.setEnabled(True)
        elif status == QMediaPlayer.EndOfMedia:
            self.play_next()

    def play_previous(self):
        """播放上一曲"""
        if self.current_index > 0:
            self.current_index -= 1
            self.play_from_playlist()

    def play_next(self):
        """播放下一曲"""
        current_list = self.get_current_list()
        if self.current_index < current_list.count() - 1:
            self.current_index += 1
            self.play_from_playlist()

    def play_from_playlist(self):
        """从当前列表播放"""
        current_list = self.get_current_list()
        if 0 <= self.current_index < current_list.count():
            current_list.setCurrentRow(self.current_index)
            self.start_music()


if __name__ == "__main__":
    app = QApplication([])
    window = MusicApp()
    window.ui.show()
    app.exec_()