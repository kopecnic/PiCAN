import can
import cantools
import time
import random

OBD2_DBC_FILEPATH = "CSS-Electronics-OBD2-v1.4.dbc"
OBD2_MSG_ID = 2024

class OBD2_ECU_Emulator():

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

    def _on_msg_recieve(self, msg):

        

        id = msg.arbitration_id
        id = OBD2_MSG_ID
        data = list(msg.data)

        try:
            decoded_msg = self._database.decode_message(id, data)   
        except:
            return

        if id in self._database_msg_ids:

            if id == OBD2_MSG_ID:

                try:    

                    if decoded_msg['service'] == 'Show current data ':

                        if decoded_msg['ParameterID_Service01'] == 'S1_PID_00_PIDsSupported_01_20':
                            
                            data = [2, 1, 0, 8, 0, 0, 0, 0]
                            msg = can.Message(arbitration_id=OBD2_MSG_ID, data = data)
                            self._bus.send(msg)


                        elif decoded_msg['ParameterID_Service01'] == 'S1_PID_20_PIDsSupported_21_40':
                            
                            data = [2, 1, 32, 0, 0, 0, 0, 0]
                            msg = can.Message(arbitration_id=OBD2_MSG_ID, data = data)
                            self._bus.send(msg)

                        elif decoded_msg['ParameterID_Service01'] == 'S1_PID_40_PIDsSupported_41_60':

                            data = [2, 1, 64, 0, 0, 0, 0, 0]
                            msg = can.Message(arbitration_id=OBD2_MSG_ID, data = data)
                            self._bus.send(msg)

                        elif decoded_msg['ParameterID_Service01'] == 'S1_PID_60_PIDsSupported_61_80':

                            data = [2, 1, 96, 0, 0, 0, 0, 0]
                            msg = can.Message(arbitration_id=OBD2_MSG_ID, data = data)
                            self._bus.send(msg)

                        elif decoded_msg['ParameterID_Service01'] == 'S1_PID_80_PIDsSupported_81_A0':

                            data = [2, 1, 128, 0, 0, 0, 0, 0]
                            msg = can.Message(arbitration_id=OBD2_MSG_ID, data = data)
                            self._bus.send(msg)

                        elif decoded_msg['ParameterID_Service01'] == 'S1_PID_A0_PIDsSupported_A1_C0':

                            data = [2, 1, 160, 0, 0, 0, 0, 0]
                            msg = can.Message(arbitration_id=OBD2_MSG_ID, data = data)
                            self._bus.send(msg)

                        elif decoded_msg['ParameterID_Service01'] == 'S1_PID_C0_PIDsSupported_C1_E0':

                            data = [2, 1, 192, 0, 0, 0, 0, 0]
                            msg = can.Message(arbitration_id=OBD2_MSG_ID, data = data)
                            self._bus.send(msg)

                        elif decoded_msg['ParameterID_Service01'] == 'S1_PID_05_EngineCoolantTemp':
                            data = [2, 1, 5, random.randint(0,255), 0, 0, 0, 0]
                            msg = can.Message(arbitration_id=OBD2_MSG_ID, data = data)
                            self._bus.send(msg)

                except KeyError:
                    print("There was a KeyError!")


if __name__ == '__main__':

    bus1 = can.interface.Bus(bustype='socketcan', channel='can1', bitrate=500000) #setup bus 1
    obd_dbc = cantools.database.load_file(OBD2_DBC_FILEPATH, database_format='dbc', encoding='cp1252')
    obd_ecu_emulator = OBD2_ECU_Emulator(bus1, obd_dbc)

    while(1):
        time.sleep(10)