from PyQt6 import QtMultimedia

from .subtitle_track import SubtitleTrack


class PyQtSubtitles:
    def __init__(self, media_player: QtMultimedia.QMediaPlayer, subtitle_files: list[str]):
        self._media_player = media_player

        self._tracks = [SubtitleTrack(filepath) for filepath in subtitle_files]
        self._current_track: SubtitleTrack | None = None

        self._media_player.positionChanged.connect(self._position_changed)

    def _position_changed(self, position: int):
        if self._current_track is not None:
            self._media_player.videoSink().setSubtitleText(self._current_track.get_subtitle(position))

    def set_current_track(self, index: int):
        """Sets current track index, if index is -1 or less, current track will be None"""
        if index < 0:
            self._current_track = None
        else:
            if index >= len(self._tracks):
                ...
            else:
                self._media_player.setActiveSubtitleTrack(-1)  # Disable video built-in subtitles
                self._current_track = self._tracks[index]

    def get_current_track(self) -> int:
        """Returns current track index, if no track is set, will return -1"""
        if self._current_track is None:
            return -1
        else:
            return self._tracks.index(self._current_track)

    def add_track(self, subtitle_file: str):
        """Adds new subtitle track. Warning: track won't set as default, you'll need to do this yourself"""
        self._tracks.append(SubtitleTrack(subtitle_file))

    def get_track_number(self) -> int:
        """Returns number of added tracks"""
        return len(self._tracks)
