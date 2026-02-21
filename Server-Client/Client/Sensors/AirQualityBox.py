from Client.Sensors.BaseSensor import BaseSensor
import random

class AirQualityBox(BaseSensor):
    device_type = "AirQualityBox"

    def __init__(self, sensor_id):
        super().__init__(sensor_id)
        self.manual_mode = False
        self.co2 = random.randint(350, 2000)
        self.ozone = round(random.uniform(0, 200), 1)
        self.air_quality_index = random.randint(0, 200)

    def randomize(self):
        self.co2 = random.randint(350, 2000)
        self.ozone = round(random.uniform(0, 200), 1)
        self.air_quality_index = random.randint(0, 200)

    def generate_payload(self):
        if not self.manual_mode:
            self.randomize()
        return {
            "co2": self.co2,
            "ozone": self.ozone,
            "air_quality_index": self.air_quality_index
        }
