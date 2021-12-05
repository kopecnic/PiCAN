import datetime
import time
import can

ID_DISPLAY_MODES = ['hex', 'dec']
DATA_DISPLAY_MODES = ['hex', 'dec']
TIMESTAMP_DISPLAY_MODES = ['absolute', 'delta']




class Analyzer():

    def __init__(
        self, 
        busses=[],
        id_display_mode = 0,
        data_display_mode = 0,
        timestamp_display_mode = 0,
        print_msg_timeout = 5.0
        ):

        self._busses = busses
        self._listeners = []
        self._notifiers = []
        self._bus_msgs_dicts = {}
        self._id_display_mode = ID_DISPLAY_MODES[id_display_mode]
        self._data_display_mode = DATA_DISPLAY_MODES[data_display_mode]
        self._timestamp_display_mode = TIMESTAMP_DISPLAY_MODES[timestamp_display_mode]
        self._print_msg_timeout = print_msg_timeout

        for bus in busses:
            listener = can.Listener()
            listener.on_message_received = self._on_msg_recieve

            notifier = can.Notifier(bus, [listener])

            self._listeners.append(listener)
            self._notifiers.append(notifier)

            self._bus_msgs_dicts[bus.channel] = {}

    def _on_msg_recieve(self, msg):

        dt = 0.0

        if msg.arbitration_id in self._bus_msgs_dicts[msg.channel]:
            last_recieved_timestamp = self._bus_msgs_dicts[msg.channel][msg.arbitration_id]['last_recieved_timestamp']
            dt = msg.timestamp - last_recieved_timestamp
        
        self._bus_msgs_dicts[msg.channel][msg.arbitration_id] = {'last_recieved_timestamp': msg.timestamp, 'msg': msg, 'last_dt': dt}
        
        #self.print_msg(msg, dt)

    def print_all_msgs(self):

        self._clear_terminal()

        print('{0}CANAnalyzer{0}'.format('-' * 34))

        print()

        current_time = time.time()

        for bus_msg_dict in self._sorted_busses_dict(0):
            for msg_id in self._sorted_msgs_dict(bus_msg_dict, 1):
                if (current_time - self._bus_msgs_dicts[bus_msg_dict][msg_id]['last_recieved_timestamp']) < self._print_msg_timeout:
                    msg = self._bus_msgs_dicts[bus_msg_dict][msg_id]['msg']
                    dt = self._bus_msgs_dicts[bus_msg_dict][msg_id]['last_dt']
                    self.print_msg(msg, dt)
        
                

    def print_msg(self, msg, dt):

        printString = ''

        if self._timestamp_display_mode == TIMESTAMP_DISPLAY_MODES[1]:
            printString = printString + 'Dt: {0:6.3f}    '.format(dt) #TODO: need to add dt calculations for each id
        else:
            printString = printString + 'Timestamp: {0:15.3f}    '.format(msg.timestamp)

        printString = printString + 'Bus: {0:5}    '.format(msg.channel)

        if self._id_display_mode == ID_DISPLAY_MODES[1]:
            printString = printString + 'Id: {0:4d}    '.format(msg.arbitration_id)
        else:
            printString = printString + 'Id: {0:3X}    '.format(msg.arbitration_id)

        printString = printString + 'Data: '
        if self. _data_display_mode == DATA_DISPLAY_MODES[1]:
            for byte in msg.data:
                printString = printString + '{0:3d}'.format(byte) + " "
            printString = printString + '    '
        else:
            for byte in msg.data:
                printString = printString + '{0:02X}'.format(byte) + " "
            printString = printString + '    '

        print(printString.strip())

    # define our clear function
    def _clear_terminal(self):
    
        print('\033[H\033[J') 

    def _sorted_msgs_dict(self, bus, mode):
        if mode == 0:
            return self._bus_msgs_dicts[bus]
        elif mode == 1:
            return sorted(self._bus_msgs_dicts[bus].keys())

    def _sorted_busses_dict(self, mode):
        if mode == 0:
            return self._bus_msgs_dicts
        elif mode == 1:
            return sorted(self._bus_msgs_dicts.keys())
