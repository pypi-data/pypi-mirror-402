from .core.UserType import CurrentUser, User, Users,CurUser
from .core.Registry import Registry,Field

from .core.Environment import Environment as stdEnvironment
from .core.PATH        import PATH        as stdPATH
from .core.AutoRun     import AutoRun     as stdAutoRun
from .core.AutoRunOnce import AutoRunOnce as stdAutoRunOnce



PATH = stdPATH(CurUser)
AutoRun = stdAutoRun(CurUser)
AutoRunOnce = stdAutoRunOnce(CurUser)
Environment = stdEnvironment(CurUser)
