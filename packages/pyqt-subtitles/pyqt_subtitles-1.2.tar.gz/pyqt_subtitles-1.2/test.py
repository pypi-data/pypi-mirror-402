import sys

from PyQt6 import QtWidgets
from qfilmplayer import QFilmPlayer

from subtitles import PyQtSubtitles

app = QtWidgets.QApplication(sys.argv)

fp = QFilmPlayer('/home/nick/Downloads/The Hobbit_The Battle of the Five Armies_[Extended Edition]_BDRip_RG_All_Films/The Hobbit_The Battle of the Five Armies_[Extended Edition]_BDRip_RG_All_Films.avi', '')
subs = PyQtSubtitles(fp.media_player, ['/home/nick/Downloads/The Hobbit_The Battle of the Five Armies_[Extended Edition]_BDRip_RG_All_Films/The Hobbit_The Battle of the Five Armies_[Extended Edition]_BDRip_RG_All_Films.srt'])
subs.set_current_track(0)
fp.show()

sys.exit(app.exec())
