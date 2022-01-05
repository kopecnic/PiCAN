import argparse
import can
import cantools
import time
import copy
from threading import Thread
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import datetime

#TODO: Thread protect dictionaries
#TODO: Make all data print at once

OBD2_DBC_FILEPATH = "CSS-Electronics-OBD2-v1.4.dbc"
OBD2_MSG_ID_RX = 2024
OBD2_MSG_ID_TX = 2015
OBD2_SUPPORTED_IDS_TX_RATE = 0.5

SERVICE01_PIDS_SUPPORTED_PIDS = {
    "01_20": [0, False],
    "21_40": [32, False],
    "41_60": [64, False],
    "61_80": [96, False],
    "81_A0": [128, False],
    "A1_C0": [160, False],
    "C1_E0": [192, False]
}

SELECTED_PRINT_DATA_SERVICE01 = [
    "S1_PID_01_MonitorStatus",
    "S1_PID_03_FuelSystemStatus",
    "S1_PID_04_CalcEngineLoad",
    "S1_PID_05_EngineCoolantTemp",
    "S1_PID_0A_FuelPressure",
    "S1_PID_0B_IntakeManiAbsPress",
    "S1_PID_0C_EngineRPM",
    "S1_PID_0D_VehicleSpeed",
    "S1_PID_0E_TimingAdvance",
    "S1_PID_0F_IntakeAirTemperature",
    "S1_PID_10_MAFAirFlowRate",
    "S1_PID_11_ThrottlePosition",
    "S1_PID_12_CmdSecAirStatus",
    "S1_PID_1C_OBDStandard",
    "S1_PID_1F_TimeSinceEngStart",
    "S1_PID_21_DistanceMILOn",
    "S1_PID_22_FuelRailPres",
    "S1_PID_23_FuelRailGaug",
    "S1_PID_2E_CmdEvapPurge",
    "S1_PID_2F_FuelTankLevel",
    "S1_PID_30_WarmUpsSinceCodeClear",
    "S1_PID_31_DistanceSinceCodeClear",
    "S1_PID_32_EvapSysVaporPres",
    "S1_PID_41_MonStatusDriveCycle",
    "S1_PID_42_ControlModuleVolt",
    "S1_PID_5C_EngineOilTemp",
    "S1_PID_5E_EngineFuelRate",
    "S1_PID_61_DemandEngTorqPct",
    "S1_PID_62_ActualEngTorqPct",
    "S1_PID_66_MAFSensor",
    "S1_PID_67_EngineCoolantTemp",
    "S1_PID_68_IntakeAirTempSens",
    "S1_PID_6B_ExhaustGasTemp",
    "S1_PID_6C_CmdThrottleActRel"
]


