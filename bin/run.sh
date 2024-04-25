#!/bin/bash

# jar
#app_jar="snmpman-cli-2.1.2.jar"
app_jar="snmpman-cli-2.2.0.jar"

# application home
app_home=$(cd $(dirname $0)/.. && pwd)

# java
java_home=$app_home/jre

# export PATH
if [ -d $java_home ];
then
    export PATH=$java_home/bin:$PATH
fi

cd $app_home

# add ip alias
$app_home/bin/ipadd.py -c  $app_home/config/configuration.yaml


#java_opts="-Djava.security.egd=file:/dev/./urandom -Dorg.slf4j.simpleLogger.defaultLogLevel=info -Dorg.slf4j.simpleLogger.showDateTime=true -Dorg.slf4j.simpleLogger.dateTimeFormat=yyyyMMdd-HH:mm:ss -Dorg.slf4j.simpleLogger.showShortLogName=true -Dorg.slf4j.simpleLogger.defaultLogLevel=DEBUG"
java_opts="-Djava.security.egd=file:/dev/./urandom"

java -jar jars/$app_jar -c config/configuration.yaml

