import can
import cantools
import time
import copy

#TODO: Thread protect dictionaries
#TODO: Make all data print at once

OBD2_DBC_FILEPATH = "CSS-Electronics-OBD2-v1.4.dbc"
OBD2_MSG_ID_RX = 2024
OBD2_MSG_ID_TX = 2015
OBD2_SUPPORTED_IDS_TX_RATE = 0.5


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

        print(self._database_msg_ids)

        self._listener = can.Listener()
        self._listener.on_message_received = self._on_msg_recieve

        self._notifier = can.Notifier(self._bus, [self._listener])

        self._obd2_data = {}

        self._received_supported_PIDs_service01_01_20 = False
        self._received_supported_PIDs_service01_21_40 = False
        self._received_supported_PIDs_service01_41_60 = False
        self._received_supported_PIDs_service01_61_80 = False
        self._received_supported_PIDs_service01_81_A0 = False
        self._received_supported_PIDs_service01_A1_C0 = False
        self._received_supported_PIDs_service01_C1_E0 = False
        self._supported_pids_service01 = {}

        self._get_supported_pids_service01()


    def _on_msg_recieve(self, msg):

        id = msg.arbitration_id
        data = msg.data

        if id in self._database_msg_ids:

            try:
              decoded_msg = self._database.decode_message(id, data)
            except:
              print("THERE WAS AN EXCEPTION")
              return

            #self._print_decoded_msg(decoded_msg)

            if id == OBD2_MSG_ID_RX:
                self._process_OBD2_data_msg(decoded_msg)

    def _get_supported_pids_service01(self):

        print("Getting supported PIDs...")

        data = [2, 1, 0, 0, 0, 0, 0, 0]
        msg = can.Message(arbitration_id=OBD2_MSG_ID_TX, is_extended_id=False, data = data)
        task = self._bus.send_periodic(msg, OBD2_SUPPORTED_IDS_TX_RATE)

        while not self._received_supported_PIDs_service01_01_20:
            time.sleep(.2)
        
        task.stop()

        data = [2, 1, 32, 0, 0, 0, 0, 0]
        msg = can.Message(arbitration_id=OBD2_MSG_ID_TX, is_extended_id=False, data = data)
        task = self._bus.send_periodic(msg, OBD2_SUPPORTED_IDS_TX_RATE)

        while not self._received_supported_PIDs_service01_21_40:
            time.sleep(.2)
        
        task.stop()
            
        """
        while not self._received_supported_PIDs_service01_41_60:
            data = [2, 1, 64, 0, 0, 0, 0, 0]
            msg = can.Message(arbitration_id=OBD2_MSG_ID_TX, is_extended_id=False, data = data)
            self._bus.send(msg)
            time.sleep(.2)

        while not self._received_supported_PIDs_service01_61_80:
            data = [2, 1, 96, 0, 0, 0, 0, 0]
            msg = can.Message(arbitration_id=OBD2_MSG_ID_TX, is_extended_id=False, data = data)
            self._bus.send(msg)
            time.sleep(.2)

        while not self._received_supported_PIDs_service01_81_A0:
            data = [2, 1, 128, 0, 0, 0, 0, 0]
            msg = can.Message(arbitration_id=OBD2_MSG_ID_TX, is_extended_id=False, data = data)
            self._bus.send(msg)
            time.sleep(.2)

        while not self._received_supported_PIDs_service01_A1_C0:
            data = [2, 1, 160, 0, 0, 0, 0, 0]
            msg = can.Message(arbitration_id=OBD2_MSG_ID_TX, is_extended_id=False, data = data)
            self._bus.send(msg)
            time.sleep(.2)

        while not self._received_supported_PIDs_service01_C1_E0:
            data = [2, 1, 192, 0, 0, 0, 0, 0]
            msg = can.Message(arbitration_id=OBD2_MSG_ID_TX, is_extended_id=False, data = data)
            self._bus.send(msg)
            time.sleep(.2)
            
        """
        
        pids_service01 = [0, 32, 64, 96, 128, 160, 192]
        
        for pid in pids_service01:
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
    def _process_OBD2_data_msg(self, decoded_msg):
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

                    self._received_supported_PIDs_service01_01_20 = True

                    print("Service Group 01 - 20 Recieved")

                    pids_supported = list(bin(decoded_msg['S1_PID_00_PIDsSupported_01_20']))[2:]

                    for i in range(0, len(pids_supported)):
                        self._supported_pids_service01[i+1] = pids_supported[i]


                elif decoded_msg['ParameterID_Service01'] == 'S1_PID_20_PIDsSupported_21_40':

                    self._received_supported_PIDs_service01_21_40 = True

                    print("Service Group 21 - 40 Recieved")

                    pids_supported = list(bin(decoded_msg['S1_PID_20_PIDsSupported_21_40']))[2:]

                    for i in range(0, len(pids_supported)):
                        self._supported_pids_service01[i+33] = pids_supported[i]

                elif decoded_msg['ParameterID_Service01'] == 'S1_PID_40_PIDsSupported_41_60':

                    self._received_supported_PIDs_service01_41_60 = True

                    print("Service Group 41 - 60 Recieved")

                    pids_supported = list(bin(decoded_msg['S1_PID_40_PIDsSupported_41_60']))[2:]

                    for i in range(0, len(pids_supported)):
                        self._supported_pids_service01[i+65] = pids_supported[i]

                elif decoded_msg['ParameterID_Service01'] == 'S1_PID_60_PIDsSupported_61_80':

                    self._received_supported_PIDs_service01_61_80 = True

                    print("Service Group 61 - 80 Recieved")

                    pids_supported = list(bin(decoded_msg['S1_PID_60_PIDsSupported_61_80']))[2:]

                    for i in range(0, len(pids_supported)):
                        self._supported_pids_service01[i+97] = pids_supported[i]

                elif decoded_msg['ParameterID_Service01'] == 'S1_PID_80_PIDsSupported_81_A0':

                    self._received_supported_PIDs_service01_81_A0 = True

                    print("Service Group 81 - A0 Recieved")

                    pids_supported = list(bin(decoded_msg['S1_PID_80_PIDsSupported_81_A0']))[2:]

                    for i in range(0, len(pids_supported)):
                        self._supported_pids_service01[i+129] = pids_supported[i]

                elif decoded_msg['ParameterID_Service01'] == 'S1_PID_A0_PIDsSupported_A1_C0':

                    self._received_supported_PIDs_service01_A1_C0 = True

                    print("Service Group A1 - C0 Recieved")

                    pids_supported = list(bin(decoded_msg['S1_PID_A0_PIDsSupported_A1_C0']))[2:]

                    for i in range(0, len(pids_supported)):
                        self._supported_pids_service01[i+161] = pids_supported[i]

                elif decoded_msg['ParameterID_Service01'] == 'S1_PID_C0_PIDsSupported_C1_E0':

                    self._received_supported_PIDs_service01_C1_E0 = True

                    print("Service Group C1 - E0 Recieved")

                    pids_supported = list(bin(decoded_msg['S1_PID_C0_PIDsSupported_C1_E0']))[2:]

                    for i in range(0, len(pids_supported)):
                        self._supported_pids_service01[i+193] = pids_supported[i]

                else:
                    for key in decoded_msg.keys():
                        if key not in excluded_sigs:
                            self._obd2_data[key] = decoded_msg[key]
                            #print(key)

        except KeyError:
            print("There was a KeyError!")

    """
    Prints all the stored OBD data
    """
    def print_OBD2_data(self):

        self._clear_terminal()

        print('{0}'.format('-' * 80))
        
        obd2_data = copy.deepcopy(self._obd2_data)
        
        for key in obd2_data.keys():
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

if __name__ == '__main__':

    bus0 = can.ThreadSafeBus(bustype='socketcan', channel='can0', bitrate=500000) #setup bus 1
    obd_dbc = cantools.database.load_file(OBD2_DBC_FILEPATH)
    obd2_interface = PiCAN_OBD2(bus0, obd_dbc)

    while(1):
        obd2_interface.print_OBD2_data()
        time.sleep(0.2)
        obd2_interface.request_data()