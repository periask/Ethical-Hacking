#!/usr/bin/env python3

import sys
import os
import socket
import argparse
import time
import json
from icmplib import ping
from concurrent.futures import ThreadPoolExecutor, as_completed
import nmap3
import Subnetting

def myArgParger():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--cidrip", type=str, nargs='+',
                        help="CIDR IP (NetworkIP/Prefix)")
    parser.add_argument("-i", "--ip", type=str, nargs='+',
                        help="IP address IP4")
    parser.add_argument("-H", "--host", type=str, nargs='+',
                        help="Host name IP4")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="increase output verbosity")
    args = parser.parse_args()
    return args, parser


def hms_string(sec_elapsed):
    h = int(sec_elapsed / (60 * 60))
    m = int((sec_elapsed % (60 * 60)) / 60)
    s = sec_elapsed % 60.
    return "{:>02}h:{:>02}m:{:>05.2f}s".format(h, m, s)

def findActiveHosts(hosts):
    start_time = time.time()
    activeHosts = []

    result =[]
    myPing = lambda target: ping(target, count=1, interval=0.2, timeout=2)
    with ThreadPoolExecutor(400) as exe:
        result = exe.map(myPing, hosts)
    exe.shutdown(wait=False)

    for h in result:
        if h.is_alive == True:
            activeHosts.append(h.address)

    end_time = time.time()
    print("findActiveHosts took {}".format(hms_string(end_time - start_time)))
    return activeHosts

def getTcpConnectionStatus(host, port):
    status = "closed"
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        socket.setdefaulttimeout(1)
        result = s.connect_ex((host, port))

    return (port, result)


def tcpPortStatus(host):
    return lambda port: getTcpConnectionStatus(host, port)

def findOpenPorts(host):
    tps = tcpPortStatus(host)
    with ThreadPoolExecutor(400) as exe:
        result = exe.map(tps, range(1, 2**16))
    exe.shutdown(wait=False)

    openPorts = []
    for (p,r) in result:
        if r == 0:
            openPorts.append(p)

    return openPorts

def findActiveHostsAndOpenPorts(hosts):
    nmap = nmap3.Nmap()
    start_time = time.time()
    activeHosts = findActiveHosts(hosts)
    end_time = time.time()
    print("{} {}".format(hms_string(end_time - start_time), activeHosts))

    for host in activeHosts:
        start_time = time.time()
        openPorts = [ str(p) for p in findOpenPorts(host) ]
        end_time = time.time()
        print("{} {}: {}".format(hms_string(end_time - start_time), host, openPorts))


        if len(openPorts) > 0:
            start_time = time.time()
            osInfo = nmap.nmap_version_detection(host, args="-O -p T:{} --script vulners --script-args mincvss+5.0".format(",".join(openPorts)))
            end_time = time.time()
            print("{} {}: OS {}".format(hms_string(end_time - start_time), host, json.dumps(osInfo, indent=4)))
        else:
            start_time = time.time()
            osInfo = nmap.nmap_os_detection(host)
            end_time = time.time()
            print("{} {}: OS {}".format(hms_string(end_time - start_time), host, json.dumps(osInfo, indent=4)))

if __name__ == "__main__":
    args, parser = myArgParger()

    print(args)

    hosts = []
    if args.cidrip:
        cidrips = [*set(args.cidrip)]
        for cidrip in cidrips:
            cidrip = Subnetting.CIDRIP(cidrip)
            hosts += cidrip.getHosts()

    if args.ip:
        hosts += args.ip

    if args.host:
        hosts += args.host
        nmap = nmap3.Nmap()
        for h in args.host:
            results = nmap.nmap_dns_brute_script(h)
            print(json.dumps(results, indent=4))

    sys.exit()
    availablehosts = [*set(hosts)]

    if len(availablehosts) == 0:
        parser.print_help()
        sys.exit()

    activeHosts = findActiveHostsAndOpenPorts(availablehosts)
    # print(activeHosts)
