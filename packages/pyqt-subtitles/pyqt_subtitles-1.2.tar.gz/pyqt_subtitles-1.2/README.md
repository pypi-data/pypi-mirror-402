# pyqt-subtitles 1.2
## Python library for adding srt subtitles into QMediaPlayer

### Installing

```shell
pip install git+https://github.com/nchistov/pyqt-subtitles.git@1.2
```

### Simple example

```python
import sys

from PyQt6 import QtWidgets, QtMultimedia, QtMultimediaWidgets, QtCore

from subtitles import PyQtSubtitles

app = QtWidgets.QApplication(sys.argv)

# Creating simple video player
media_player = QtMultimedia.QMediaPlayer()
video = QtMultimediaWidgets.QVideoWidget()
media_player.setVideoOutput(video)
media_player.setSource(QtCore.QUrl('path/to/your/video_file'))
media_player.play()

# Using pyqt-subtitles library
subs = PyQtSubtitles(media_player, ['path/to/your/file.srt'])
subs.set_current_track(0)

video.show()

sys.exit(app.exec())
```
