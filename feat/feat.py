from .flight import FlightProfileGenerator
from .fuel import FuelEstimator
import statsmodels.formula.api as sm


class FeatModelReduction:
    def __init__(self, ac_type, eng_type=None):
        self.ac_type = ac_type
        self.eng_type = eng_type

    def gen_flight_profiles(self, range_step=100, dt=10):
        fpg = FlightProfileGenerator(ac_type=self.ac_type, eng_type=self.eng_type)
        return fpg(range_step=range_step, dt=dt)

    def compute_fuel(self, flight_profiles):
        assert flight_profiles is not None, "No flight profiles"
        fe = FuelEstimator(ac_type=self.ac_type, eng_tyep=self.eng_type)
        return fe.compute_fuel_per_flight(flight_profiles)

    def fit(self, fc):
        return sm.ols(formula="fc ~ fd + I(fd**2)", data=fc).fit()
