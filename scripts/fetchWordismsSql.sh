#!/bin/bash

if [ ! -e ~/.my.cnf ]; then
  echo "Missing ~/.my.cnf"
  echo "Copy global my.cnf to ~/.my.cnf, set 'user' and 'password' in client section"
  echo "And re-run the script."
  exit 1
fi

echo "Copying mysqldump to $HOSTNAME"
ssh derwiki@wordisms.org "mysqldump wordisms > ~/wordisms.sql"
scp derwiki@wordisms.org:/home/derwiki/wordisms.sql .
if [ -e ./wordisms.sql ]; then
  echo "Dropping and re-creating wordisms DB locally"
  echo "drop database wordisms"   | mysql
  echo "create database wordisms" | mysql
  echo "Importing wordisms.sql"
  mysql wordisms < wordisms.sql
  rm ./wordisms.sql
else
  echo "Could not copy wordisms.sql locally"
fi

