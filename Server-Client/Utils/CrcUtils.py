import struct
import math

#CRC

def crc16_ccitt(data: bytes, poly=0x1021, init=0xFFFF) -> int:
    crc = init
    for b in data:
        crc ^= (b << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ poly) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc



MSG_TYPES = {
    "REGISTER":          0,
    "REGISTER_OK":       1,
    "DATA":              2,
    "ACK":               3,
    "RESEND":            4,
    "RESEND_RESPONSE":   5,
    "PING":              6,
    "PONG":              7,
    "INVALID_TOKEN":     8,
}

MSG_TYPES_REV = {v: k for k, v in MSG_TYPES.items()}

DEVICE_TYPES = {
    "ThermoNode":   1,
    "WindSense":    2,
    "RainDetect":   3,
    "AirQualityBox":4,
}

DEVICE_TYPES_REV = {v: k for k, v in DEVICE_TYPES.items()}



def encode_payload(device_type: str, msg_type: str, payload: dict) -> bytes:

    if msg_type != "DATA" and msg_type != "RESEND_RESPONSE":
        return b""

    if device_type == "ThermoNode":
        # temperature, humidity, dew_point, pressure
        t  = int(round((float(payload["temperature"]) + 50.0) * 10))
        h  = int(round(float(payload["humidity"]) * 10))
        dp = int(round((float(payload["dew_point"]) + 50.0) * 10))
        p  = int(round((float(payload["pressure"]) - 800.0) * 100))
        return struct.pack("!HHHH", t, h, dp, p)

    elif device_type == "WindSense":
        ws = int(round(float(payload["wind_speed"]) * 10))
        wg = int(round(float(payload["wind_gust"]) * 10))
        wd = int(round(int(payload["wind_direction"])))
        tb = int(round(float(payload["turbulence"]) * 10))
        return struct.pack("!HHHB", ws, wg, wd, tb)

    elif device_type == "RainDetect":
        rf  = int(round(float(payload["rainfall"]) * 10))
        sm  = int(round(float(payload["soil_moisture"]) * 10))
        fr  = int(round(int(payload["flood_risk"])))
        dur = int(round(int(payload["rain_duration"])))
        return struct.pack("!HHBB", rf, sm, fr, dur)

    elif device_type == "AirQualityBox":
        co2 = int(round(int(payload["co2"])))
        oz  = int(round(float(payload["ozone"]) * 10))
        aqi = int(round(int(payload["air_quality_index"])))
        return struct.pack("!HHH", co2, oz, aqi)


    return b""


def decode_payload(device_type: str, msg_type: str, data: bytes) -> dict:
    if msg_type != "DATA" and msg_type != "RESEND_RESPONSE":
        return {}

    if device_type == "ThermoNode":
        t, h, dp, p = struct.unpack("!HHHH", data)
        return {
            "temperature":   (t / 10.0) - 50.0,
            "humidity":      h / 10.0,
            "dew_point":     (dp / 10.0) - 50.0,
            "pressure":      (p / 100.0) + 800.0,
        }

    elif device_type == "WindSense":
        ws, wg, wd, tb = struct.unpack("!HHHB", data)
        return {
            "wind_speed":     ws / 10.0,
            "wind_gust":      wg / 10.0,
            "wind_direction": wd,
            "turbulence":     tb / 10.0,
        }

    elif device_type == "RainDetect":
        rf, sm, fr, dur = struct.unpack("!HHBB", data)
        return {
            "rainfall":      rf / 10.0,
            "soil_moisture": sm / 10.0,
            "flood_risk":    fr,
            "rain_duration": dur,
        }

    elif device_type == "AirQualityBox":
        co2, oz, aqi = struct.unpack("!HHH", data)
        return {
            "co2":               co2,
            "ozone":             oz / 10.0,
            "air_quality_index": aqi,
        }

    return {}




def make_packet(obj: dict) -> bytes:

    msg_type = obj["msg_type"]
    device_type = obj["device_type"]
    sensor_id = obj["sensor_id"]
    ts = int(obj["timestamp"])
    low_battery = bool(obj.get("low_battery", False))
    token = obj.get("token", "") or ""
    payload = obj.get("payload", {})

    msg_code = MSG_TYPES[msg_type]
    dev_code = DEVICE_TYPES.get(device_type, 0)


    sid_bytes = sensor_id.encode("ascii")
    if len(sid_bytes) != 2:

        sid_bytes = (sensor_id[:2]).ljust(2, "_").encode("ascii")

    flags = 0
    if low_battery:
        flags |= 0x01

    token_bytes = token.encode("ascii", errors="ignore")


    if len(token_bytes) > 4:
        token_bytes = token_bytes[:4]
    else:
        token_bytes = token_bytes.ljust(4, b'_')

    payload_bytes = encode_payload(device_type, msg_type, payload)


    header = struct.pack("!BB2sIB4s",
                         msg_code,
                         dev_code,
                         sid_bytes,
                         ts,
                         flags,
                         token_bytes)

    body = header + payload_bytes
    crc = crc16_ccitt(body)
    pkt = body + struct.pack("!H", crc)
    return pkt


def parse_packet(data: bytes):


    if len(data) < 13 + 2:
        return None

    body = data[:-2]
    recv_crc = struct.unpack("!H", data[-2:])[0]
    calc_crc = crc16_ccitt(body)

    if recv_crc != calc_crc:
        return None


    msg_code, dev_code, sid_bytes, ts, flags, token_bytes = struct.unpack("!BB2sIB4s", body[:13])
    offset = 13

    token = token_bytes.decode("ascii", errors="ignore").rstrip("_")

    payload_bytes = body[offset:]


    msg_type = MSG_TYPES_REV.get(msg_code, "UNKNOWN")
    device_type = DEVICE_TYPES_REV.get(dev_code, "UNKNOWN")
    sensor_id = sid_bytes.decode("ascii", errors="ignore")

    low_battery = bool(flags & 0x01)

    payload = decode_payload(device_type, msg_type, payload_bytes)

    obj = {
        "msg_type": msg_type,
        "device_type": device_type,
        "sensor_id": sensor_id,
        "timestamp": ts,
        "low_battery": low_battery,
        "token": token,
        "payload": payload,
    }
    return obj


def verify_crc(data: bytes) -> bool:
    if len(data) < 2:
        return False
    body = data[:-2]
    recv_crc = struct.unpack("!H", data[-2:])[0]
    return crc16_ccitt(body) == recv_crc
