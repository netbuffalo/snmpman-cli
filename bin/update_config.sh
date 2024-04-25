#!/bin/bash

if [ $# != 1 ]; then
    echo "Invalid argument."
    exit 1
fi

# application home
app_home=$(cd $(dirname $0)/.. && pwd)
config=$app_home/config

if [ ! -f $1 ];
then
    echo "file ($1) does not exit."
    exit 1
fi

if [ -d $config ];
then
    echo "updating snmpman config file..."
    rm -rf $config && tar xzf $1 -C $app_home && supervisorctl restart snmpman
fi
