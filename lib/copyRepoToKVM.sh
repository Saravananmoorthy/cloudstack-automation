#!/usr/bin/env bash
scp  -r -q -o StrictHostKeyChecking=no -i /root/.ssh/id_rsa.cloud /tmp/cloudstack.repo root@$1:/tmp/
