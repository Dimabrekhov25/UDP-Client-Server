from abc import ABC, abstractmethod
import random

class BaseSensor(ABC):

    def __init__(self, sensor_id: str):
        self.sensor_id = sensor_id
        self.low_battery = False

    @property
    @abstractmethod
    def device_type(self):
        pass

    @abstractmethod
    def generate_payload(self) -> dict:
        pass
