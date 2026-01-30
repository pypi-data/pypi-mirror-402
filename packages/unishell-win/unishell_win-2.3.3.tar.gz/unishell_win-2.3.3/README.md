Unishell is a powerful, cross-platform, and intuitive Python library for working with files, directories, and text data. It provides two API styles: the shell-style unishell.sh_space and the Python-style unishell.

## Two API styles

### 1. UniShell - Shell style
A high-level interface inspired by the Unix command line/Cmd. It automatically expands paths with environment variables (`%VAR%`), special notations (`~`, `..`, `.`), and supports some method chaining. To avoid polluting the global environment, it is recommended to import functions in separate files, create them in them, and then import them in separate modules.

```python
#shell_module.py
from unishell.sh_space import *
def shell_function():
    cd("~")
    mkfile("1.txt")
    file("1.txt") < "data"
```
### 2. Python-style ORM
Classes for working with the file system in an object-oriented style.
```python
#python_module.py
from unishell import File,Unishell
def shell_function():
    sh = UniShell()
    sh.cd("~")
    file = File("1.txt")
    file.create()
    file.content = "data"
```
### Installation for all OS (recommended for development)
```bash
pip install unishell
```
### Installation for Windows only
```bash
pip install unishell_win
```
### Installation only for Linux (Unix systems)
```bash
pip install unishell_unix
```
### Main modules
1. Working with files and folders    
    Create, edit, delete, move, copy files and folders with automatic path expansion.
    ```python
    from unishell import shell
    ```
2. Working with encodings  
    Allows recognition and recoding into minimal encoding.
    Functions:
    ```python
    from unishell import detect_encoding,determine_minimal_encoding
    ```
    Dependencies: chardet (LGPL) - for automatic encoding detection.  

3. Working with archives   
    Editing archives with passwords and extracting individual files. Multiple formats are supported. Requires appropriate libraries.
    ```python
    from unishell import Archive
    ```
    Dependencies: py7zr (LGPL-2.1), pyzipper (MIT), rarfile (ISC)
4. Working with the Windows registry.
    Create and delete users by SID, change passwords. Edit PATH, AutoRun, and AutoRunOnce.
    CurrentUser, User, Users
    ```python
    from unishell import CurUser, User, Users,PATH, AutoRun, AutoRunOnce
    ```
    Dependencies: pywin32(PSF)  

## Implementation Features

1. **Cross-platform** - a single API for Windows, Linux, and macOS
2. **Two API levels** - shell-style (UniShell) and Python-style (ORM)
3. **PropCase(PropertyCase)** - many attributes are changed through properties.
4. **Avoiding exceptions** - Most commands avoid exceptions, returning None when necessary.
5. **Lazy operations** - files are read and created only when necessary
6. **Stream operations** - support for operators >>, >, <<, < for working with content

## License

UniShell is distributed under the **MIT License**. See the LICENSE file for details.

### Dependency Licenses

The project uses the following dependencies and their licenses:

- **chardet** — LGPL
- **py7zr** — LGPL-2.1-or-later
- **pyzipper** — MIT
- **rarfile** — ISC
- **pywin32** - PSF (Python Software Foundation License)

All dependencies are compatible with the MIT License.   
**Requirements:**
- Python 3.10+

### Documentation
# UniShell API: Complete list of signatures with examples (AI-generated)
### Constructor
```python
shell = UniShell(
    sep: str = "\n",
    current_dir = os.getcwd(),
    default_encoding: str = 'utf-8',
    autodetect_encoding: bool = False,
    parms : ViewPort = ViewPort()
)
```

### Methods

#### file
```python
def file(self, path: str | Path, encoding: str|None = None) -> File
sh.file("demo.txt")
```

#### files
```python
def files(self, *files: str|Path|File, encoding: str|None = None, sep="\n") -> Files
sh.files("1.txt","2.txt")
```

#### cd
```python
def cd(self, path: str|Path) -> UniShell
sh.cd("..")
```

#### copy
```python
def copy(self, from_path: str|Path, to_path: str|Path, *, follow_symlinks=True, ignore_errors=False) -> UniShell
sh.copy("a.txt", "b.txt")
```

#### mkdir
```python
def mkdir(self, path: str|Path, mode=0o777, parents=False, exist_ok=False, ignore_errors=False) -> UniShell
sh.mkdir("d")
```

#### mkfile
```python
def mkfile(self, path: str|Path, ignore_errors=False) -> UniShell
sh.mkfile("new.txt")
```

#### rmfile
```python
def rmfile(self, path: str|Path, ignore_errors=False) -> UniShell
sh.rmfile("f.txt")
```

#### rmdir
```python
def rmdir(self, path: str|Path, ignore_errors=False, onexc=None) -> UniShell
sh.rmdir("folder")
```

#### make_archive
```python
def make_archive(self, from_path: str|Path, to_path: str|Path|None = None, format: str = "zip", owner: Optional[str] = None, group: Optional[str] = None, ignore_errors: bool = False) -> UniShell
sh.make_archive("f", "f.zip")
```

#### extract_archive
```python
def extract_archive(self, archive_path: str|Path, extract_dir: Optional[str|Path]=None, format=None, ignore_errors=False) -> UniShell
sh.extract_archive("f.zip", "outdir")
```

#### chmod
```python
def chmod(self, path: str|Path, mode: int, ignore_errors=False) -> UniShell
sh.chmod("file.txt", 0o400)
```

