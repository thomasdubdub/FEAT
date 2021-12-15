import numpy as np
import pandas as pd
from openap import aero, FuelFlow
from .thrust import ThrustEstimator


class FuelEstimator:
    def __init__(self, ac_type, eng_type=None, mass=None):
        self.ac_type = ac_type
        self.eng_type = eng_type
        self.fuelflow = FuelFlow(ac=ac_type, eng=eng_type)
        self.mass = mass

    def __call__(self, flight_profiles):
        assert flight_profiles is not None, "No flight profiles"

        def ff(x):
            v, h, vs = x.v / aero.kts, x.h / aero.ft, x.vs / aero.fpm
            if x.fp == "TO":
                return self.fuelflow.takeoff(tas=v, alt=h, throttle=1)
            if x.fp == "CR":
                return self.fuelflow.enroute(mass=self.mass, tas=v, alt=h)
            if x.thr == x.thr:
                return self.fuelflow.at_thrust(acthr=x.thr, alt=h)
            return np.NaN

        if "thr" not in flight_profiles.columns:
            thrust = ThrustEstimator(self.ac_type, self.eng_type)
            flight_profiles = thrust(flight_profiles)

        flight_profiles = flight_profiles.assign(
            ff=lambda x: x.apply(lambda x: ff(x), axis=1)
        )
        flight_profiles["ff"] = flight_profiles["ff"].astype("float")
        return flight_profiles

    def compute_fuel_per_segment(self, flight_profiles):
        if "ff" not in flight_profiles.columns:
            flight_profiles = self(flight_profiles)
        cumul = []
        t = int(flight_profiles["t"].diff().iloc[1])
        for _, fp in flight_profiles.groupby("id"):
            fp["fc"] = (fp["ff"] * t).cumsum(skipna=True)
            cumul.append(fp)
        return pd.concat(cumul)

    def compute_fuel_per_flight(self, flight_profiles):
        if "fc" not in flight_profiles.columns:
            flight_profiles = self.compute_fuel_per_segment(flight_profiles)
        cumul = []
        for id, fp in flight_profiles.groupby("id"):
            last_point = fp.query("fc==fc").iloc[-1]
            cumul.append((id, last_point.s, last_point.fc))
        return pd.DataFrame.from_records(cumul, columns=["id", "fd", "fc"])


def compute_fuel_trip(ac_type, eng_type, mass, flight_profile):
    return (
        FuelEstimator(ac_type=ac_type, eng_type=eng_type, mass=mass)
        .compute_fuel_per_flight(flight_profile)
        .fc.item()
    )


def compute_fuel_reserve(fpg, mass):
    return (
        FuelEstimator(ac_type=fpg.ac_type, eng_type=fpg.eng_type, mass=mass)
        .compute_fuel_per_flight(fpg.gen_cruise_for_fuel_reserve())
        .fc.item()
    )


def compute_fuel_alternate(fpg, mass):
    return (
        FuelEstimator(ac_type=fpg.ac_type, eng_type=fpg.eng_type, mass=mass)
        .compute_fuel_per_flight(fpg.gen_flight_for_alternate_fuel())
        .fc.item()
    )
