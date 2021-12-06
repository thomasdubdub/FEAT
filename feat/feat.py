from feat import FlightProfileGenerator, FuelEstimator, MassEstimator


class FeatModelReduction:
    def __init__(self, ac_type, eng_type=None):
        self.ac_type = ac_type
        self.eng_type = eng_type

    def fit(self, range_step=100, dt=10):
        fpg = FlightProfileGenerator(ac_type=self.ac_type, eng_type=self.eng_type)
        flight_profiles = fpg(range_step=range_step, dt=dt)
        me = MassEstimator(ac_type=self.ac_type)
        fe = FuelEstimator(
            ac_type=self.ac_type, eng_tyep=self.eng_type, mass=me.reference_mass
        )
        flight_profiles = fe(flight_profiles)
        # TODO
        # Quadratic fitting
