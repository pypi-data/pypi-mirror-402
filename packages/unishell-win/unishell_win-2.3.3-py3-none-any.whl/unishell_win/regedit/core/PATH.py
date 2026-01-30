from .UserType import UserTp,Users
from .Registry import RegPage

class PATH(RegPage):
	_regpath = r"Environment"
	"""
	user: CurrentUser | User | Users | User_id:str | None
	PATH(user).add(path)
			   .pop(path)
			   .all()
	for path in PATH(user):
		pass
	for i in range(len(PATH(user))):
		PATH(user[i])
	"""

	def __init__(self, user: UserTp = None) -> None:

		if isinstance(user, Users):
			self._regpath = r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"
		super().__init__(user)


	def get(self) -> list[str]:
		try:
			return self._regedit["Path"].split(';') # type: ignore
		except FileNotFoundError:
			return []



	def add(self, path: str):
		paths = self.get()
		if path not in paths:
			paths.append(path)
			self._regedit["Path"] = ';'.join(paths)
	def insert(self, index: int, path: str):
		self._regedit["Path"] = self.get().insert(index,path)

	def pop(self, path: str) -> None:
		paths = [p for p in self.get() if p != path]
		self._regedit["Path"] = ';'.join(paths)

	def json(self) -> list[str]: return self.get()
	def from_json(self, data:list[str]):   self._regedit["Path"] = ';'.join(data)
	def keys(self) -> list[str]:   return self.get()
	def values(self) -> list[str]: return self.get()