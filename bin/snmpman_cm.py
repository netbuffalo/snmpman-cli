#!/usr/bin/env /opt/venv/js/bin/python
import argparse
import subprocess
import os
import logging

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s %(levelname)s - %(message)s')
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
handler.setFormatter(formatter)
log.addHandler(handler)

def parse(line: str):
    if line.startswith('#'):
        return None

    if ' = ' not in line:
        return None

    oid, data = line.split(' = ')

    if ': ' in data:
        syntax, value = data.split(': ', 1)
        mobject = {'oid': oid.strip(), 'syntax': syntax.strip(), 'val': value.strip(), 'raw': line}
    else:
        mobject = {'oid': oid.strip(), 'val': None, 'raw': line}

    return mobject

def store(mib: dict, mobject: dict):
    if mobject is None:
        return mib

    oid = mobject['oid']

    if mobject['val'] is not None:
        mib[oid] = mobject

    return mib

def snmpget(host: str, oids: list, community: str = 'public'):
    objects = []
    for oid in oids:
        name = oid['oid']
        if 'name' in oid:
            name = oid['name']

        log.info(f'getting {name} from {host}...')

        command = f'snmpget -v2c -OxbenU -t 3 -r 1 -c {community} {host} {oid["oid"]}'

        process = subprocess.run([command],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
                shell=True,
                timeout=30,
                input=None)

        if process.returncode == 0:
            for out in process.stdout.splitlines():
                mobject = parse(out)
                objects.append(mobject)
        else:
#           for out in process.stderr.splitlines():
#               out = ' '.join(out.split())
            pass

    return objects

def snmpwalk(host: str, oids: list, community: str = 'public'):
    objects = []
    for oid in oids:
        name = oid['oid']
        if 'name' in oid:
            name = oid['name']

        log.info(f'walking {name} from {host}...')

        command = f'snmpwalk -v2c -OxbenU -t 3 -r 1 -c {community} {host} {oid["oid"]}'

        process = subprocess.run([command],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
                shell=True,
                timeout=30,
                input=None)

        if process.returncode == 0:
            for out in process.stdout.splitlines():
                mobject = parse(out)
                objects.append(mobject)
        else:
#           for out in process.stderr.splitlines():
#               out = ' '.join(out.split())
            pass

    return objects

