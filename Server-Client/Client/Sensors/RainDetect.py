from Client.Sensors.BaseSensor import BaseSensor
import random

class RainDetect(BaseSensor):
    device_type = "RainDetect"

    def __init__(self, sensor_id):
        super().__init__(sensor_id)
        self.manual_mode = False
        self.rainfall = round(random.uniform(0, 50), 1)
        self.soil_moisture = round(random.uniform(10, 90), 1)
        self.flood_risk = random.randint(0, 3)
        self.rain_duration = random.randint(0, 60)

    def randomize(self):
        self.rainfall = round(random.uniform(0, 50), 1)
        self.soil_moisture = round(random.uniform(10, 90), 1)
        self.flood_risk = random.randint(0, 3)
        self.rain_duration = random.randint(0, 60)

    def generate_payload(self):
        if not self.manual_mode:
            self.randomize()
        return {
            "rainfall": self.rainfall,
            "soil_moisture": self.soil_moisture,
            "flood_risk": self.flood_risk,
            "rain_duration": self.rain_duration
        }
