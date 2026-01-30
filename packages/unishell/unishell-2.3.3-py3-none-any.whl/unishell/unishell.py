from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from ._internal.file_utils import copy, mkdir, mkfile, rmfile, rmdir, make_archive, extract_archive, chmod, nano, make, remove, ls

from ._internal.ViewPort import ViewPort



class UniShell:

	def file(self, path: str | Path, encoding: str|None = None):
		from .__init__ import File
		return File(path, encoding,shell = self)
	
	def files(self, *files:"str|Path|File", encoding: str|None = None, sep = "\n"): # type: ignore
		from .__init__ import Files
		return Files(*files,encoding = encoding,sep = sep,shell = self)


	parms:ViewPort
		
	def __init__(
		self,
		sep: str = "\n",
		current_dir = os.getcwd(),
		default_encoding: str = 'utf-8',
		autodetect_encoding: bool = False,
		parms :ViewPort = ViewPort()
	):
		
		self.current_dir = Path(str(current_dir))
		parms.sets({
			"~": lambda: Path(os.path.expanduser('~')),
			"..": lambda: self.current_dir.parent,
			"CURRENTDIR": lambda: self.current_dir
		})
		parms["default_encoding"] = default_encoding
		parms["autodetect_encoding"] = autodetect_encoding
		parms["sep"] = sep
		self.parms = parms



	def to_abspath(self, path: "str|Path|File|Dir") -> Path:  # pyright: ignore[reportUndefinedVariable]
		path = Path(str(path))
		parts = path.parts
		new_path = Path()

		for part in parts:
			if len(part) >= 3 and part.startswith('%') and part.endswith('%'):
				var_name = part[1:-1]
				if var_name in self.parms.all():
					new_path = new_path / Path(self.parms[var_name])
				else:
					new_path = new_path / part
			elif part == '~':
				new_path = new_path / Path(os.path.expanduser('~'))
			elif part == '..':
				new_path = new_path.parent if new_path.parts else self.current_dir.parent
			elif part == '.':
				new_path = new_path / self.current_dir
			elif part:
				new_path = new_path / part

		if not new_path.is_absolute():
			new_path = self.current_dir / new_path

		return new_path.absolute()


	def cd(self, path):
		self.current_dir = self.to_abspath(path)
		return self

	def copy(self, from_path: str | Path, to_path: str | Path, *, follow_symlinks: bool = True, ignore_errors: bool = False):
		from_path = self.to_abspath(from_path)
		to_path = self.to_abspath(to_path)
		try:
			copy(from_path, to_path, follow_symlinks=follow_symlinks)
		except Exception:
			if not ignore_errors:
				raise
		return self

	def mkdir(self, path: str | Path, mode: int = 0o777, parents: bool = False, exist_ok: bool = False, ignore_errors: bool = False):
		path = self.to_abspath(path)
		try:
			mkdir(path, mode=mode, parents=parents, exist_ok=exist_ok)
		except Exception:
			if not ignore_errors:
				raise
		return self

	def mkfile(self, path: str | Path, ignore_errors: bool = False):
		path = self.to_abspath(path)
		try:
			mkfile(path)
		except Exception:
			if not ignore_errors:
				raise
		return self

	def rmfile(self, path: str | Path , ignore_errors: bool = False):
		path = self.to_abspath(path)
		try:
			rmfile(path)
		except Exception:
			if not ignore_errors:
				raise
		return self

	def rmdir(self, path: str | Path, ignore_errors: bool = False, onexc=None):
		path = self.to_abspath(path)
		rmdir(path, ignore_errors=ignore_errors, onexc=onexc)
		return self

	def make_archive(self, from_path: str | Path, to_path: str | Path | None = None, format: str = "zip", owner: Optional[str] = None, group: Optional[str] = None, ignore_errors: bool = False):
		from_path = self.to_abspath(from_path)
		if to_path is None:
			archive_name = f"{from_path.name}.{format}"
			to_path = self.current_dir / archive_name
		else:
			to_path = self.to_abspath(to_path)
		try:
			make_archive(from_path, to_path, format=format, owner=owner, group=group)
		except Exception:
			if not ignore_errors:
				raise
		return self
		
	def extract_archive(self, archive_path: str | Path, extract_dir: Optional[str | Path] = None, format: Optional[str] = None, ignore_errors: bool = False):
		archive_path = self.to_abspath(archive_path)
		if extract_dir is None:
			extract_dir = self.current_dir
		else:
			extract_dir = self.to_abspath(extract_dir)
		try:
			extract_archive(archive_path, extract_dir, format=format)
		except Exception:
			if not ignore_errors:
				raise
		return self
		
	def chmod(self, path: str | Path, mode: int, ignore_errors: bool = False):
		path = self.to_abspath(path)
		try:
			chmod(path, mode=mode)
		except Exception:
			if not ignore_errors:
				raise
		return self
		
	def recode(self, file_path: str | Path, to_encoding: str, from_encoding: Optional[str] = None, ignore_errors: bool = False):
		try:
			file_obj = self.file(file_path)
			file_obj.recode(to_encoding, from_encoding)
		except Exception as e:
			if not ignore_errors:
				raise
		return self
		
	def nano(self, path: str | Path, edit_txt="notepad", ignore_errors: bool = False):
		path = self.to_abspath(path)
		try:
			nano(path, edit_txt=edit_txt)
		except Exception:
			if not ignore_errors:
				raise
		return self

	def remove(self, path: str | Path, ignore_errors: bool = False):
		path = self.to_abspath(path)
		try:
			remove(path)
		except Exception:
			if not ignore_errors:
				raise
		return self

	def make(self, path: str | Path, is_file: bool|None = None, ignore_errors: bool = False):
		path = self.to_abspath(path)
		try:
			make(path, is_file=is_file)
		except Exception:
			if not ignore_errors:
				raise
		return self

	def ls(self, path: str | Path = ".", details: bool = False, ignore_errors: bool = False):
		path = self.to_abspath(path)
		try:
			return ls(path, details=details)
		except Exception:
			if not ignore_errors:
				raise
			return {} if details else []


	#Псевдонимы 
	touch = mkfile
	rm = remove
	rmtree = rmdir
	mk_archive = make_archive
	mkarch = make_archive
	unpack_archive = extract_archive
	unparch = extract_archive
	unp_arch =extract_archive
	ext_arch =extract_archive
	extarch = extract_archive
	convert_encoding = recode

	def __str__(self):
		return str(self.current_dir)

	def __repr__(self):
		return f"<UniShell cur_dir={self.current_dir}>"
	



__all__ = [
    'UniShell',
]
