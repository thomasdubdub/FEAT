import numpy as np
from openap import aero, prop, Thrust
from .flight import FlightPhaseEstimator


class ThrustEstimator:
    def __init__(self, ac_type, eng_type=None):
        self.ac_type = ac_type
        aircraft = prop.aircraft(ac_type)
        if eng_type is None:
            self.eng_type = aircraft["engine"]["default"]
        self.thrust = Thrust(ac=ac_type, eng=eng_type)

    def __call__(self, flight_profiles):
        assert flight_profiles is not None, "No flight profiles"

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

        if "fp" not in flight_profiles.columns:
            flight_profiles = FlightPhaseEstimator()(flight_profiles)
        flight_profiles = flight_profiles.assign(
            thr=lambda x: x.apply(lambda x: thr(x), axis=1)
        )
        flight_profiles["thr"] = flight_profiles["thr"].astype("float")
        return flight_profiles
