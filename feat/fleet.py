class FleetData:
    """To be completed when fleet data available (e.g. Planespotters)"""

    def __init__(self, ac_type):
        self.ac_type = ac_type
        pass

    def get_avg_num_seats(self):
        if self.ac_type == "A320":
            return 150
        else:
            return None
