import numpy as np
import pandas as pd
from openap import aero, FuelFlow
from .flight import FlightProfiles
from .thrust import ThrustEstimator


class FuelEstimator:
    def __init__(self, ac_type, eng_type=None):
        self.ac_type = ac_type
        self.eng_type = eng_type
        self.fuelflow = FuelFlow(ac=ac_type, eng=eng_type)

    def __call__(self, flight_profiles, mass, last_point=False):
        assert flight_profiles is not None, "No flight profiles"

        def generate():
            for fp in flight_profiles:
                yield self.compute_fuel(fp, mass, last_point)

        return FlightProfiles(generate())

    def compute_fuel(self, flight_profile, mass, last_point=False):
        def ff(x):
            v, h = x.v / aero.kts, x.h / aero.ft
            if x.fp == "TO":
                return self.fuelflow.takeoff(tas=v, alt=h, throttle=1)
            if x.fp == "CR":
                return self.fuelflow.enroute(mass=mass, tas=v, alt=h)
            if x.thr == x.thr:
                return self.fuelflow.at_thrust(acthr=x.thr, alt=h)
            return np.NaN

        if "thr" not in flight_profile.columns:
            flight_profile = ThrustEstimator(
                self.ac_type, self.eng_type
            ).compute_thrust(flight_profile)

        flight_profile = flight_profile.assign(
            ff=lambda x: x.apply(lambda x: ff(x), axis=1)
        )
        flight_profile["ff"] = flight_profile["ff"].astype("float")
        t = int(flight_profile["t"].diff().iloc[1])
        flight_profile["fc"] = (flight_profile["ff"] * t).cumsum(skipna=True)
        if last_point:
            last_point = flight_profile.query("fc==fc").iloc[-1]
            return pd.DataFrame.from_records(
                [(last_point.id, last_point.s, last_point.fc)],
                columns=["id", "fd", "fc"],
            )
        return flight_profile
