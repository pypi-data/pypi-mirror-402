from .Registry import RegPage
from .UserType import UserTp,Users

class Environment(RegPage):
    _regpath = r"Environment"
    def __init__(self, user: UserTp = None) -> None:

        if isinstance(user, Users):
            self._regpath = r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"
        super().__init__(user)
        