class PiCAN_OBD2():
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

        self._obd2_data = {}

        self._service01_pids_supported_pids = SERVICE01_PIDS_SUPPORTED_PIDS

        self._supported_pids_service01 = {}

        self._get_supported_pids_service01()



    def _on_msg_recieve(self, msg):

        id = msg.arbitration_id
        data = msg.data
        timestamp = msg.timestamp

        if id in self._database_msg_ids:

            try:
              decoded_msg = self._database.decode_message(id, data)
            except:
              #print("THERE WAS AN EXCEPTION")
              return

            if id == OBD2_MSG_ID_RX:
                self._process_OBD2_data_msg(decoded_msg, timestamp)

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

    def _get_supported_pids_service01(self):

        print("Getting supported PIDs...")
        
        self._supported_pids_service01[0] = '1'

        for key in self._service01_pids_supported_pids:
            pid = self._service01_pids_supported_pids[key][0]
            
            #print(self._supported_pids_service01)
            
  
            data = [2, 1, pid, 0, 0, 0, 0, 0]
            msg = can.Message(arbitration_id=OBD2_MSG_ID_TX, is_extended_id=False, data = data)
            task = self._bus.send_periodic(msg, OBD2_SUPPORTED_IDS_TX_RATE)
    
            #while not self._service01_pids_supported_pids[key][1]:
            time.sleep(.2)
            task.stop()
        
        for key in self._service01_pids_supported_pids:
            pid = self._service01_pids_supported_pids[key][0]
            self._supported_pids_service01[pid] = 0
            
        print(self._supported_pids_service01)

    def request_data(self):
    
        supported_pids_service01 = copy.deepcopy(self._supported_pids_service01)

        for pid in supported_pids_service01:
            if supported_pids_service01[pid] == '1':
                #print(pid)
                data = [2, 1, pid, 0, 0, 0, 0, 0]
                msg = can.Message(arbitration_id=OBD2_MSG_ID_TX, is_extended_id=False, data = data)
                self._bus.send(msg)
                time.sleep(0.01)


    """
    Process a recieved OBD2 message. Stores recieved data in the self._obd2_data dictionary
    """
    def _process_OBD2_data_msg(self, decoded_msg, timestamp):
        excluded_sigs = [
            "length",
            "response",
            "service", 
            "ParameterID_Service01",
            "ParameterID_Service02"
        ]   

        try:     

            if decoded_msg['service'] == 'Show current data ':

                if decoded_msg['ParameterID_Service01'] == 'S1_PID_00_PIDsSupported_01_20':

                    self._service01_pids_supported_pids['01_20'][1] = True

                    print("Service Group 01 - 20 Recieved")

                    pids_supported = list("{:032b}".format(decoded_msg['S1_PID_00_PIDsSupported_01_20']))

                    for i in range(0, len(pids_supported)):
                        self._supported_pids_service01[i+1] = pids_supported[i]


                elif decoded_msg['ParameterID_Service01'] == 'S1_PID_20_PIDsSupported_21_40':

                    self._service01_pids_supported_pids['21_40'][1] = True

                    print("Service Group 21 - 40 Recieved")

                    pids_supported = list("{:032b}".format(decoded_msg['S1_PID_20_PIDsSupported_21_40']))

                    for i in range(0, len(pids_supported)):
                        self._supported_pids_service01[i+33] = pids_supported[i]

                elif decoded_msg['ParameterID_Service01'] == 'S1_PID_40_PIDsSupported_41_60':

                    self._service01_pids_supported_pids['41_60'][1] = True

                    print("Service Group 41 - 60 Recieved")

                    pids_supported = list("{:032b}".format(decoded_msg['S1_PID_40_PIDsSupported_41_60']))

                    for i in range(0, len(pids_supported)):
                        self._supported_pids_service01[i+65] = pids_supported[i]

                elif decoded_msg['ParameterID_Service01'] == 'S1_PID_60_PIDsSupported_61_80':

                    self._service01_pids_supported_pids['61_80'][1] = True

                    print("Service Group 61 - 80 Recieved")

                    pids_supported = list("{:032b}".format(decoded_msg['S1_PID_60_PIDsSupported_61_80']))

                    for i in range(0, len(pids_supported)):
                        self._supported_pids_service01[i+97] = pids_supported[i]

                elif decoded_msg['ParameterID_Service01'] == 'S1_PID_80_PIDsSupported_81_A0':

                    self._service01_pids_supported_pids['81_A0'][1] = True

                    print("Service Group 81 - A0 Recieved")

                    pids_supported = list("{:032b}".format(decoded_msg['S1_PID_80_PIDsSupported_81_A0']))

                    for i in range(0, len(pids_supported)):
                        self._supported_pids_service01[i+129] = pids_supported[i]

                elif decoded_msg['ParameterID_Service01'] == 'S1_PID_A0_PIDsSupported_A1_C0':

                    self._service01_pids_supported_pids['A1_C0'][1] = True

                    print("Service Group A1 - C0 Recieved")

                    pids_supported = list("{:032b}".format(decoded_msg['S1_PID_A0_PIDsSupported_A1_C0']))

                    for i in range(0, len(pids_supported)):
                        self._supported_pids_service01[i+161] = pids_supported[i]

                elif decoded_msg['ParameterID_Service01'] == 'S1_PID_C0_PIDsSupported_C1_E0':

                    self._service01_pids_supported_pids['C1_E0'][1] = True

                    print("Service Group C1 - E0 Recieved")

                    pids_supported = list("{:032b}".format(decoded_msg['S1_PID_C0_PIDsSupported_C1_E0']))

                    for i in range(0, len(pids_supported)):
                        self._supported_pids_service01[i+193] = pids_supported[i]

                else:
                    for key in decoded_msg.keys():
                        if key not in excluded_sigs:
                            self._obd2_data[key] = decoded_msg[key]
                            if self._log_to_influx:
                                thread = Thread(target = self._write_obd2_data_to_influx, args = (key, decoded_msg[key], timestamp))
                                thread.start()

        except KeyError:
            print("There was a KeyError!")

    def _write_obd2_data_to_influx(self, field_name, field_data, timestamp):
        try:
          #print("Logging", field_name, "to influx!")
          obd2_data_point = Point("TEST_VEHICLE").field(field_name, field_data).time(datetime.datetime.utcfromtimestamp(timestamp))
          self.influx_write_client.write(bucket=self._influx_bucket, record=obd2_data_point)
        except:
          return
        return

    """
    Prints all the stored OBD data
    """
    def print_all_OBD2_data(self):

        self._clear_terminal()

        print('{0}'.format('-' * 80))
        
        obd2_data = copy.deepcopy(self._obd2_data)
        
        for key in obd2_data.keys():
            print(key, ": ", obd2_data[key])

        print('{0}'.format('-' * 80))

    def print_select_OBD2_data(self, pids_to_print):

        self._clear_terminal()

        print('{0}'.format('-' * 80))
        
        obd2_data = copy.deepcopy(self._obd2_data)
        
        for key in obd2_data.keys():
            if key in pids_to_print:
                print(key, ": ", obd2_data[key])

        print('{0}'.format('-' * 80))

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
    obd_dbc = cantools.database.load_file(OBD2_DBC_FILEPATH)
    obd2_interface = PiCAN_OBD2(bus0, obd_dbc)

    if "logging_type" in vars(args).keys():
        
        if args.logging_type == "influx":
            obd2_interface.enable_influx_logging(args.url, args.org, args.token, args.bucket)

    while(1):
        #obd2_interface.print_all_OBD2_data()
        #obd2_interface.print_select_OBD2_data(SELECTED_PRINT_DATA_SERVICE01)
        time.sleep(0.2)
        obd2_interface.request_data()

if __name__ == '__main__':
    main()