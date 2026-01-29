# This attempts to be a simpler interface to a Fronius Gen24 Primo/Symo
# Inverter. With some functions to poll status and set various parameters
# easily without needing to know the underlyin modbus registers.
#


class Gen24:
    def __init__(self, modbus_client):
        self._modbus_client = modbus_client

    def status(self):
        pass
        # return dict with:
        # solar power
        # AC power
        # inverter status


class Gen24Storage(Gen24):
    def __init__(self, modbus_client):
        super().__init__(modbus_client)

    def status(self) -> {}:
        base_stats = super().stats(self)
        extra_stats = self._getStorageStats()
        return base_stats.append(extra_stats)

    def forceStorageCharge(self, watts=2500, time="1 hour"):
        pass

    def _getStorageStats():
        pass
