from someip_py.codec import *


class IdtLockingFuncOnOff(SomeIpPayload):

    IdtLockingFuncOnOff: Uint8

    def __init__(self):

        self.IdtLockingFuncOnOff = Uint8()
