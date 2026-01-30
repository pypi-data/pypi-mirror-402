from .._internal.structures import Dir,File,Archive
try:
    from unishell_win import Users,CurUser
except ImportError:
    print("Not found module: 'unishell_win'. pip install unishell_win")
import sys
NAME_PROJECT = "Project"
VERSION_PROJECT = "1.1.1"
DIR_FROM_PROJECT = Dir("")
DIR_FOR_PROJECT = "C:/Program files"
MAIN_DIR = DIR_FOR_PROJECT + NAME_PROJECT
    
ALL_USERS = False
PATH = ["C:/Program files/my_project"]
AutoRun = (1,)
AutoRunOnce = (1,)

BASE_DIR_FOR_PROJECT = "C:/Program files"
BASE_DIR_FROM_PROJECT = Dir("sys.MEIPASS")

def json(cls):
    data = {}
    for el, value in cls.__dict__.items():
        if el.startswith("__"):
            continue
        elif isinstance(value, type):
            data[el] = json(value)
        else:
            data[el] = value
    return data
class Config:
    NAME_PROJECT = "Project"
    VERSION_PROJECT = "1.1.1"
    DIR_FROM_PROJECT = NAME_PROJECT
    DIR_FOR_PROJECT = "C:/Program files"
    MAIN_DIR = DIR_FOR_PROJECT + NAME_PROJECT
    
    ALL_USERS = True
    PATH = ["C:/Program files/my_project"]
    
    class FileType:
        class txt:
            run = "path"
            icon = "path"
        class pdf:
            run = "path"
            icon = "path"
    
    class ContextMenu:
        Dir = ( 
            { "text": "Открыть_в_проводнике", "run" : "run", "icon" : "path", "position" : "top|middle|bottom",},
        ) 
        File =  (
            { "text": "Открыть_в_проводнике", "icon" : "path", "position" : "top|middle|bottom"},
        )



def install_program(DIR_FOR_PROJECT:str = None,ALL_USERS = True, PATH = [],FileType = [], ContextMenu = {"File": [], "Dir": []},**kwargs): # type: ignore
    
    DIR_FOR_PROJECT:Dir = Dir(DIR_FOR_PROJECT or BASE_DIR_FOR_PROJECT)
    ARCHIVED_PROJECT = (DIR_FROM_PROJECT or BASE_DIR_FROM_PROJECT) / NAME_PROJECT # type: ignore
    MAIN_DIR = MAIN_DIR or DIR_FOR_PROJECT/NAME_PROJECT # type: ignore

    if not DIR_FOR_PROJECT.on_disk():
        raise OSError(f"Невозможно получить доступ к директории {DIR_FOR_PROJECT}")
    if type(ARCHIVED_PROJECT) == File and ARCHIVED_PROJECT.on_disk():
        raise OSError(f"Невозможно получить доступ к директории {ARCHIVED_PROJECT}")
    
    MAIN_DIR.create()
    Archive(ARCHIVED_PROJECT.path).extract(path = "")
    USER = ALL_USERS and Users or CurUser
    
    _ = (USER.PATH.add(path) for path in PATH)
    _ = (USER.AutoRun.add(i) for i in AutoRun)
    _ = (USER.FileType.add(extension = file_type, icon = icon, run = run) for file_type,icon_run in FileType for icon,run in icon_run)
    _ = (USER.ContextMenuDir.add (text = text, icon = icon, run = run) for text,icon_run in ContextMenu["Dir"] for icon,run in icon_run )
    _ = (USER.ContextMenuFile.add(text = text, icon = icon, run = run) for text,icon_run in ContextMenu["File"] for icon,run in icon_run )

install_program(**json(Config))