"""
UniShell - унифицированная оболочка для работы с файловой системой
"""
from .unishell import *
from ._internal import structures as std
from pathlib import Path
from ._internal.encoding_utils import detect_encoding,determine_minimal_encoding,check_bom
class File(std.File):
	def __init__(self, path: str | Path, encoding: str|None = None,shell:UniShell|None = None):
		shell = shell or sh
		path = shell.to_abspath(path)
		enc = encoding or path and shell.parms["autodetect_encoding"] and detect_encoding(path, ignore_errors = True) or shell.parms["default_encoding"]
		super().__init__(path, enc)
class Files(std.Files):
	def __init__(self, *files:str|Path|File, encoding: str|None = None, sep = "\n", shell: UniShell|None = None):
		shell = shell or sh
		def abspath(file):
			if isinstance(file, File):
				return file
			file = shell.to_abspath(file) or file
			return file
		super().__init__(*map(lambda file: abspath(file), files), encoding = encoding, sep = sep)
class Dir(std.Dir):
	def __init__(self, path: "Dir|Path|str", shell: UniShell|None = None):
		shell = shell or sh
		path = shell.to_abspath(path)
		super().__init__(path)
class Archive(std.Archive):
	def __init__(self,path: File|Path|str, format: str|None = None, password: str|None = None, shell: UniShell|None = None):
		shell = shell or sh
		path = shell.to_abspath(path)
		super().__init__(path)

sh = UniShell()

__all__ = [
    'UniShell',
    'sh',
    'File',
	'Dir',
    'Files',
    'detect_encoding',
    'determine_minimal_encoding',
	'check_bom',
    'Path',
]

