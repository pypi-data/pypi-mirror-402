"""
UniShell Interface Documentation
=================================

This module provides comprehensive interface documentation for the UniShell class,
which is the main entry point for file system operations in FileAlchemy.

The documentation follows PEP 484 type hints and Google-style docstrings
for optimal IDE support and documentation generation.

Version: 1.0.0
"""

import os
from pathlib import Path
from typing import Optional, Union, List, Dict, Any, overload
from ._internal.ViewPort import ViewPort
from .__init__ import File, Files, Dir

# Type Aliases
PathTp = Union[str, Path]
FileTp = Union[str, Path, File]
DirTp =  Union[str, Path, Dir]
FileDirTp = Union[str, Path, File, Dir]
Encoding = str
Mode = int
ArchiveFormat = str

class UniShell:
    """
    Unified shell interface for comprehensive file system operations.
    
    The UniShell class provides a Pythonic, fluent interface for working with files,
    directories, encodings, and archives. It abstracts platform-specific details
    while maintaining performance and flexibility.
    
    Key Features:
        • File and directory management (create, copy, move, delete)
        • Automatic encoding detection and conversion
        • Archive operations (zip, tar, gztar, bztar, xztar)
        • Path resolution with environment variable expansion
        • Method chaining for fluent workflows
        • Configurable error handling
    
    Attributes:
        current_dir (Path): Current working directory as Path object.
        parms (ViewPort): Configuration parameters and environment variables.
    
    Examples:
        >>> shell = UniShell()
        >>> content = shell.file('data.txt').content
        >>> shell.copy('source/', 'dest/').make_archive('dest/', 'backup.zip')
    """
    parms : ViewPort
    def __init__(
        self,
        sep: str = "\n",
        current_dir: DirTp = os.getcwd(),
        default_encoding: str = 'utf-8',
        autodetect_encoding: bool = False,
        parms: ViewPort = ViewPort()
    ) -> None:
        """
        Initialize a new UniShell instance with specified configuration.
        
        Args:
            sep: Separator used when joining contents of multiple files.
                Defaults to newline.
            current_dir: Initial working directory. Defaults to current
                process working directory.
            default_encoding: Default text encoding for file operations.
                Used when encoding cannot be auto-detected.
            autodetect_encoding: Enable automatic encoding detection for
                text files. Adds overhead but improves compatibility.
            parms: ViewPort instance for configuration. Creates new instance
                if not provided.
        
        Returns:
            Configured UniShell instance ready for operations.
        
        Examples:
            >>> # Basic initialization
            >>> shell = UniShell()
            >>> 
            >>> # With custom configuration
            >>> shell = UniShell(
            ...     current_dir='/home/user/projects',
            ...     default_encoding='utf-16',
            ...     autodetect_encoding=True
            ... )
        """
        ...
    
    
    
    def to_abspath(self, path: FileDirTp) -> Path:
        """
        Convert path to absolute path with variable expansion.
        
        Expands:
            • Environment variables: %VAR% (Windows) style
            • Home directory: ~
            • Parent directory: ..
            • Current directory: .
        
        Args:
            path: Input path to resolve. Can be relative, contain
                variables, or use special notations.
        
        Returns:
            Absolute, resolved Path object.
        
        Raises:
            ValueError: If path contains malformed variable syntax.
        
        Examples:
            >>> shell.to_abspath('~/%USERNAME%/docs')
            WindowsPath('C:/Users/john/docs')
            >>> shell.to_abspath('../data/./files')
            PosixPath('/home/user/data/files')
        """
        ...
    
    # File Operations
    def file(self, path: FileTp, encoding: str|None = None) -> File:
        """
        Create a File object for operations on a single file.
        
        Args:
            path: Path to the target file.
            encoding: Text encoding to use. If None and autodetect_encoding
                is True, encoding will be auto-detected. Otherwise uses
                default_encoding.
        
        Returns:
            File object configured for the specified file.
        
        Raises:
            FileNotFoundError: If the specified file does not exist.
            PermissionError: If read access to the file is denied.
            IsADirectoryError: If the path points to a directory.
        
        Examples:
            >>> file = shell.file('config.ini')
            >>> content = file.read()
            >>> file.write('new content')
            >>> file.append('additional data')
        """
        ...
    
    def files(self, *args: FileTp, encoding: str|None = None) -> Files:
        """
        Create a _files object for batch operations on multiple files.
        
        Args:
            *args: Variable number of file paths or File objects.
            encoding: Encoding to use for text operations on all files.
                Overrides individual file encodings.
        
        Returns:
            _files object for batch operations.
        
        Examples:
            >>> # Batch read
            >>> all_content = shell.files('a.txt', 'b.txt', 'c.txt').read()
            >>> 
            >>> # Batch copy
            >>> shell.files('*.txt').copy_to('backup/')
        """
        ...
    
    # Directory Operations
    def cd(self, path: DirTp) -> 'UniShell':
        """
        Change current working directory.
        
        Args:
            path: New working directory path.
        
        Returns:
            Self for method chaining.
        
        Raises:
            FileNotFoundError: If directory doesn't exist.
            NotADirectoryError: If path is not a directory.
            PermissionError: If directory access is denied.
        
        Examples:
            >>> shell.cd('/home/user').cd('projects')
            <UniShell cur_dir=/home/user/projects>
        """
        ...
    
    def mkdir(
        self,
        path: DirTp,
        mode: int = 0o777,
        parents: bool = False,
        exist_ok: bool = False,
        ignore_errors: bool = False
    ) -> 'UniShell':
        """
        Create a new directory.
        
        Args:
            path: Directory path to create.
            mode: Permission mode (Unix-style octal). Defaults to 0o777.
            parents: Create parent directories if they don't exist.
            exist_ok: Don't raise error if directory already exists.
            ignore_errors: Continue execution on errors.
        
        Returns:
            Self for method chaining.
        
        Raises:
            FileExistsError: If directory exists and exist_ok is False.
            PermissionError: If parent directory is not writable.
        
        Examples:
            >>> shell.mkdir('logs/2024/01', parents=True)
            >>> shell.mkdir('temp', mode=0o755, exist_ok=True)
        """
        ...
    
    def rmdir(
        self,
        path: FileTp,
        ignore_errors: bool = False,
        onerror: Optional[Any] = None
    ) -> 'UniShell':
        """
        Recursively delete a directory and all its contents.
        
        Args:
            path: Directory path to delete.
            ignore_errors: Continue execution on errors.
            onerror: Error handler callback. If provided, called with
                (function, path, excinfo) on errors.
        
        Returns:
            Self for method chaining.
        
        Warning:
            This operation is irreversible. Use with caution.
        
        Examples:
            >>> shell.rmdir('temp_backup/', ignore_errors=True)
        """
        ...
    
    # File System Operations
    def copy(
        self,
        from_path: FileDirTp,
        to_path: FileDirTp,
        *,
        follow_symlinks: bool = True,
        ignore_errors: bool = False
    ) -> 'UniShell':
        """
        Copy file or directory recursively.
        
        Args:
            from_path: Source path (file or directory).
            to_path: Destination path.
            follow_symlinks: Follow symbolic links. If False, copies
                symlinks as symlinks.
            ignore_errors: Continue execution on errors.
        
        Returns:
            Self for method chaining.
        
        Raises:
            FileNotFoundError: If source doesn't exist.
            PermissionError: If destination is not writable.
            IsADirectoryError: If copying file to directory without
                specifying filename.
        
        Examples:
            >>> shell.copy('source.txt', 'dest.txt')
            >>> shell.copy('src/', 'backup/src/')
            >>> shell.copy('data.db', 'backup/', follow_symlinks=False)
        """
        ...
    
    def mkfile(
        self,
        path: FileDirTp,
        ignore_errors: bool = False
    ) -> 'UniShell':
        """
        Create an empty file.
        
        Args:
            path: File path to create.
            ignore_errors: Continue execution on errors.
        
        Returns:
            Self for method chaining.
        
        Raises:
            FileExistsError: If file already exists.
            PermissionError: If directory is not writable.
        
        Examples:
            >>> shell.mkfile('empty.txt')
            >>> shell.mkfile('config/.gitkeep', ignore_errors=True)
        """
        ...
    
    def rmfile(
        self,
        path: FileDirTp,
        ignore_errors: bool = False
    ) -> 'UniShell':
        """
        Delete a file.
        
        Args:
            path: File path to delete.
            ignore_errors: Continue execution on errors.
        
        Returns:
            Self for method chaining.
        
        Raises:
            FileNotFoundError: If file doesn't exist.
            PermissionError: If file is not deletable.
            IsADirectoryError: If path points to a directory.
        
        Examples:
            >>> shell.rmfile('temp.txt')
            >>> shell.rmfile('*.tmp', ignore_errors=True)
        """
        ...
    
    # Archive Operations
    def make_archive(
        self,
        from_path: FileDirTp,
        to_path: FileTp|None = None,
        format: str = "zip",
        owner: str|None = None,
        group: str|None = None,
        ignore_errors: bool = False
    ) -> 'UniShell':
        """
        Create archive from file or directory.
        
        Supported formats: 'zip', 'tar', 'gztar', 'bztar', 'xztar'.
        
        Args:
            from_path: Source to archive (file or directory).
            to_path: Archive destination path. If None, creates archive
                with same name as source in current directory.
            format: Archive format. Defaults to 'zip'.
            owner: Set owner for archive entries (Unix only).
            group: Set group for archive entries (Unix only).
            ignore_errors: Continue execution on errors.
        
        Returns:
            Self for method chaining.
        
        Raises:
            FileNotFoundError: If source doesn't exist.
            ValueError: If format is not supported.
        
        Examples:
            >>> shell.make_archive('project/', 'backup.zip')
            >>> shell.make_archive('data/', format='gztar')
            >>> shell.make_archive('logs/', 'logs.tar.gz', format='gztar')
        """
        ...
    
    def extract_archive(
        self,
        archive_path: FileTp,
        extract_dir: FileTp|None = None,
        format: str|None = None,
        ignore_errors: bool = False
    ) -> 'UniShell':
        """
        Extract archive contents to directory.
        
        Args:
            archive_path: Path to archive file.
            extract_dir: Destination directory. If None, extracts to
                current directory.
            format: Archive format. If None, auto-detected from extension.
            ignore_errors: Continue execution on errors.
        
        Returns:
            Self for method chaining.
        
        Raises:
            FileNotFoundError: If archive doesn't exist.
            ValueError: If format cannot be determined.
            ArchiveError: If archive is corrupt or invalid.
        
        Examples:
            >>> shell.extract_archive('data.zip', 'extracted/')
            >>> shell.extract_archive('backup.tar.gz')
            >>> shell.extract_archive('archive.unknown', format='zip')
        """
        ...
    
    # Permissions and Attributes
    def chmod(
        self,
        path: FileTp,
        mode: int,
        ignore_errors: bool = False
    ) -> 'UniShell':
        """
        Change file or directory permissions.
        
        Args:
            path: Target path.
            mode: New permission mode (Unix-style octal).
            ignore_errors: Continue execution on errors.
        
        Returns:
            Self for method chaining.
        
        Raises:
            FileNotFoundError: If path doesn't exist.
            PermissionError: If lacking permission to change mode.
        
        Note:
            On Windows, only the read-only flag is supported.
        
        Examples:
            >>> shell.chmod('script.sh', 0o755)
            >>> shell.chmod('secret.txt', 0o600)
        """
        ...
    
    # Encoding Operations
    def recode(
        self,
        file_path: FileTp,
        to_encoding: str,
        from_encoding: str|None = None,
        ignore_errors: bool = False
    ) -> 'UniShell':
        """
        Convert file text encoding.
        
        Args:
            file_path: Path to file to convert.
            to_encoding: Target encoding.
            from_encoding: Source encoding. If None, auto-detected.
            ignore_errors: Continue execution on errors.
        
        Returns:
            Self for method chaining.
        
        Raises:
            FileNotFoundError: If file doesn't exist.
            EncodingError: If encoding conversion fails.
            UnicodeError: If text cannot be decoded/encoded.
        
        Examples:
            >>> shell.recode('old.txt', 'utf-8', 'windows-1251')
            >>> shell.recode('data.csv', 'utf-8')  # auto-detect source
        """
        ...
    
    # Utility Operations
    def nano(
        self,
        path: FileTp,
        edit_txt: str = "notepad",
        ignore_errors: bool = False
    ) -> 'UniShell':
        """
        Open file in text editor.
        
        Args:
            path: File to edit.
            edit_txt: Editor command or executable name.
                Defaults to 'notepad' on Windows.
            ignore_errors: Continue execution on errors.
        
        Returns:
            Self for method chaining.
        
        Raises:
            FileNotFoundError: If file doesn't exist.
            OSError: If editor cannot be launched.
        
        Examples:
            >>> shell.nano('config.ini')
            >>> shell.nano('notes.txt', edit_txt='vim')
        """
        ...
    
    def remove(
        self,
        path: FileDirTp,
        ignore_errors: bool = False
    ) -> 'UniShell':
        """
        Remove file or directory recursively.
        
        Args:
            path: Path to remove.
            ignore_errors: Continue execution on errors.
        
        Returns:
            Self for method chaining.
        
        Warning:
            Directory removal is recursive and irreversible.
        
        Examples:
            >>> shell.remove('temp_file.tmp')
            >>> shell.remove('old_backup/', ignore_errors=True)
        """
        ...
    
    def make(
        self,
        path: FileDirTp,
        is_file: bool|None = None,
        ignore_errors: bool = False
    ) -> 'UniShell':
        """
        Create directory path and optionally a file.
        
        Args:
            path: Path to create.
            is_file: If True, creates empty file at path. If False,
                creates directory. If None, determines from path
                (creates file if path has extension).
            ignore_errors: Continue execution on errors.
        
        Returns:
            Self for method chaining.
        
        Examples:
            >>> shell.make('a/b/c/file.txt')  # Creates dirs and file
            >>> shell.make('logs/', is_file=False)  # Creates directory only
        """
        ...
    
    @overload
    def ls(self, path: DirTp = ".", details: bool = False, 
           ignore_errors: bool = False) -> List[str]: ...
    
    @overload
    def ls(self, path: DirTp = ".", details: bool = True,
           ignore_errors: bool = False) -> Dict[str, Any]: ...
    
    def ls(
        self,
        path: DirTp = ".",
        details: bool = False,
        ignore_errors: bool = False
    ) -> Union[List[str], Dict[str, Any]]:
        """
        List directory contents.
        
        Args:
            path: Directory to list. Defaults to current directory.
            details: If True, returns detailed file information.
                If False, returns only filenames.
            ignore_errors: Continue execution on errors.
        
        Returns:
            If details=False: List of filename strings.
            If details=True: Dictionary mapping filenames to file
                information dictionaries with keys: size, is_dir,
                created, modified, mode, etc.
        
        Raises:
            FileNotFoundError: If directory doesn't exist.
            NotADirectoryError: If path is not a directory.
        
        Examples:
            >>> # Simple listing
            >>> files = shell.ls('.')
            ['file1.txt', 'file2.txt', 'subdir']
            
            >>> # Detailed listing
            >>> details = shell.ls('.', details=True)
            {'file1.txt': {'size': 1024, 'is_dir': False, ...}}
        """
        ...
    
    # Aliases (for convenience)
    def touch(self, path: Union[str, Path], ignore_errors: bool = False) -> 'UniShell':
        """Alias for mkfile(). Create empty file."""
        ...
    
    def rm(self, path: Union[str, Path], ignore_errors: bool = False) -> 'UniShell':
        """Alias for remove(). Delete file or directory."""
        ...
    
    def rmtree(self, path: Union[str, Path], ignore_errors: bool = False) -> 'UniShell':
        """Alias for rmdir(). Recursively delete directory."""
        ...
    
    def mk_archive(
        self,
        from_path: Union[str, Path],
        to_path: Optional[Union[str, Path]] = None,
        format: str = "zip",
        ignore_errors: bool = False
    ) -> 'UniShell':
        """Alias for make_archive()."""
        ...
    
    mkarch = mk_archive
    
    def unpack_archive(
        self,
        archive_path: Union[str, Path],
        extract_dir: Optional[Union[str, Path]] = None,
        format: Optional[str] = None,
        ignore_errors: bool = False
    ) -> 'UniShell':
        """Alias for extract_archive()."""
        ...
    
    unparch = unpack_archive
    unp_arch = unpack_archive
    ext_arch = unpack_archive
    extarch = unpack_archive
    
    def convert_encoding(
        self,
        file_path: Union[str, Path],
        to_encoding: str,
        from_encoding: Optional[str] = None,
        ignore_errors: bool = False
    ) -> 'UniShell':
        """Alias for recode()."""
        ...
    
    # Magic Methods
    def __str__(self) -> str:
        """
        String representation of UniShell instance.
        
        Returns:
            String of current working directory.
        """
        ...
    
    def __repr__(self) -> str:
        """
        Official string representation for debugging.
        
        Returns:
            String in format: <UniShell cur_dir=/path/to/dir>
        """
        ...
sh: UniShell
