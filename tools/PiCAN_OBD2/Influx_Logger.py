from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import argparse
import pandas
import psutil
import socket
import os
from threading import Thread
from multiprocessing import Process
import time
from subprocess import PIPE, Popen
from gpiozero import CPUTemperature

def initialize_client(args):
    url = args.url
    org = args.org
    token = args.token

    client = InfluxDBClient(url=url, token=token, org=org, debug=False)

    write_api = client.write_api(write_options=SYNCHRONOUS)

    return client, write_api

def write_pc_stats(write_api):

    while(1):

        cpu_usage = psutil.cpu_percent()

        ram = psutil.virtual_memory()
        ram_total = ram.total / 2**20       # MiB.
        ram_used = ram.used / 2**20
        ram_free = ram.free / 2**20
        ram_percent_used = ram.percent
        
        disk = psutil.disk_usage('/')
        disk_total = disk.total / 2**30     # GiB.
        disk_used = disk.used / 2**30
        disk_free = disk.free / 2**30
        disk_percent_used = disk.percent

        cpu_temp = CPUTemperature().temperature

        cpu_load_point = Point(socket.gethostname()).field("cpu_load", cpu_usage)
        ram_total_point = Point(socket.gethostname()).field("ram_total", ram_total)
        ram_used_point = Point(socket.gethostname()).field("ram_used", ram_used)
        ram_free_point = Point(socket.gethostname()).field("ram_free", ram_free)
        ram_percent_used_point = Point(socket.gethostname()).field("ram_percent_used", ram_percent_used)
        disk_total_point = Point(socket.gethostname()).field("disk_total", disk_total)
        disk_used_point = Point(socket.gethostname()).field("disk_used", disk_used)
        disk_free_point = Point(socket.gethostname()).field("disk_free", disk_free)
        disk_percent_used_point = Point(socket.gethostname()).field("disk_percent_used", disk_percent_used)
        cpu_temp_point = Point(socket.gethostname()).field("cpu_temp", cpu_temp)

        write_api.write(bucket="pcstats", record=[cpu_load_point, ram_total_point, ram_used_point, ram_free_point,
            ram_percent_used_point, disk_total_point, disk_used_point, disk_free_point, disk_percent_used_point,
            cpu_temp_point])

        time.sleep(5)


def get_cpu_temperature():
    process = Popen(['vcgencmd', 'measure_temp'], stdout=PIPE)
    output, _error = process.communicate()
    return float(output[output.index('=') + 1:output.rindex("'")])
    

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("url")
    parser.add_argument("org")
    parser.add_argument("token")
    
    args = parser.parse_args()

    client, write_api = initialize_client(args)

    process = Process(target = write_pc_stats, args = (write_api,))
    process.start()

    
    while(1):
        time.sleep(10)

    client.close()




if __name__ == "__main__":
    main()