#!/usr/bin/env bash

curl ${1:-https://s3.amazonaws.com/conceptnet/downloads/2018/edges/conceptnet-assertions-5.6.0.csv.gz} --output conceptnet-assertions.csv.gz