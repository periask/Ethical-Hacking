#!/usr/bin/env python3

import sys
import os
import re
import socket
import argparse
import subprocess
import ipaddress
import datetime
import time
from pyroute2 import IPRoute
import concurrent.futures

def hms_string(sec_elapsed):
    h = int(sec_elapsed / (60 * 60))
    m = int((sec_elapsed % (60 * 60)) / 60)
    s = sec_elapsed % 60.
    return "{}h:{:>02}m:{:>05.2f}s".format(h, m, s)

def ping(target):
    try:
        if str(target):
            cmd = ['/usr/bin/fping', '-c', '1', target]
            output = subprocess.Popen(cmd,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE).communicate()[0]
            return output
        else:
            return ""

    except KeyboardInterrupt:
        sys.exit()
    except:
        print(" ".join(cmd), sys.exc_info())

def findAllActiveHosts():
    ip = IPRoute()
    activeHosts = []
    for x in ip.get_addr():
        if x.get_attr('IFA_LABEL') != "lo":
            interface = None

            if ":" not in x.get_attr('IFA_ADDRESS'):
                interface = ipaddress.IPv4Interface('{}/{}'.format(x.get_attr('IFA_ADDRESS'), x['prefixlen']))

            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=300) as executor:
                    data_returned = {executor.submit(ping, str(target)): target for target in ipaddress.ip_network(str(interface.network)).hosts()}
                for data in concurrent.futures.as_completed(data_returned):
                    l = data_returned[data]
                    output = data.result()
                    if "0% loss" in output.decode('utf-8'):
                        activeHosts.append(str(l))
            except KeyboardInterrupt:
                sys.exit()
            except:
                pass
    ip.close()
    return activeHosts

def scanPort(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket.setdefaulttimeout(2)
    result = s.connect_ex((host, port))
    s.close()
    return result

def main():
    hosts = findAllActiveHosts()
    activePorts = {}
    for host in hosts:
        print("Host:", host)
        activePorts[host] = []
        start_time = time.time()

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1000) as executor:
                data_returned = {executor.submit(scanPort, host, port): (host, port) for port in range(1, 2**16)}
                count = 0;
                for data in concurrent.futures.as_completed(data_returned):
                    (h, p) = data_returned[data]
                    result = data.result()
                    if result == 0:
                        print("    ", h, p, "is open.")
                        activePorts[host].append(p)
                        count += 1
        except KeyboardInterrupt:
            sys.exit()

        end_time = time.time()
        print("Total {} port(s) are open. Took {}".format(count,
                                    hms_string(end_time - start_time)))
    return activePorts

if __name__ == "__main__":
    activePorts = main()
    for key in activePorts.keys():
        print(key, activePorts[key])
