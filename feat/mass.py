from openap import prop


class MassEstimator:
    def __init__(self, ac_type):
        self.aircraft = prop.aircraft(ac_type)

    @property
    def reference_mass(self):
        return (
            self.aircraft["limits"]["OEW"]
            + (self.aircraft["limits"]["MTOW"] - self.aircraft["limits"]["OEW"]) * 0.7
        )
