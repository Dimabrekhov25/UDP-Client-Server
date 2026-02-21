from Client.Sensors.BaseSensor import BaseSensor
import random

class ThermoNode(BaseSensor):
    device_type = "ThermoNode"

    def __init__(self, sensor_id):
        super().__init__(sensor_id)

        self.temperature = round(random.uniform(-10, 30), 1)
        self.humidity = round(random.uniform(20, 90), 1)
        self.dew_point = round(random.uniform(-10, 20), 1)
        self.pressure = round(random.uniform(980, 1040), 2)

    def generate_payload(self):

        return {
            "temperature": self.temperature,
            "humidity": self.humidity,
            "dew_point": self.dew_point,
            "pressure": self.pressure
        }

    def randomize(self):

        self.temperature = round(random.uniform(-10, 30), 1)
        self.humidity = round(random.uniform(20, 90), 1)
        self.dew_point = round(random.uniform(-10, 20), 1)
        self.pressure = round(random.uniform(980, 1040), 2)
