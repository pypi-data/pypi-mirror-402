from __future__ import annotations

from ..stream import Stream
from .file import File
from pathlib import Path

class Files(Stream):
    def __init__(self,*files : str|Path|File, encoding = None, sep = "\n"):
        self.files:list[File] = [File(file, encoding = encoding) for file in files ]
        self.sep = sep

    
    def __stream_getData__(self) -> str:
        return self.sep.join(map(lambda file:file.content, self.files))
