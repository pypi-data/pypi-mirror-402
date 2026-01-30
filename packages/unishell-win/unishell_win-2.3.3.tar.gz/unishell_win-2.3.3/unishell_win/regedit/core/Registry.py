import winreg
from typing import Optional, Union, List, Dict, Any

from ..reg_types import \
	_REG_TYPE_AUTO, STRING, \
    _REG_TYPE_INT,_REG_TYPE_STR, \
	_HKEY_INT,_HKEY_STR
from .UserType import _get_winreg_hkey,_get_winreg_subkey,UserTp







class Container:
	"""Registry container (key)"""
	
	def __init__(self, hive: int, path: str = ""):
		self.hive = hive
		self.path = path.strip("\\")
	
	def __truediv__(self, subpath: str) -> 'Container':
		
		if self.path:
			new_path = f"{self.path}\\{subpath}"
		else:
			new_path = subpath
		
		return Container(self.hive, new_path)
	
	def __getitem__(self, name: str) -> Optional[Any]:
		field = Field(self, name)
		return field.get()
	
	def __setitem__(self, name: str, value: Any):
		field = Field(self, name)
		field.set(value)
	
	def __delitem__(self, name: str):
		field = Field(self, name)
		field.delete()
	
	def _open(self, access=winreg.KEY_READ):
		"""Open registry key"""
		try:
			if self.path:
				return winreg.OpenKey(self.hive, self.path, 0, access)
			else:
				return winreg.OpenKey(self.hive, "", 0, access)
		except FileNotFoundError:
			raise FileNotFoundError(f"Container not found: {self.path}")
		except Exception as e:
			raise Exception(f"Error opening container: {e}")
	
	def create(self):
		try:
			if self.path:
				winreg.CreateKey(self.hive, self.path)
		except Exception as e:
			raise Exception(f"Error creating container: {e}")
	
	def delete(self, recursive: bool = True):
		if self.path:
			if recursive:
				for container_name in self.containers():
					sub_container = self / container_name
					sub_container.delete()
				
				for field_name in self.fields():
					self[field_name] = None
					del self[field_name]
			

			if not recursive:
				with self._open(winreg.KEY_READ):
					subkeys = list(self.containers())
					fields = list(self.fields())
				
				if subkeys or fields:
					raise Exception("Container is not empty. Use delete(recursive=True) to force delete.")
			
			if "\\" in self.path:
				parent_path = "\\".join(self.path.split("\\")[:-1])
				key_name = self.path.split("\\")[-1]
				parent = Container(self.hive, parent_path)
				with parent._open(winreg.KEY_WRITE) as parent_key:
					winreg.DeleteKey(parent_key, key_name)
			else:
				winreg.DeleteKey(self.hive, self.path)

	
	def rename(self, new_name: str):
		if "\\" in self.path:
			parent_path = "\\".join(self.path.split("\\")[:-1])
			parent = Container(self.hive, parent_path)
		else:
			parent = Container(self.hive, "")
		
		data = self.json(use_types=True)
		
		new_path = f"{parent.path}\\{new_name}" if parent.path else new_name
		new_container = Container(self.hive, new_path)
		new_container.create()
		
		new_container.from_json(data, use_types=True)
		
		old_container = Container(self.hive, self.path)
		old_container.delete()
		
		self.path = new_path
			

	
	def containers(self):
		result = []

		with self._open() as key:
			i = 0
			while True:
				try:
					result.append( winreg.EnumKey(key, i))
					i += 1
				except OSError:
					break
		return result
	
	def fields(self):
		result = []
		with self._open() as key:
			i = 0
			while True:
				try:
					name, _, _ = winreg.EnumValue(key, i)
					result.append(name)
					i += 1
				except OSError:
					break
		return result
	
	def json(self, use_types = False) -> Dict[str, Any]:
		"""Export container to JSON"""
		result = {}
		
		for field_name in self.fields():
			field = Field(self, field_name)
			value = field.json(use_types = use_types)
			if value is not None:
				result[field_name] = value
		

		for container_name in self.containers():
			sub_container = self / container_name
			result[container_name] = sub_container.json(use_types = use_types)
				
		return result
	
	def from_json(self, data: Dict[str, Any], use_types = False):
		"""Import container from JSON"""

		if not self.exists():
			self.create()
		
		for reg_el in data.keys():
			if not isinstance(data[reg_el], (dict)): # type is field
				field = Field(self,reg_el)
				field.from_json(data[reg_el], use_types = use_types)
			else:
				(self / reg_el).from_json(data[reg_el], use_types = use_types)
		
	def exists(self) -> bool:
		try:
			with self._open():
				return True
		except Exception:
			return False
		
	def __repr__(self) -> str:
		return f"Registry({_HKEY_STR[self.hive]}\\{self.path})"