def main():
    parser = argparse.ArgumentParser(description='coming soon?')
    parser.add_argument('--cmts', required=True, type=str, help='')
    parser.add_argument('--mac',   required=True, type=str, help='')
    parser.add_argument('--cmtscom', default='public', type=str, help='')
    parser.add_argument('--cmcom',   default='public', type=str, help='')
    args = parser.parse_args()

    total_us = 0
    total_ds = 0

    ##############################################################
    #                          CMTS                              #
    ##############################################################
    # SNMP
    oids = [{
            'oid': '1.3.6.1.2.1.1.5.0',
            'name': 'sysName'
           }]
    [sysname] = snmpget(host=args.cmts, community=args.cmtscom, oids=oids)

    if sysname['val'] is not None:
        name = sysname['val']
        cmtswalk = f'cmts__{name}__{args.cmts}.snmpwalk'
    else:
        cmtswalk = f'cmts__unknown__{args.cmts}.snmpwalk'

    cmtsmib = {}
    if os.path.isfile(cmtswalk):
        with open(cmtswalk) as f:
            lines = f.readlines()
            for l in lines:
                mobject = parse(l.strip())
                if mobject is not None:
                    cmtsmib[mobject['oid']] = mobject

    store(cmtsmib, sysname)

    # SNMP
    oids = [{
            'name': 'sysUpTime',
            'oid': f'1.3.6.1.2.1.1.3.0'
           }]

    objects = snmpget(host=args.cmts, community=args.cmtscom, oids=oids)

    for o in objects:
        store(cmtsmib, o)

    # SNMP
    hfcmac = args.mac.replace(':', '').replace(' ', '').lower()
    decimals = []
    for i in range(0, len(hfcmac), 2):
        octet = hfcmac[i:i+2]
        decimals.append(str(int(octet, base=16)))

    oids = [{
            'name': 'docsIfCmtsCmPtr',
            'oid': f'1.3.6.1.2.1.10.127.1.3.7.1.2.{".".join(decimals)}'
           }]

    [ptr] = snmpget(host=args.cmts, community=args.cmtscom, oids=oids)

    store(cmtsmib, ptr)

    pval = ptr['val']

    oids = [
            {'name': 'docsIf3CmtsCmRegStatusMacAddr', 'oid': f'1.3.6.1.4.1.4491.2.1.20.1.3.1.2.{pval}'},
            {'name': 'docsIf3CmtsCmRegStatusIPv4Addr', 'oid': f'1.3.6.1.4.1.4491.2.1.20.1.3.1.5.{pval}'},
            {'name': 'docsIf3CmtsCmRegStatusValue', 'oid': f'1.3.6.1.4.1.4491.2.1.20.1.3.1.6.{pval}'},
            {'name': 'docsIf3CmtsCmRegStatusLastRegTime', 'oid': f'1.3.6.1.4.1.4491.2.1.20.1.3.1.14.{pval}'}
           ]

    objects = snmpget(host=args.cmts, community=args.cmtscom, oids=oids)

    cmip = '0.0.0.0'
    for o in objects:
        if '1.3.6.1.4.1.4491.2.1.20.1.3.1.5' in o['oid']: # IPv4Addr?
            cmip = '.'.join([str(int(hexs, 16)) for hexs in o['val'].split()])
        store(cmtsmib, o)

    oids = [
            {'oid': f'1.3.6.1.4.1.4491.2.1.20.1.4.1.4.{pval}', 'name': 'docsIf3CmtsCmUsStatusSignalNoise'},
            {'oid': f'1.3.6.1.4.1.4491.2.1.20.1.4.1.7.{pval}', 'name': 'docsIf3CmtsCmUsStatusUnerroreds'},
            {'oid': f'1.3.6.1.4.1.4491.2.1.20.1.4.1.8.{pval}', 'name': 'docsIf3CmtsCmUsStatusCorrecteds'},
            {'oid': f'1.3.6.1.4.1.4491.2.1.20.1.4.1.9.{pval}', 'name': 'docsIf3CmtsCmUsStatusUncorrectables'}
       ]

    usifindex = []
    objects = snmpwalk(host=args.cmts, community=args.cmtscom, oids=oids)
    for o in objects:
        store(cmtsmib, o)
        ifx = o['oid'].split('.')[-1]
        if ifx not in usifindex:
            usifindex.append(ifx)

    total_us = len(usifindex)

    oids = []
    for i in usifindex:
        oids.append({'oid': f'1.3.6.1.2.1.10.127.1.1.2.1.1.{i}', 'name': 'docsIfUpChannelId'})
        oids.append({'oid': f'1.3.6.1.2.1.2.2.1.2.{i}', 'name': 'ifDescr'})
        oids.append({'oid': f'1.3.6.1.2.1.31.1.1.1.1.{i}', 'name': 'ifName'})
        oids.append({'oid': f'1.3.6.1.2.1.31.1.1.1.18.{i}', 'name': 'ifAlias'})

    objects = snmpget(host=args.cmts, community=args.cmtscom, oids=oids)

    for o in objects:
        store(cmtsmib, o)


    objects = snmpget(host=args.cmts, community=args.cmtscom, oids=oids)

    for o in objects:
        store(cmtsmib, o)

    ##############################################################
    #                           CM                               #
    ##############################################################
    oids = [{
            'oid': '1.3.6.1.2.1.1.5.0',
            'name': 'sysName'
           }]
    [sysname] = snmpget(host=cmip, community=args.cmcom, oids=oids)

    cmwalk = f'cm__{hfcmac}__{cmip}.snmpwalk'
