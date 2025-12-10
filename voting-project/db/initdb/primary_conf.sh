#!/bin/bash
set -e
PGDATA="/var/lib/postgresql/data"

echo "wal_level = replica" >> $PGDATA/postgresql.conf
echo "max_wal_senders = 3" >> $PGDATA/postgresql.conf
echo "hot_standby = on" >> $PGDATA/postgresql.conf

echo "host replication voter 0.0.0.0/0 md5" >> $PGDATA/pg_hba.conf
