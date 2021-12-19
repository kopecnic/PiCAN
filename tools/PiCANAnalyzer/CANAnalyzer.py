import datetime
import time
import can
import re
from colorama import Fore, Back, Style

#constants
ID_DISPLAY_MODES = ['hex', 'dec']
DATA_DISPLAY_MODES = ['hex', 'dec']
TIMESTAMP_DISPLAY_MODES = ['absolute', 'delta']
MESSAGE_SORTING_MODES = ['none', 'id', 'bus', 'bus_then_id']

"""
Class that describes an CANAnalyzer. Used for reading and transmitting CAN messages on CAN busses.
"""
class CANAnalyzer():

    """
    Initializes a CANAnalyzer object

    @params
    busses: a list of python-can can.interface.Bus objects
    id_display_mode: the mode to display can ids in. modes are listed in constants
    data_display_mode: the mode to display message data in. modes are listed in constants
    timestamp_display_modes: the mode to display timestamps in. modes are listed in constants
    message_sorting_mode: the mode to sort messages for display. modes are listed in constants
    print_msg_timeout: timeout for displaying messages in seconds
    """
    def __init__(
        self, 
        busses=[],
        id_display_mode = 0,
        data_display_mode = 0,
        timestamp_display_mode = 0,
        message_sorting_mode = 3,
        print_msg_timeout = 10.0
        ):

        self._busses = busses #a list of python-can busses CANAnalyzer should join
        self._listeners = [] #a list of listeners used by CANAnalyzer
        self._notifiers = [] #a list of notifiers used by CANAnalyzer

        #a list of recieved messages ready by CANAnalyzer. each message dictionary within this dictionary
        #is stored with '<bus>:<message id>' as a key. each message dictionary stores information
        #about a single message such as the actual message object, a timestamp of the last time
        #the message was recieved, the time delta between the last two times the message was 
        #recieved, and if the message was recieved again since the last time it was printed. 
        self._recv_msgs_dicts = {}

        self._id_display_mode = ID_DISPLAY_MODES[id_display_mode] #mode in which to display ids when printing
        self._data_display_mode = DATA_DISPLAY_MODES[data_display_mode] #mode in which to display data when printing
        self._timestamp_display_mode = TIMESTAMP_DISPLAY_MODES[timestamp_display_mode] #mode in which to display timestamps
        self._message_sorting_mode = MESSAGE_SORTING_MODES[message_sorting_mode] #mode in which to sort messages when printing
        self._print_msg_timeout = print_msg_timeout #message timeout in sec in which to stop printing the message

        #for each bus that CANAnalyzer should join
        for bus in busses:
            listener = can.Listener() #create a lister for the bus
            listener.on_message_received = self._on_msg_recieve #set the listener's message recieved callback

            notifier = can.Notifier(bus, [listener]) #create a notifier for the bus and add the listener

            self._listeners.append(listener) #add the listener to CANAnalyzer's list of listeners
            self._notifiers.append(notifier) #add the notifier to CANAnalyzer's list of notifiers

    """
    CANAnalyzer's callaback for received CAN messages on any bus.

    @param
    msg: the a python-can CAN message object of the message that was received. passed in from the listener
    """
    def _on_msg_recieve(self, msg):

        dt = 0.0 
        data_changed = True 

        data_changed = []

        for i in range(8):
            data_changed.append(False)

        #check if the read message is stored in the recieved message dictionary
        if (msg.channel + ":" + str(msg.arbitration_id)) in self._recv_msgs_dicts:

            #store the timestamp (seconds since epoch) of the previous time the message was recieved
            last_recieved_timestamp = self._recv_msgs_dicts[msg.channel + ":" + str(msg.arbitration_id)]['last_recieved_timestamp']

            #calculate the delta time (seconds) between the last two times the message was recieved
            dt = msg.timestamp - last_recieved_timestamp

            #store the data from the last time the message was recieved
            last_data = self._recv_msgs_dicts[msg.channel + ":" + str(msg.arbitration_id)]['msg'].data

            #check if the data in each byte has changed since the last time the message was recieved
            for i in range(len(msg.data)):
                if msg.data[i] != last_data[i]:
                    data_changed[i] = True
        
        #store the new message information into the recieved message dictionary
        self._recv_msgs_dicts[msg.channel + ":" + str(msg.arbitration_id)] = {'last_recieved_timestamp': msg.timestamp, 'msg': msg, 'last_dt': dt, 'recieved_since_last_print': True,
            'data_changed': data_changed}
        
    """
    Prints recieved messages to the terminal
    """
    def print_data(self):

        #clear the terminal before printing
        self._clear_terminal()

        #print the header
        print('{0}CANAnalyzer{0}'.format('-' * 34))

        #print a newline
        print()

       #print(self._get_print_msg_table_header(self))

        #print each message, sorted using desired sort order
        for msg_bus_and_id in self._sorted_msgs(3):
            print(self._get_print_msg_str(msg_bus_and_id))

    def get_web_print_data_string(self):
        print_data = []

        for msg_bus_and_id in self._sorted_msgs(3):
            print_data_string = self._get_print_msg_str(msg_bus_and_id)

            reaesc = re.compile(r'\x1b[^m]*m')
            print_data_string = reaesc.sub('', print_data_string)

            print_data.append(print_data_string)
            
        return print_data

    def get_web_print_data_table(self):
        print_data = []

        for msg_bus_and_id in self._sorted_msgs(3):

            data = self.get_web_print_table_data(msg_bus_and_id)
            if data:
                print_data.append(data)

        return print_data
        

    def get_web_print_table_headers(self):
        print_data = {}

        print_data['bus'] = 'BUS'

        #delta time mode
        if self._timestamp_display_mode == TIMESTAMP_DISPLAY_MODES[1]:
            print_data['time'] = 'TIME (Dt)'
        #absolute time mode
        else:
            print_data['time'] = 'TIME (Absolute)'

        #decimal mode
        if self._id_display_mode == ID_DISPLAY_MODES[1]:
            print_data['id'] = 'ID (dec)'
        #hex mode
        else:
            print_data['id'] = 'ID (hex)'

        #decimal mode
        if self. _data_display_mode == DATA_DISPLAY_MODES[1]:
            print_data['data'] = 'DATA (dec)'
        #hex mode
        else:
            print_data['data'] = 'DATA (hex)'

        return print_data

        

    def get_web_print_table_data(self, msg_bus_and_id):

        print_data = {}

        #a python-can CAN message object of the message to print
        msg = self._recv_msgs_dicts[msg_bus_and_id]['msg'] 

        #the delta time (seconds) between the last two times the message was recieved
        dt = self._recv_msgs_dicts[msg_bus_and_id]['last_dt']

        #the current time since epoch in seconds
        current_time = time.time()

        #the time since the last time the message was recieved in seconds
        time_since_last_recieve = current_time - self._recv_msgs_dicts[msg_bus_and_id]['last_recieved_timestamp']

        #bool storing if the message has been recieved again since it was last printed
        recieved_since_last_print = self._recv_msgs_dicts[msg_bus_and_id]['recieved_since_last_print']

        #bool storing if the data has changed since the last time it was printed
        data_changed = self._recv_msgs_dicts[msg_bus_and_id]['data_changed']

        #check to see if the message is past the timeout, if so, dont print it 
        if time_since_last_recieve > self._print_msg_timeout:
            return {}

        print_data['recieved_since_last_print'] = recieved_since_last_print

        #delta time mode
        if self._timestamp_display_mode == TIMESTAMP_DISPLAY_MODES[1]:
           print_data['timestamp'] = '{0:06.3f}'.format(dt)
        #absolute time mode
        else:
            print_data['timestamp'] = 'T{0:15.3f}'.format(msg.timestamp)


        print_data['bus'] = '{0:5}'.format(msg.channel)

        #decimal mode
        if self._id_display_mode == ID_DISPLAY_MODES[1]:
            print_data['id'] = '{0:4d}'.format(msg.arbitration_id)
        #hex mode
        else:
            print_data['id'] = '{0:3X}'.format(msg.arbitration_id)


        #decimal mode
        if self. _data_display_mode == DATA_DISPLAY_MODES[1]:

            data_bytes = []
            
            #print each byte
            for i in range(len(msg.data)):

                data = []

                #if the byte has not changed, grey it out
                if not data_changed[i] or not recieved_since_last_print:
                    data.append(False)
                else:
                    data.append(True)

                data.append = '{0:3d}'.format(msg.data[i])

                data_bytes.append(data)

        #hex mode
        else:

            data_bytes = []
            
            #print each byte
            for i in range(len(msg.data)):

                data = []

                #if the byte has not changed, grey it out
                if not data_changed[i] or not recieved_since_last_print:
                    data.append(False)
                else:
                    data.append(True)

                data.append('{0:02X}'.format(msg.data[i]))

                data_bytes.append(data)  

        print_data['data'] = data_bytes


        #set the recieved since last print bool to false for this message
        self._recv_msgs_dicts[msg_bus_and_id]['recieved_since_last_print'] = False

        return print_data
                
    """
    Print a single CAN message to the terminal

    @param
    msg_bus_and_id: the key of the msg to print in the form of '<bus>:<message id>'
    """
    def _get_print_msg_str(self, msg_bus_and_id):

        #a python-can CAN message object of the message to print
        msg = self._recv_msgs_dicts[msg_bus_and_id]['msg'] 

        #the delta time (seconds) between the last two times the message was recieved
        dt = self._recv_msgs_dicts[msg_bus_and_id]['last_dt']

        #the current time since epoch in seconds
        current_time = time.time()

        #the time since the last time the message was recieved in seconds
        time_since_last_recieve = current_time - self._recv_msgs_dicts[msg_bus_and_id]['last_recieved_timestamp']

        #bool storing if the message has been recieved again since it was last printed
        recieved_since_last_print = self._recv_msgs_dicts[msg_bus_and_id]['recieved_since_last_print']

        #bool storing if the data has changed since the last time it was printed
        data_changed = self._recv_msgs_dicts[msg_bus_and_id]['data_changed']

        #check to see if the message is past the timeout, if so, dont print it 
        if time_since_last_recieve > self._print_msg_timeout:
            return ''

        #initialize string that will get printed
        printString = ''

        #if the message has not been recieved since the last time it was printed, grey it out. 
        if not recieved_since_last_print:
            printString = printString + Style.DIM

        #print the message's timestamp in the correct mode:
        #delta time mode
        if self._timestamp_display_mode == TIMESTAMP_DISPLAY_MODES[1]:
            printString = printString + 'Dt: {0:06.3f}    '.format(dt)
        #absolute time mode
        else:
            printString = printString + 'Timestamp: {0:15.3f}    '.format(msg.timestamp)

        #print the bus that the message was recieved on
        printString = printString + 'Bus: {0:5}    '.format(msg.channel)

        #print the message's id in the correct mode:
        #decimal mode
        if self._id_display_mode == ID_DISPLAY_MODES[1]:
            printString = printString + 'Id: {0:4d}    '.format(msg.arbitration_id)
        #hex mode
        else:
            printString = printString + 'Id: {0:3X}    '.format(msg.arbitration_id)

        #print the data tag
        printString = printString + 'Data: '

        #print the data in the correct mode:
        #decimal mode
        if self. _data_display_mode == DATA_DISPLAY_MODES[1]:
            
            #print each byte
            for i in range(len(msg.data)):

                #if the byte has not changed, grey it out
                if not data_changed[i] or not recieved_since_last_print:
                    printString = printString + Style.DIM
                printString = printString + '{0:3d}'.format(msg.data[i]) + Style.RESET_ALL + " "
            printString = printString + '    '
        #hex mode
        else:

            #print each byte
            for i in range(len(msg.data)):

                #if the byte has not changed, grey it out
                if not data_changed[i] or not recieved_since_last_print:
                    printString = printString + Style.DIM
                printString = printString + '{0:02X}'.format(msg.data[i]) + Style.RESET_ALL + " "
            printString = printString + '    '

        #reset the style
        printString = printString + Style.RESET_ALL

        #set the recieved since last print bool to false for this message
        self._recv_msgs_dicts[msg_bus_and_id]['recieved_since_last_print'] = False

        #strip off spaces
        return printString.strip()

    """
    Sends ASCII code to clear the terminal
    """
    def _clear_terminal(self):
    
        print('\033[H\033[J') 

    """
    Sorts messages by given order mode

    @param
    mode: mode in which to sort the messages
    """
    def _sorted_msgs(self, mode):

        #default mode: no sorting
        if mode == 0:
            return self._recv_msgs_dicts

        #sort by id only
        elif mode == 1:
            return sorted(self._recv_msgs_dicts, key=lambda msg_bus_and_id: msg_bus_and_id.split(":")[-1])

        #sort by bus only
        elif mode == 2:
            return sorted(self._recv_msgs_dicts, key=lambda msg_bus_and_id: msg_bus_and_id.split(":")[0])

        #sort by bus then id
        elif mode == 3:
            return sorted(self._recv_msgs_dicts, key=lambda msg_bus_and_id: (msg_bus_and_id.split(":")[0], msg_bus_and_id.split(":")[-1]))

