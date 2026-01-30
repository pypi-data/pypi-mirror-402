from someip_py.codec import *


class IdtDriveModeStateKls(SomeIpPayload):

    _include_struct_len = True

    EcoMode: Bool

    ComfortMode: Bool

    SportMode: Bool

    PersonalMode: Bool

    OffroadMode: Bool

    AdaptiveMode: Bool

    RaceMode: Bool

    SnowMode: Bool

    SandMode: Bool

    MudMode: Bool

    RockMode: Bool

    GrassOrGravelMode: Bool

    DeepSnowMode: Bool

    MountainMode: Bool

    WaterWadingMode: Bool

    Anti_CarsicknessMode: Bool

    SlipperyMode: Bool

    SportPlusMode: Bool

    def __init__(self):

        self.EcoMode = Bool()

        self.ComfortMode = Bool()

        self.SportMode = Bool()

        self.PersonalMode = Bool()

        self.OffroadMode = Bool()

        self.AdaptiveMode = Bool()

        self.RaceMode = Bool()

        self.SnowMode = Bool()

        self.SandMode = Bool()

        self.MudMode = Bool()

        self.RockMode = Bool()

        self.GrassOrGravelMode = Bool()

        self.DeepSnowMode = Bool()

        self.MountainMode = Bool()

        self.WaterWadingMode = Bool()

        self.Anti_CarsicknessMode = Bool()

        self.SlipperyMode = Bool()

        self.SportPlusMode = Bool()


class IdtDriveModeState(SomeIpPayload):

    IdtDriveModeState: IdtDriveModeStateKls

    def __init__(self):

        self.IdtDriveModeState = IdtDriveModeStateKls()
