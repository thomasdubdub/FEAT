import pandas as pd
from openap import WRAP, aero, FlightPhase
from openap.traj import Generator


class FlightProfileGenerator:
    def __init__(self, ac_type, eng_type=None):
        self.trajgen = Generator(ac=ac_type, eng=eng_type)
        self.wrap = WRAP(ac=ac_type)

    def __call__(self, range_step=100, dt=10, set_flight_phase=True):
        cumul = []
        for i, range_cr in enumerate(
            range(
                int(self.wrap.cruise_range()["minimum"]),
                int(self.wrap.cruise_range()["maximum"]),
                range_step,
            )
        ):
            flight_profile = pd.DataFrame.from_dict(
                self.trajgen.complete(dt=dt, range_cr=range_cr * 1e3, random=True)
            ).assign(id=i)
            cumul.append(flight_profile)
        flight_profiles = pd.concat(cumul)
        flight_profiles["t"] = flight_profiles["t"].astype("int64")
        cols = ["h", "s", "v", "vs"]
        flight_profiles[cols] = flight_profiles[cols].astype("float")
        if set_flight_phase:
            return FlightPhaseEstimator()(flight_profiles)
        return flight_profiles


class FlightPhaseEstimator:
    def __init__(self):
        self.fpe = FlightPhase()

    def __call__(self, flight_profiles):
        cumul = []
        for _, fp in flight_profiles.groupby("id"):
            ts = fp["t"].values  # timestamp, int, second
            alt = fp["h"].values / aero.ft  # altitude, int, ft
            spd = fp["v"].values / aero.kts  # speed, int, kts
            roc = fp["vs"].values / aero.fpm  # vertical rate, int, ft/min
            self.fpe.set_trajectory(ts, alt, spd, roc)
            labels = self.fpe.phaselabel()
            fp = fp.assign(fp=labels)
            t_cl = fp.query("fp=='CL'").iloc[0].t
            # t_de = fprof.query("fp=='DE'").iloc[-1].t
            # print(t_cl, t_de)
            # take_off = fprof.query(f"fp=='GND' and t < {t_cl}")
            fp.loc[(fp.fp == "GND") & (fp.t < t_cl), "fp"] = "TO"
            # landing = fprof.query(f"fp in {['GND','NA']} and t > {t_de}")
            # traj.loc[(fprof.fp == "NA") & (fprof.t > t_de), "fp"] = "L"
            cumul.append(fp)
        return pd.concat(cumul)