#### nano
```python
def nano(self, path: str|Path, edit_txt="notepad", ignore_errors=False) -> UniShell
sh.nano("t.txt")
```

#### remove
```python
def remove(self, path: str|Path, ignore_errors=False) -> UniShell
sh.remove("obj.txt")
```

#### make
```python
def make(self, path: str|Path, is_file: bool|None = None, ignore_errors: bool = False) -> UniShell
sh.make("demo.dir", is_file=False)
```

#### ls
```python
def ls(self, path: str|Path = ".", details: bool = False, ignore_errors: bool = False) -> Union[list[str], dict[str,Any]]
sh.ls("some_dir", details=True)
```

#### to_abspath
```python
def to_abspath(self, path:str|Path|File|Dir) -> Path
sh.to_abspath("~/%USER%/1.txt")
```

#### recode
```python
def recode(self, file_path: str|Path, to_encoding: str, from_encoding: Optional[str]=None, ignore_errors: bool = False) -> UniShell
sh.recode("ru.txt", to_encoding="cp1251")
```

#### parms
```python
sh.parms["TEST"] = "value"
print(sh.parms.all())
```

---

## File
```python
f = File("test.txt", encoding="utf-8")
```
- content: str (property)
- @content.setter (content: str)
- @contentdeleter
- create(mode=438, ignore_errors=True) -> File
- remove() -> None
- nano(edit_txt="notepad") -> None
- chmod(mode: int) -> None
- recode(to_encoding=None, from_encoding=None) -> None
- name: str
- parent: Dir
- extension: str
- on_disk() -> bool
- sizeof() -> int
- created_utc(), modified_utc(), accessed_utc() -> datetime
- created_lcl(), modified_lcl(), accessed_lcl() -> datetime
- is_symlink() -> bool
- hidden (property)
- metadata() -> dict

#### Examples:
```python
f = File("tt.txt")
f.content = "123"
f.create()
f.metadata()
f.chmod(0o777)
f.remove()
```

---

## Dir
```python
d = Dir("data/")
```
- create(mode=0o777, parents=False, ignore_errors=False) -> None
- add(path) -> Dir
- move_to(dir) -> Dir
- rename(new_name) -> None
- on_disk() -> bool
- chmod(mode) -> None
- name (property): str
- parent (property): Dir
- hidden (property): bool
- hidden.setter: bool
- len_files_and_dirs(recursive=True, symlinks=False) -> dict
- sizeof(recursive=True, symlink=False) -> int
- created_utc, modified_utc, accessed_utc() -> datetime
- created_lcl, modified_lcl, accessed_lcl() -> datetime
- is_symlink() -> bool
- metadata() -> dict
- __truediv__(name)
- __iter__()
- __str__()
- __repr__()

#### Example:
dir = Dir("a")
dir.create()
for entry in dir:
    print(entry)
dir.hidden = True


---

## Files
```python
f = Files("a.txt", "b.txt")
f.files # list[File]
```
- __stream_getData__() -> str

---

## Archive
```python
arc = Archive("z.zip")
```
- __init__(path: Path|str, format: str|None=None, password: str|None=None)
- __iter__() -> Iterator[str]
- add(path, arcname=None) -> None
- extract(member=None, path=".") -> None
- list_files() -> list[str]
- create() -> Archive
- create_from(path, format, files: list, password=None) -> Archive [classmethod]

#### Example:
arc.add("1.txt")
print(list(arc))
arc.extract(path="out")

---

## ViewPort
```python
v = ViewPort()
v["A"] = 12
print("A" in v)
```
- set_gl(name: str, value: str)
- del_gl(name: str)
- all() -> dict
- set_(name: str, value:Any, link=False)
- sets(parms: dict, link=False)
- del_(name: str)
- dels(parms: list)
- __getitem__, __setitem__, __delitem__, __contains__

---

## encoding_utils
```python
detect_encoding(path, sample_size=65536, ignore_errors=False) -> Optional[str]
determine_minimal_encoding(content: str) -> str
check_bom(data: bytes) -> Optional[str]
```
#### Example:
determine_minimal_encoding("text")

---

## unishell_win.regedit
### User/CurrentUser/Users
- User(id=None, name=None, domain="")
    - .create(name, password, ...)
    - .delete()
    - .password_chg(old,new)
    - .exists(id=None, name=None, domain="") [staticmethod]
    - .getCurUserSid() [staticmethod]
    - id, name, domain, type (property)
    - PATH, AutoRun, AutoRunOnce (property)
    - __repr__
- Users.local() -> list[User]
- Users.all(name=None, domain=None) -> list[User]
- __iter__
- __repr__

#### Examples:
u = User.create("u1","1234")
Users.all()
print(u.id, u.name)

### PATH
PATH(user: User|CurrentUser|Users|str|None = None)
- add(path)
- pop(path)
- all() -> list[str]
- get()
- __contains__, __iter__, __getitem__, __setitem__, __delitem__, __len__, __repr__, __str__

#### Example:
PATH.add(r"C:\bin")
PATH[0]

### AutoRun, AutoRunOnce
AutoRun(user: ... = None)
- add(name, path)
- set(name, path)
- pop(name)
- get(name)
- all() -> dict[str, str]
- keys() -> list[str]
- values() -> list[str]
- items() -> list[tuple[str,str]]
- __contains__, __iter__, __getitem__, __setitem__, __delitem__, __len__, __repr__

#### Example:
AutoRun.add("App", r"C:\path\app.exe")
print(AutoRun[0], AutoRun["App"])

---
