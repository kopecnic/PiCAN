import can
import time
import CANAnalyzer

bus0 = can.interface.Bus(bustype='socketcan', channel='can0', bitrate=500000) #setup bus 1
#bus1 = can.interface.Bus(bustype='socketcan', channel='can1', bitrate=1000000) #setup bus 2

#initialize Analyzer object
analyzer = CANAnalyzer.CANAnalyzer(busses=[bus0], id_display_mode=0, data_display_mode=0, timestamp_display_mode=1) 

if __name__ == '__main__':

    #print all can messages on repeat
    while(1):
        analyzer.print_data()
        time.sleep(0.5)