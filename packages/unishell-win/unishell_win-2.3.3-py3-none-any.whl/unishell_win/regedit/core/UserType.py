from __future__ import annotations
import ctypes
try:
	import winreg  
	import win32api 
	import win32security  
	import win32net  
	import win32netcon  
except ImportError:
	print("Not found module pywin32. pip install pywin32")

class User:
	_id :str|None = ""

	def __init__(self, id = None, name = None, domain = ""):
		domain = None if domain == "" else domain

		if domain and domain in (win32api.GetComputerName(), ".", ""):
			domain = None
		
		if id and type(self).exists(id, domain = domain): # type: ignore
			self._id = id
		elif name:
			locations = [domain] if domain is not None else [None]
			if domain is not None:
				locations.append(None)
			
			for try_domain in locations:
				try:
					sid, found_domain, use = win32security.LookupAccountName(try_domain, name)
					self._id = win32security.ConvertSidToStringSid(sid)
					return
				except win32security.error:
					continue
			
			raise ValueError(f"Not found user sid = {id}, domain = {domain}, name = {name}")
		else:
			raise ValueError(f"Not found user sid = {id}, domain = {domain}, name = {name}")

	@classmethod
	def create(cls, name: str = "", password: str = "",
			   domain = None, 
			   full_name: str = "", description: str = "", 
			   flags: int = win32netcon.UF_NORMAL_ACCOUNT | win32netcon.UF_SCRIPT,
			   priv: int = win32netcon.USER_PRIV_USER) -> "User":
		"""
		Создает нового пользователя Windows.
		
		Args:
			name: Имя пользователя (обязательно)
			password: Пароль (пустая строка = пароль не требуется)
			full_name: Полное имя пользователя
			description: Описание
			flags: Флаги учетной записи
			priv: Уровень привилегий			
		"""
		user_info = {
			'name': name,
			'password': password,
			'priv': priv,
			'home_dir': None,
			'comment': description,
			'flags': flags,
			'script_path': None
		}
		
		if full_name:
			user_info['full_name'] = full_name
		
		win32net.NetUserAdd(
			domain,
			1,              # уровень информации
			user_info
		)
		print(win32net.error)	
		return User(name = name)
	
	def delete(self):
		win32net.NetUserDel(self.domain, self.name) # type: ignore
	
	def password_chg(self, old: str, new: str, domain = "") -> bool:
		netapi32 = ctypes.windll.netapi32
		result = netapi32.NetUserChangePassword(
			None if domain == "" else domain,
			self.name,
			old,
			new
		)
		return result == 0 

	@staticmethod
	def getCurUserSid():
		sid, domain, sid_type = win32security.LookupAccountName(None, win32api.GetUserName())
		id = win32security.ConvertSidToStringSid(sid)
		return id
	@staticmethod
	def exists(id:str|None = None, name = None, domain = ""):
		domain = None if domain == "" else domain
		try:
			if id: 
				sid = win32security.ConvertStringSidToSid(id)
				win32security.LookupAccountSid(domain, sid)
			elif name:  
				win32security.LookupAccountName(domain, name)
			else:
				return False
			return True
		except win32security.error as e:
			return False
	
	
	#properties
	def get_id(self):
		return self._id
	def set_id(self,value): ...
	def get_name(self):
		sid = win32security.ConvertStringSidToSid(self.id) # type: ignore
		username, domain, sid_type = win32security.LookupAccountSid(None, sid)
		return username
	def set_name(self,value): ...
	def get_domain(self) -> str:
		sid = win32security.ConvertStringSidToSid(self.id) # type: ignore
		username, domain, sid_type = win32security.LookupAccountSid(None, sid)
		return domain
	def set_domain(self,value): ...
	def get_type(self):
		if self._id is None: return None
		sid = win32security.ConvertStringSidToSid(self.id)
		username, domain, sid_type = win32security.LookupAccountSid(None, sid)

		type_names = {
			win32security.SidTypeUser: "User",
			win32security.SidTypeGroup: "Group",
			win32security.SidTypeAlias: "Alias",
			win32security.SidTypeWellKnownGroup: "WellKnownGroup", 
			win32security.SidTypeComputer: "Computer",
			win32security.SidTypeDomain: "Domain"
		}

		return type_names.get(sid_type, None)
	def set_type(self,value):...
	
	id     = property(get_id,set_id,doc = "SID пользователя") #"SID пользователя"
	name   = property(get_name,set_name)
	domain = property(get_domain,set_domain)
	type   = property(get_type,set_type)
	
	def __repr__(self):
		return f"User <id = {self.id},name = {self.name}, domain = {self.domain},type = {self.type}>"

	@property
	def PATH(self):
		from .PATH import PATH as stdPATH
		return stdPATH(self)
	
	@property
	def AutoRun(self):
		from .AutoRun import AutoRun as stdAutoRun
		return stdAutoRun(self)
	
	@property
	def AutoRunOnce(self):
		from .AutoRunOnce import AutoRunOnce as stdAutoRunOnce
		return stdAutoRunOnce(self)


class CurrentUser(User):
	def __init__(self):
		self._id = User.getCurUserSid()
	def get_id(self):
		return super().get_id()
	def set_id(self, value):
		raise ValueError("Must not id CurrentUser")
	
	def __repr__(self):
		return f"Current User <id = {self.id},name = {self.name}, domain = {self.domain},type = {self.type}>"
	



class Users:
	@staticmethod
	def local() -> list[User]:
		"""Список пользователей на данном ПК"""
		server = ""
		level = 0
		filter_flag = 0 
		resume_handle = 0
		
		result = win32net.NetUserEnum(
			server, 
			level, 
			filter_flag, 
			resume_handle, 
		)
		return [User(name=user['name']) for user in result[0]]

	@staticmethod
	def all( name = None, domain = None) -> list[User]:...
	
	@property
	def PATH(self):
		from .PATH import PATH as stdPATH
		return stdPATH(self)
	
	@property
	def AutoRun(self):
		from .AutoRun import AutoRun as stdAutoRun
		return stdAutoRun(self)
	
	@property
	def AutoRunOnce(self):
		from .AutoRunOnce import AutoRunOnce as stdAutoRunOnce
		return stdAutoRunOnce(self)
	
	@classmethod
	def __iter__(cls):
		return iter(cls.local())
	
	@classmethod
	def __repr__(cls) -> str:
		return f"<Users {cls.local()}>"

def _get_winreg_hkey(user: "CurrentUser|User|Users|str|None") -> int:
	if isinstance(user, str):
		return winreg.HKEY_USERS
	elif user is None or isinstance(user, CurrentUser):
		return winreg.HKEY_CURRENT_USER
	elif isinstance(user, User):
		return winreg.HKEY_USERS
	elif isinstance(user, Users):
		return winreg.HKEY_LOCAL_MACHINE
	else:
		raise ValueError(f"Invalid user type: {type(user)}")
def _get_winreg_subkey(user: "CurrentUser|User|Users|str|None") -> str:
	if isinstance(user, str):
		return user
	elif user is None or isinstance(user, CurrentUser):
		return ""
	elif isinstance(user, User):
		return user.id
	elif isinstance(user, Users):
		return ""
	else:
		raise ValueError(f"Invalid user type: {type(user)}")

UserTp = User|Users|CurrentUser|str|None
CurUser = CurrentUser()

