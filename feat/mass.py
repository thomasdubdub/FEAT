import pandas as pd
from openap import prop
from .fleet import FleetData
from .flight import FlightProfiles, FlightProfileGenerator
from .fuel import FuelEstimator


class MassEstimator:
    def __init__(self, ac_type, eng_type=None):
        self.aircraft = prop.aircraft(ac_type)
        self.fleet = FleetData(ac_type)
        self.fpg = FlightProfileGenerator(ac_type=ac_type, eng_type=eng_type)
        self.fe = FuelEstimator(ac_type=ac_type, eng_type=eng_type)

    def __call__(self, flight_profiles, mass, return_tow_only=True):
        def generate():
            for fp in flight_profiles:
                yield self.compute_tow(fp, return_tow_only)

        return FlightProfiles(generate())

    @property
    def reference_mass(self):
        return (
            self.aircraft["limits"]["OEW"]
            + (self.aircraft["limits"]["MTOW"] - self.aircraft["limits"]["OEW"]) * 0.7
        )

    @property
    def oew(self):
        return self.aircraft["limits"]["OEW"]

    def compute_payload_mass(self):
        """TODO use fleet and updated ICAO/IATA data"""
        avg_num_seats = self.fleet.get_avg_num_seats()

        # ICAO, 2009. Traffic - Commercial Air Carriers Reporting Instructions, Form A.
        # International Civil Aviation Organization. URL http://www.icao.int/staforms.
        passenger_luggage_mass = 100  # KG

        # IATA, 2019. Economic Performance of the Airline Industry, 2019 End-year report.
        # International Air Transport Association.
        # URL https://www.iata.org/contentassets/36695cd211574052b3820044111b56de/airline-industry-economic-performance-dec19-report.pdf.
        avg_load_factor = 0.819  # for 2018

        return avg_load_factor * avg_num_seats * passenger_luggage_mass

    def compute_tow(self, flight_profile, return_tow_only=True):
        tow = self.reference_mass
        res_cruise = self.fpg.gen_cruise_for_fuel_reserve()
        alt_flight = self.fpg.gen_flight_for_alternate_fuel()
        cumul = []
        while True:
            f_trip = self.fe.compute_fuel(
                flight_profile, mass=tow, last_point=True
            ).fc.item()
            f_cont = f_trip * 0.05
            landing_mass = tow - f_trip
            f_res = self.fe.compute_fuel(
                res_cruise, mass=landing_mass, last_point=True
            ).fc.item()
            f_alt = self.fe.compute_fuel(
                alt_flight, mass=landing_mass, last_point=True
            ).fc.item()
            m_fuel = f_trip + f_cont + f_res + f_alt
            new_tow = self.oew + self.compute_payload_mass() + m_fuel
            cumul.append((f_trip, f_cont, f_res, f_alt, m_fuel, tow, new_tow))
            if abs(tow - new_tow) < 10:
                break
            tow = new_tow

        if return_tow_only:
            return tow

        return tow, pd.DataFrame.from_records(
            cumul,
            columns=["f_trip", "f_cont", "f_res", "f_alt", "m_fuel", "tow", "new_tow"],
        )
