from someip_py.codec import *


class IdtXCallTypeAndStsKls(SomeIpPayload):

    _include_struct_len = True

    CallType: Uint8

    CallStatus: Uint8

    def __init__(self):

        self.CallType = Uint8()

        self.CallStatus = Uint8()


class IdtXCallTypeAndSts(SomeIpPayload):

    IdtXCallTypeAndSts: IdtXCallTypeAndStsKls

    def __init__(self):

        self.IdtXCallTypeAndSts = IdtXCallTypeAndStsKls()
