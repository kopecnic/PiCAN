import can
import time
import CANAnalyzer

bus0 = can.interface.Bus(bustype='socketcan', channel='can0', bitrate=1000000)
bus1 = can.interface.Bus(bustype='socketcan', channel='can1', bitrate=1000000)

analyzer = CANAnalyzer.Analyzer(busses=[bus0, bus1], id_display_mode=0, data_display_mode=0, timestamp_display_mode=1)

if __name__ == '__main__':
    while(1):
        analyzer.print_all_msgs()
        time.sleep(0.5)