#    if sysname['val'] is not None:
#        name = sysname['val']
#        cmwalk = f'cm__{name}__{hfcmac}__{cmip}.snmpwalk'
#    else:
#        cmwalk = f'cm__unknown__{hfcmac}__{cmip}.snmpwalk'

    cmmib = {}
    if os.path.isfile(cmwalk):
        with open(cmwalk) as f:
            lines = f.readlines()
            for l in lines:
                mobject = parse(l.strip())
                if mobject is not None:
                    cmmib[mobject['oid']] = mobject

    store(cmmib, sysname)

    # SNMP
    oids = [
            {'oid': '1.3.6.1.2.1.1.3.0', 'name': 'sysUpTime'},
            {'oid': '1.3.6.1.2.1.69.1.3.2.0', 'name': 'docsDevSwFilename'},
            {'oid': '1.3.6.1.2.1.69.1.3.5.0', 'name': 'docsDevSwCurrentVers'},
            {'oid': '1.3.6.1.2.1.69.1.1.3.0', 'name': 'docsDevResetNow'}
           ]

    objects = snmpget(host=cmip, community=args.cmcom, oids=oids)

    for o in objects:
        store(cmmib, o)

    # SNMP
    oids = [
            {'name': 'docsIfUpChannelId', 'oid': '1.3.6.1.2.1.10.127.1.1.2.1.1'},
            {'name': 'docsIfUpChannelFrequency', 'oid': '1.3.6.1.2.1.10.127.1.1.2.1.2'},
            {'name': 'docsIfUpChannelWidth', 'oid': '1.3.6.1.2.1.10.127.1.1.2.1.3'}
           ]

    objects = snmpwalk(host=cmip, community=args.cmcom, oids=oids)

    for o in objects:
        store(cmmib, o)

    # SNMP
    oids = [
            {'name': 'docsIfUpstreamChannelTable', 'oid': '1.3.6.1.4.1.4491.2.1.20.1.2'},
           ]

    objects = snmpwalk(host=cmip, community=args.cmcom, oids=oids)

    for o in objects:
        store(cmmib, o)

    # SNMP
    oids = [
            {'name': 'docsIfCmStatusTable', 'oid': '1.3.6.1.2.1.10.127.1.2.2'},
           ]

    objects = snmpwalk(host=cmip, community=args.cmcom, oids=oids)

    for o in objects:
        store(cmmib, o)

    # SNMP
    oids = [
            {'name': 'docsIfDownstreamChannelTable', 'oid': '1.3.6.1.2.1.10.127.1.1.1'},
           ]

    objects = snmpwalk(host=cmip, community=args.cmcom, oids=oids)

    for o in objects:
        store(cmmib, o)
        if '1.3.6.1.2.1.10.127.1.1.1.1.1' in o['oid']:
            total_ds += 1

    # SNMP
    oids = [
            {'name': 'docsIfSignalQualityTable', 'oid': '1.3.6.1.2.1.10.127.1.1.4'},
           ]

    objects = snmpwalk(host=cmip, community=args.cmcom, oids=oids)

    for o in objects:
        store(cmmib, o)

    # SNMP
    oids = [
            {'name': 'ifTable', 'oid': '1.3.6.1.2.1.2.2'},
           ]

    objects = snmpwalk(host=cmip, community=args.cmcom, oids=oids)

    for o in objects:
        store(cmmib, o)

    # SNMP
    oids = [
            {'name': 'dot1dTpFdbAddress', 'oid': '1.3.6.1.2.1.17.4.3.1.1'},
           ]

    objects = snmpwalk(host=cmip, community=args.cmcom, oids=oids)

    fdbdecmac = []
    for o in objects:
        fdbdecmac.append(o['oid'].split(oids[0]['oid'])[1])
        store(cmmib, o)

    ##############################################################
    #                          CISCO                             #
    ##############################################################
    oids = []
    for d in fdbdecmac:
        oids.append({'name': 'cdxCmCpeType', 'oid': f'1.3.6.1.4.1.9.9.116.1.3.1.1.2{d}'})
        oids.append({'name': 'cdxCmCpeIpAddress', 'oid': f'1.3.6.1.4.1.9.9.116.1.3.1.1.3{d}'})

    objects = snmpget(host=args.cmts, community=args.cmtscom, oids=oids)

    for o in objects:
        store(cmtsmib, o)

    ##############################################################
    #                           OFDM                             #
    ##############################################################
    # CMTS
    # SNMP
    oids = [
           {'name': 'docsIf31CmtsCmUsOfdmaChannelRxPower', 'oid': f'.1.3.6.1.4.1.4491.2.1.28.1.4.1.1.{pval}'},
           {'name': 'docsIf31CmtsCmUsOfdmaChannelMeanRxMer', 'oid': f'.1.3.6.1.4.1.4491.2.1.28.1.4.1.2.{pval}'},
           {'name': 'docsIf31CmtsCmUsOfdmaChannelStdDevRxMer', 'oid': f'.1.3.6.1.4.1.4491.2.1.28.1.4.1.3.{pval}'},
           {'name': 'docsIf31CmtsCmUsOfdmaChannelRxMerThreshold', 'oid': f'.1.3.6.1.4.1.4491.2.1.28.1.4.1.4.{pval}'},
           {'name': 'docsIf31CmtsCmUsOfdmaChannelThresholdRxMerValue ', 'oid': f'.1.3.6.1.4.1.4491.2.1.28.1.4.1.5.{pval}'},
           {'name': 'docsIf31CmtsCmUsOfdmaChannelThresholdRxMerHighestFreq', 'oid': f'.1.3.6.1.4.1.4491.2.1.28.1.4.1.6.{pval}'},
           {'name': 'docsIf31CmtsCmUsOfdmaChannelMicroreflections', 'oid': f'.1.3.6.1.4.1.4491.2.1.28.1.4.1.7.{pval}'},
           {'name': 'docsIf31CmtsCmUsOfdmaChannelHighResolutionTimingOffset', 'oid': f'.1.3.6.1.4.1.4491.2.1.28.1.4.1.8.{pval}'},
           {'name': 'docsIf31CmtsCmUsOfdmaChannelIsMuted', 'oid': f'.1.3.6.1.4.1.4491.2.1.28.1.4.1.9.{pval}'},
           {'name': 'docsIf31CmtsCmUsOfdmaChannelRangingStatus', 'oid': f'.1.3.6.1.4.1.4491.2.1.28.1.4.1.10.{pval}'},
           {'name': 'docsIf31CmtsCmUsOfdmaChannelCurPartialSvcReasonCode', 'oid': f'.1.3.6.1.4.1.4491.2.1.28.1.4.1.11.{pval}'},
           {'name': 'docsIf31CmtsCmUsOfdmaChannelLastPartialSvcTime', 'oid': f'.1.3.6.1.4.1.4491.2.1.28.1.4.1.12.{pval}'},
           {'name': 'docsIf31CmtsCmUsOfdmaChannelLastPartialSvcReasonCode', 'oid': f'.1.3.6.1.4.1.4491.2.1.28.1.4.1.13.{pval}'},
           {'name': 'docsIf31CmtsCmUsOfdmaChannelNumPartialSvcIncidents', 'oid': f'.1.3.6.1.4.1.4491.2.1.28.1.4.1.14.{pval}'},
           {'name': 'docsIf31CmtsCmUsOfdmaChannelNumPartialChanIncidents', 'oid': f'.1.3.6.1.4.1.4491.2.1.28.1.4.1.15.{pval}'}
          ]

    objects = snmpwalk(host=args.cmts, community=args.cmtscom, oids=oids)

    for o in objects:
        store(cmtsmib, o)

    # SNMP
    oids = [
            {'name': 'docsIf31CmtsCmUsOfdmaProfileTotalCodewords', 'oid': f'1.3.6.1.4.1.4491.2.1.28.1.5.1.1.{pval}'},
            {'name': 'docsIf31CmtsCmUsOfdmaProfileCorrectedCodewords', 'oid': f'1.3.6.1.4.1.4491.2.1.28.1.5.1.2.{pval}'},
            {'name': 'docsIf31CmtsCmUsOfdmaProfileUnreliableCodewords', 'oid': f'1.3.6.1.4.1.4491.2.1.28.1.5.1.3.{pval}'}
           ]

    objects = snmpwalk(host=args.cmts, community=args.cmtscom, oids=oids)

    oids = []
    for o in objects:
        store(cmtsmib, o)
        # resolve ifdescr.
        ifindex = int(o['oid'].split('.')[-2])
        ifdesc  = f'1.3.6.1.2.1.2.2.1.2.{ifindex}'
        if not any(oid['oid'] == ifdesc for oid in oids):
            oids.append({'oid': ifdesc, 'name': 'ifDescr'})

    objects = snmpget(host=args.cmts, community=args.cmtscom, oids=oids)

    for o in objects:
        store(cmtsmib, o)

    # CM
    # SNMP
    oids = [
            {'name': 'docsIf31CmDsOfdmChannelPowerTable', 'oid': '1.3.6.1.4.1.4491.2.1.28.1.11'},
           ]

    objects = snmpwalk(host=cmip, community=args.cmcom, oids=oids)

    for o in objects:
        store(cmmib, o)

    # SNMP
    oids = [
            {'name': 'docsIf31CmDsOfdmChanTable', 'oid': '1.3.6.1.4.1.4491.2.1.28.1.9'},
           ]

    objects = snmpwalk(host=cmip, community=args.cmcom, oids=oids)

    for o in objects:
        store(cmmib, o)

    # SNMP
    oids = [
            {'name': 'docsIf31CmDsOfdmProfileStatsTable', 'oid': '1.3.6.1.4.1.4491.2.1.28.1.10'},
           ]

    objects = snmpwalk(host=cmip, community=args.cmcom, oids=oids)

    for o in objects:
        store(cmmib, o)

    # SNMP
    oids = [
            {'name': 'docsIf31CmUsOfdmaProfileStatsTable', 'oid': '1.3.6.1.4.1.4491.2.1.28.1.14'},
           ]

    objects = snmpwalk(host=cmip, community=args.cmcom, oids=oids)

    for o in objects:
        store(cmmib, o)

    # SNMP
    oids = [
            {'name': 'docsIf31CmUsOfdmaChanTable', 'oid': '1.3.6.1.4.1.4491.2.1.28.1.13'},
           ]

    objects = snmpwalk(host=cmip, community=args.cmcom, oids=oids)

    for o in objects:
        store(cmmib, o)

    ##############################################################
    #                          WRITE                             #
    ##############################################################
    log.info('writing mib data....')
    # write data to snmpwalk file.
    with open(cmtswalk, mode='w') as f:
        for s in sorted(cmtsmib.items()):
            key, val = s
            raw = val['raw']
            f.write(f'{raw}\n')

    # write data to snmpwalk file.
    with open(cmwalk, mode='w') as f:
        for s in sorted(cmmib.items()):
            key, val = s
            raw = val['raw']
            f.write(f'{raw}\n')

    log.info(f'hfcmac: {hfcmac}, hfcip: {cmip}, us: {total_us}, ds: {total_ds}')

if __name__ == '__main__':
    main()

