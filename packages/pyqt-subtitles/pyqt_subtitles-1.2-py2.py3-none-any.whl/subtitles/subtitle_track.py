import datetime

import srt


class SubtitleTrack:
    def __init__(self, filepath: str):
        self._subtitles = []

        self._load_subtitle(filepath)

    def get_subtitle(self, position: int) -> str:
        time = datetime.timedelta(milliseconds=position)

        for sub in self._subtitles:
            if sub.start < time < sub.end:
                return sub.content

        return ''

    def _load_subtitle(self, filepath: str):
        encodings = ['utf-8', 'windows-1251']

        for encoding in encodings:
            try:
                with open(filepath, encoding=encoding) as f:
                    self._subtitles = list(srt.parse(f.read()))
                    break
            except UnicodeDecodeError:
                continue
