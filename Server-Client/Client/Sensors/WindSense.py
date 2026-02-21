from Client.Sensors.BaseSensor import BaseSensor
import random

class WindSense(BaseSensor):
    device_type = "WindSense"

    def __init__(self, sensor_id):
        super().__init__(sensor_id)
        self.manual_mode = False
        self.wind_speed = round(random.uniform(0, 30), 1)
        self.wind_gust = round(random.uniform(0, 50), 1)
        self.wind_direction = random.randint(0, 359)
        self.turbulence = round(random.uniform(0, 1), 1)

    def randomize(self):
        self.wind_speed = round(random.uniform(0, 30), 1)
        self.wind_gust = round(random.uniform(0, 50), 1)
        self.wind_direction = random.randint(0, 359)
        self.turbulence = round(random.uniform(0, 1), 1)

    def generate_payload(self):
        if not self.manual_mode:
            self.randomize()
        return {
            "wind_speed": self.wind_speed,
            "wind_gust": self.wind_gust,
            "wind_direction": self.wind_direction,
            "turbulence": self.turbulence
        }

