from someip_py.codec import *


class IdtElSPPopupConditionKls(SomeIpPayload):

    _include_struct_len = True

    ElSPLwarn: Uint8

    ElSPRwarn: Uint8

    def __init__(self):

        self.ElSPLwarn = Uint8()

        self.ElSPRwarn = Uint8()


class IdtElSPPopupCondition(SomeIpPayload):

    IdtElSPPopupCondition: IdtElSPPopupConditionKls

    def __init__(self):

        self.IdtElSPPopupCondition = IdtElSPPopupConditionKls()
