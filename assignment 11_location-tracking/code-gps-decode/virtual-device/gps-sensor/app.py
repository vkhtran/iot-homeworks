from counterfit_connection import CounterFitConnection
CounterFitConnection.init('127.0.0.1', 5000)

from datetime import datetime, timezone
import time
import counterfit_shims_serial
import pynmea2
import json

connection_string = '<connection_string>'

serial = counterfit_shims_serial.Serial('/dev/ttyAMA0')

gps_state = {
    'latitude': None,
    'longitude': None,
    'altitude_m': None,
    'speed_kmph': None,
    'speed_knots': None,
    'gps_time_utc': None,
    'satellites': None,
    'gps_quality': None,
}


def parse_nmea(line):
    line = line.strip()

    try:
        return pynmea2.parse(line)
    except pynmea2.nmea.ChecksumError:
        if '*' not in line:
            raise

        return pynmea2.parse(line.split('*', 1)[0])


def dm_to_decimal(value, direction):
    decimal = pynmea2.dm_to_sd(value)

    if direction in ['S', 'W']:
        decimal = decimal * -1

    return decimal


def update_time_from_msg(msg):
    if msg.sentence_type == 'ZDA':
        gps_datetime = datetime(
            int(msg.year),
            int(msg.month),
            int(msg.day),
            msg.timestamp.hour,
            msg.timestamp.minute,
            msg.timestamp.second,
            msg.timestamp.microsecond,
            tzinfo=timezone.utc,
        )
        gps_state['gps_time_utc'] = gps_datetime.isoformat()

    if msg.sentence_type == 'RMC' and msg.datestamp and msg.timestamp:
        gps_datetime = datetime.combine(
            msg.datestamp,
            msg.timestamp,
            tzinfo=timezone.utc,
        )
        gps_state['gps_time_utc'] = gps_datetime.isoformat()


def update_speed_from_msg(msg):
    if msg.sentence_type == 'VTG' and msg.spd_over_grnd_kmph:
        gps_state['speed_kmph'] = float(msg.spd_over_grnd_kmph)
        gps_state['speed_knots'] = float(msg.spd_over_grnd_kts)

    if msg.sentence_type == 'RMC' and msg.spd_over_grnd:
        speed_knots = float(msg.spd_over_grnd)
        gps_state['speed_knots'] = speed_knots
        gps_state['speed_kmph'] = speed_knots * 1.852


def update_location_from_msg(msg):
    if msg.sentence_type == 'GGA' and msg.lat and msg.lon:
        gps_state['latitude'] = dm_to_decimal(msg.lat, msg.lat_dir)
        gps_state['longitude'] = dm_to_decimal(msg.lon, msg.lon_dir)

        if msg.num_sats:
            gps_state['satellites'] = int(msg.num_sats)

        if msg.gps_qual:
            gps_state['gps_quality'] = int(msg.gps_qual)

        if msg.altitude:
            gps_state['altitude_m'] = float(msg.altitude)

        if msg.timestamp:
            gps_state['gps_time_utc'] = msg.timestamp.isoformat()


def has_usable_telemetry():
    return any(
        gps_state[key] is not None
        for key in ['altitude_m', 'speed_kmph', 'gps_time_utc', 'satellites']
    )


def send_gps_data(line):
    try:
        msg = parse_nmea(line)
    except pynmea2.ParseError as error:
        print(f'Skipping invalid NMEA sentence: {error}')
        return

    update_location_from_msg(msg)
    update_time_from_msg(msg)
    update_speed_from_msg(msg)

    if has_usable_telemetry():
        telemetry = {
            'latitude': gps_state['latitude'],
            'longitude': gps_state['longitude'],
            'altitude_m': gps_state['altitude_m'],
            'speed_kmph': gps_state['speed_kmph'],
            'speed_knots': gps_state['speed_knots'],
            'gps_time_utc': gps_state['gps_time_utc'],
            'satellites': gps_state['satellites'],
            'gps_quality': gps_state['gps_quality'],
            'moving': gps_state['speed_kmph'] is not None and gps_state['speed_kmph'] > 1,
        }

        print(json.dumps(telemetry))


def main():
    while True:
        line = serial.readline().decode('utf-8')

        while len(line) > 0:
            send_gps_data(line)
            line = serial.readline().decode('utf-8')

        time.sleep(1)


if __name__ == '__main__':
    main()
