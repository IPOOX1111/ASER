#!/bin/bash
set -e

DATA="/var/lib/postgresql/data"

if [ -z "$(ls -A $DATA)" ]; then
    echo "Initializing replica..."

    until pg_isready -h postgres-primary -p 5432 -U voter; do
        echo "Waiting for primary..."
        sleep 1
    done

    rm -rf ${DATA:?}/*

    PGPASSWORD=voterpass pg_basebackup -h postgres-primary \
        -D $DATA -U voter -Fp -Xs -P --write-recovery-conf

    # Create standby.signal to enable replica mode
    touch $DATA/standby.signal

    # Configure connection to the primary
    echo "primary_conninfo = 'host=postgres-primary port=5432 user=voter password=voterpass'" >> $DATA/postgresql.auto.conf
fi

exec docker-entrypoint.sh postgres
