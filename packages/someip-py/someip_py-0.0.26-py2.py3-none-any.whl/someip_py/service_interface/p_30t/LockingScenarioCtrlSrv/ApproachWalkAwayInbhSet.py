from someip_py.codec import *


class IdtLockingOnOffReq(SomeIpPayload):

    IdtLockingOnOffReq: Uint8

    def __init__(self):

        self.IdtLockingOnOffReq = Uint8()


class IdtInhbTrigSrc(SomeIpPayload):

    IdtInhbTrigSrc: Uint8

    def __init__(self):

        self.IdtInhbTrigSrc = Uint8()


class IdtReturnCode(SomeIpPayload):

    IdtReturnCode: Uint8

    def __init__(self):

        self.IdtReturnCode = Uint8()
