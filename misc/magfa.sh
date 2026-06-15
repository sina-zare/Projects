#!/bin/bash

# Zabbix passes $1=phone, $2=message
PHONE="$1"
MESSAGE="$2"

# Magfa API credentials
USERNAME="abramad_41307"
PASSWORD="XXXXXXXX"
DOMAIN="abramad"
FROM="98300041307"

# Send SMS using curl
RESPONSE=$(curl --silent --get \
  --data-urlencode "username=${USERNAME}" \
  --data-urlencode "password=${PASSWORD}" \
  --data-urlencode "domain=${DOMAIN}" \
  --data-urlencode "service=enqueue" \
  --data-urlencode "from=${FROM}" \
  --data-urlencode "to=${PHONE}" \
  --data-urlencode "message=${MESSAGE}" \
  "https://sms.magfa.com/api/http/sms/v1")