import numpy as np
from openap import aero, prop, Thrust
from .flight import FlightPhaseEstimator, FlightProfiles


class ThrustEstimator:
    def __init__(self, ac_type, eng_type=None):
        self.ac_type = ac_type
        aircraft = prop.aircraft(ac_type)
        if eng_type is None:
            self.eng_type = aircraft["engine"]["default"]
        self.thrust = Thrust(ac=ac_type, eng=eng_type)

    def __call__(self, flight_profiles):
        assert flight_profiles is not None, "No flight profiles"

        def generate():
            for fp in flight_profiles:
                yield self.compute_thrust(fp)

        return FlightProfiles(generate())

    def compute_thrust(self, flight_profile):
        def thr(x):
            v, h, vs = x.v / aero.kts, x.h / aero.ft, x.vs / aero.fpm
            if x.fp == "TO":
                return self.thrust.takeoff(tas=v, alt=h)
            if x.fp == "CL":
                return self.thrust.climb(tas=v, alt=h, roc=vs)
            if x.fp == "CR":
                return self.thrust.cruise(tas=v, alt=h)
            if x.fp == "DE":
                return self.thrust.descent_idle(tas=v, alt=h)
            return np.NaN

        if "fp" not in flight_profile.columns:
            flight_profile = FlightPhaseEstimator()(flight_profile)
        flight_profile = flight_profile.assign(
            thr=lambda x: x.apply(lambda x: thr(x), axis=1)
        )
        flight_profile["thr"] = flight_profile["thr"].astype("float")
        return flight_profile
