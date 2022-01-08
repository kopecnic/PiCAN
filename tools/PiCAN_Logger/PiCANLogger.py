import argparse
import can
import cantools
import time
import copy
from threading import Thread
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import datetime




class PiCANLogger():
    def __init__(
        self,
        bus,
        database):

        self._bus = bus
        self._database = database
        self._database_msg_ids = []

        for message in self._database.messages:
            self._database_msg_ids.append(message.frame_id)

        self._listener = can.Listener()
        self._listener.on_message_received = self._on_msg_recieve

        self._notifier = can.Notifier(self._bus, [self._listener])

        self._log_to_influx = False
        self._influx_bucket = ''
        self._influx_client = None
        self.influx_write_client = None




    def _on_msg_recieve(self, msg):

        id = msg.arbitration_id
        data = msg.data
        timestamp = msg.timestamp

        if id in self._database_msg_ids:

            try:
              decoded_msg = self._database.decode_message(id, data)
            except:
              return

            print(decoded_msg)


    def enable_influx_logging(self, url, org, token, bucket):

        try:

            self._influx_bucket = bucket

            self._influx_client = InfluxDBClient(url=url, token=token, org=org, debug=False)

            self.influx_write_client = self._influx_client.write_api(write_options=SYNCHRONOUS)

            self._log_to_influx = True

        except:
            self._log_to_influx = False
            print("Could not enable influx logging!!")
            return False

        return True

    def _write_obd2_data_to_influx(self, field_name, field_data, timestamp):
        try:
          #print("Logging", field_name, "to influx!")
          obd2_data_point = Point("TEST_VEHICLE").field(field_name, field_data).time(datetime.datetime.utcfromtimestamp(timestamp))
          self.influx_write_client.write(bucket=self._influx_bucket, record=obd2_data_point)
        except:
          return
        return

    """
    Prints a single decoded CAN message
    """
    def _print_decoded_msg(self, decoded_msg):

        self._clear_terminal()

        print('{0}'.format('-' * 80))
        
        keys = decoded_msg.keys()

        for key in keys:
            print(key, ": ", decoded_msg[key])
            
        print('{0}'.format('-' * 80))
        print()

    """
    Sends ASCII code to clear the terminal
    """
    def _clear_terminal(self):
    
        print('\033[H\033[J') 

def main():

    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers()

    log_parser = subparsers.add_parser('log')

    log_subparser = log_parser.add_subparsers(dest='logging_type')

    sd_log_subparser = log_subparser.add_parser('sd')

    influx_log_subparser = log_subparser.add_parser('influx')

    influx_log_subparser.add_argument("url")
    influx_log_subparser.add_argument("org")
    influx_log_subparser.add_argument("token")
    influx_log_subparser.add_argument("bucket")

    args = parser.parse_args()

    print(args)

    bus0 = can.ThreadSafeBus(bustype='socketcan', channel='can0', bitrate=500000) #setup bus 1
    dbc_bus0 = cantools.database.load_file('TeensyTestDatabase.dbc')
    logger = PiCANLogger(bus0, dbc_bus0)

    if "logging_type" in vars(args).keys():
        
        if args.logging_type == "influx":
            logger.enable_influx_logging(args.url, args.org, args.token, args.bucket)

    while(1):
        time.sleep(10)

if __name__ == '__main__':
    main()