class Field:
	
	def __init__(self, container: Container, name: str):
		self.container = container
		self.name = name
	
	def get(self,default = None, return_type = False) -> Optional[Any]:
		try:
			with self.container._open() as key:
				value, reg_type = winreg.QueryValueEx(key, self.name)
				if return_type:
					return value,reg_type
				else:
					return value  
		except FileNotFoundError:
			return default

	
	def set(self, value: Any, reg_type: Optional[int] = None):
		if reg_type is None:
			reg_type = _REG_TYPE_AUTO(value) 
		if reg_type == STRING:
			value = str(value)
		
		if not self.container.exists():
			self.container.create()
		
		with self.container._open(winreg.KEY_WRITE) as key:
			winreg.SetValueEx(key, self.name, 0, reg_type, value)
				

	
	def delete(self):
		try:
			with self.container._open(winreg.KEY_WRITE) as key:
				winreg.DeleteValue(key, self.name)
		except FileNotFoundError:
			pass 

	
	def exists(self) -> bool:
		try:
			with self.container._open() as key:
				winreg.QueryValueEx(key, self.name)
				return True
		except Exception:
			return False
	
	def rename(self, new_name: str):
		with self.container._open() as key:
			value, reg_type = winreg.QueryValueEx(key, self.name)
		
		with self.container._open(winreg.KEY_WRITE) as key:
			winreg.SetValueEx(key, new_name, 0, reg_type, value)
		
		self.delete()
	def type(self):
		if self.exists():
			with self.container._open() as key:
				_, reg_type = winreg.QueryValueEx(key, self.name)
				return _REG_TYPE_STR[reg_type]
		else:
			return None
	def json(self, use_types = False) ->  list[Any|str]|Any:
		ans = self.get(return_type = use_types)
		if use_types:
			value, reg_type = ans # type: ignore
			return value, _REG_TYPE_STR[reg_type]
		else:
			return ans
		
	def from_json(self, data, use_types = False):
		if use_types:
			value, reg_type = data
			reg_type = _REG_TYPE_INT[reg_type]
		else:
			value = data
			reg_type = None
		self.set(value, reg_type)
	def __repr__(self) -> str:
		return f"Field({self.container}\\{self.name})"


class Registry:
	
	def __new__(cls, hive: int|str|UserTp) -> Container:
		path = ""
		if isinstance(hive, str):
			hive = _HKEY_INT.get(hive.upper())
		if not isinstance(hive, int):
			path = _get_winreg_subkey(hive)
			hive = _get_winreg_hkey(hive)
		return Container(hive,path)


class RegPage:
	_regpath : str
	_regedit : Container
	def __init__(self, user: UserTp = None) -> None:
		self._regedit = Registry(user) / self._regpath

	

	def get(self,name:str):
		""" Получает значение поля у ключа:
			HKEY_CURRENT_USER\\SOFTWARE\\7-Zip\\Compression\\Options\\7z , Level -> 5
			Reg_SZ -> list
		"""
		return self._regedit[name]


	def add(self,name, value):  self._regedit[name] = value
	def pop(self,name):         del self._regedit[name]
	
	
	def json(self, use_types = False): return self._regedit.json(use_types = use_types)
	def from_json(self, data, use_types = False): self._regedit.from_json(data,use_types = use_types)
		

	def keys(self) -> list[str]:   return self._regedit.fields()
	def values(self):              return [self.get(key) for key in self.keys()]
	def items(self):               return list(zip(self.keys(), self.values()))
	
	def __getitem__(self,name): return self.get(name)
	def __delitem__(self,name): return self.pop(name)
	def __iter__(self):
		for name in self.keys():
			yield name
	def __contains__(self,name): return name in self.keys()
	def __len__(self): return len(self.keys())
	def __repr__(self): return f"<{self.__class__.__name__}> :" + str(self.json())
	def __str__(self): return str(self.json())