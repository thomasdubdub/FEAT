import numpy as np
import pandas as pd
from openap import WRAP, aero, FlightPhase
from openap.traj import Generator
from openap import prop


class FlightProfiles:
    def __init__(self, fpg):
        self.fpg = fpg

    def __iter__(self):
        return (fp for fp in self.fpg)

    @classmethod
    def from_df(cls, df):
        return cls(fp for _, fp in df.groupby("id"))

    def to_df(self):
        return pd.concat(self.fpg).reset_index(drop=True)


class FlightProfileGenerator:
    def __init__(self, ac_type, eng_type=None):
        self.ac_type = ac_type
        self.eng_type = eng_type
        self.trajgen = Generator(ac=ac_type, eng=eng_type)
        self.wrap = WRAP(ac=ac_type)
        self.aircraft = prop.aircraft(ac_type)

    def __call__(self, range_step=100, dt=10, set_flight_phase=True):
        def generate():
            for i, range_cr in enumerate(
                range(
                    int(self.wrap.cruise_range()["minimum"]),
                    int(self.wrap.cruise_range()["maximum"]),
                    range_step,
                )
            ):
                fp = _to_df(
                    self.trajgen.complete(dt=dt, range_cr=range_cr * 1e3, random=True),
                    id=i,
                )
                if set_flight_phase:
                    yield FlightPhaseEstimator()(fp)
                yield fp

        return FlightProfiles(generate())

    def gen_cruise_for_fuel_reserve(self):
        """Values according to FEAT appendix G"""
        duration = (
            45 * 60
            if self.aircraft["engine"]["type"] == "turboprop"
            else 30 * 60  # turbofan/pistion
        )
        cruise = self.trajgen.cruise(dt=duration, alt_cr=1500, random=True)
        cruise = dict(
            (key, value[:2] if isinstance(value, np.ndarray) else value)
            for key, value in cruise.items()
        )
        return _to_df(cruise).assign(fp="CR")

    def gen_flight_for_alternate_fuel(self):
        return _to_df(self.trajgen.complete(dt=30, range_cr=0, random=True))


def _to_df(trajgen, id=0):
    fp = pd.DataFrame.from_dict(trajgen).assign(id=id)
    fp["t"] = fp["t"].astype("int64")
    cols = ["h", "s", "v", "vs"]
    fp[cols] = fp[cols].astype("float")
    return fp


class FlightPhaseEstimator:
    def __init__(self):
        self.fpe = FlightPhase()

    def __call__(self, flight_profile):
        ts = flight_profile["t"].values  # timestamp, int, second
        alt = flight_profile["h"].values / aero.ft  # altitude, int, ft
        spd = flight_profile["v"].values / aero.kts  # speed, int, kts
        roc = flight_profile["vs"].values / aero.fpm  # vertical rate, int, ft/min
        self.fpe.set_trajectory(ts, alt, spd, roc)
        labels = self.fpe.phaselabel()
        flight_profile = flight_profile.assign(fp=labels)
        t_cl = flight_profile.query("fp=='CL'").iloc[0].t
        # t_de = fprof.query("fp=='DE'").iloc[-1].t
        # print(t_cl, t_de)
        # take_off = fprof.query(f"fp=='GND' and t < {t_cl}")
        flight_profile.loc[
            (flight_profile.fp == "GND") & (flight_profile.t < t_cl), "fp"
        ] = "TO"
        # landing = fprof.query(f"fp in {['GND','NA']} and t > {t_de}")
        # traj.loc[(fprof.fp == "NA") & (fprof.t > t_de), "fp"] = "L"
        return flight_profile
