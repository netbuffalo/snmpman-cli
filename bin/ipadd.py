#!/usr/bin/env python3
import ipaddress
import argparse
import os

def main():
    # parse options
    parser = argparse.ArgumentParser(description='coming soon?')
    parser.add_argument('-c', '--config', action="store", dest="config", help="snmpman config file.", default='/opt/snmpman-cli/config/configuration.yaml')
    args = parser.parse_args()

    with open(args.config, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('ip') and ':' in line:
                ipaddr = line.split(':')[1].replace('"', '').strip()
                try:
                    command = f'/sbin/ip addr add {ipaddr} dev lo'
                    print(f'executing ip command: {command}')
                    os.popen(command)
                except:
                    pass

if __name__ == '__main__':
    main()
