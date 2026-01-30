#!/usr/bin/env bash
if [ "$2" = "2" ]; then
    echo "run python-nxsconfigserver tests"
    docker exec ndts python test
else
    echo "run python3-nxsconfigserver tests"
    docker exec ndts python3 -m pytest
fi    
if [ "$?" != "0" ]; then exit -1; fi
