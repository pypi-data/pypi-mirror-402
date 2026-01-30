from __future__ import annotations

import winreg  
from typing import Iterator, TYPE_CHECKING

if TYPE_CHECKING:
    from .UserType import CurrentUser, User, Users
from .core import RegPage
class ProgId(RegPage):
	"""
	run :Path - open"""
	_regpath = r"Software\Classes"
	def get(self, name: str) -> str:
		"""Получает по имени """
		...
	def set(self,name,run,icon = None):
		"""Полностью перезаписывает обьект"""
		...
	def add(self,run,icon = None):
		"""Атрибуты добавляются в случае конфликта перезаписываются"""
		...
	def pop(self,name):
		"""Удаляет обьект"""
		...


class FileType(RegPage):
	_regpath = r"Software\Classes"
	
		
	def add_progid(self,name,run, descr = "", icon = ""):
		"""
		Создает новый ProgId
		"""
		...
	def add_extension(self, name = "", default_progid = None, progids = []):
		"""
        Создает новый тип файла в реестре Windows.
		default_progid: str = None,
        """
		...
	def add(self, extension,run,progid,default_progid = None, progids = []) -> None:
		if progid:
			self.add_progid(progid,run,descr,icon)
	
	def pop(self, name: str) -> None:
		"""Удалить программу из автозагрузки"""
		try:
			with winreg.OpenKey(self.hive, self.key_path, 0, winreg.KEY_WRITE) as key:
				winreg.DeleteValue(key, name)
		except FileNotFoundError:
			pass
	
	def all(self) -> dict[str, str]:
		"""Получить все программы в автозагрузке: {имя: путь}"""
		result = {}
		with winreg.OpenKey(self.hive, self.key_path) as key:
			count = winreg.QueryInfoKey(key)[1]
			for i in range(count):
				name, value, _ = winreg.EnumValue(key, i)
				result[name] = value
		return result
	
	def keys(self) -> list[str]:
		"""Получить список имен программ"""
		return list(self.all().keys())
	
	def values(self) -> list[str]:
		"""Получить список путей программ"""
		return list(self.all().values())
	
	def items(self) -> list[tuple[str, str]]:
		"""Получить список пар (имя, путь)"""
		return list(self.all().items())
	
	def __iter__(self) -> Iterator[str]:
		"""Итерация по именам программ"""
		return iter(self.keys())
	
	def __len__(self) -> int:
		"""Количество программ в автозагрузке"""
		return len(self.keys())
	
	def __getitem__(self, key: str|int) -> str:
		if isinstance(key, int):
			return self.keys()[key]
		elif isinstance(key, str):
			return self.get(key)
		else:
			raise TypeError(f"Invalid key type: {type(key)}")
	
	def __setitem__(self, name: str, path: str) -> None:
		self.set(name, path)
	
	def __delitem__(self, name: str) -> None:
		self.pop(name)
	
	def __contains__(self, name: str) -> bool:
		try:
			self.get(name)
			return True
		except:
			return False
	
	def __repr__(self) -> str:
		return f"<AutoRun: {self.all()}>"