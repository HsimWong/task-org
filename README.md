# Task-Org

A submodule of SATFAD, implemented for orchestrating docker-based tasks

## Overview
![Services running on nodes and corresponding dataflow](pics/service.jpg)

## Responsibilities of Each Module
### Node Service
1. Always check if "I am the master"
2. Enable/Disable the master service of current node based on the result
given by `1`.
3. Node registering to the cluster

### Master Service
1. Accepts tasks assigned to the cluster via the subordinate service `Webview Service`
2. Accepts backup info from current master node (when not activated)
3. Trigger the backup process (when activated)
4. Always syncing the status of members in the cluster from DNS service

### Slave Service
1. Accepts tasks assigned by `master service`
2. Returns the execution status of tasks to master node
3. Monitors status of sensors, FPGA cores, GPU cores and CPU

### DNS service
1. Provides storage for infos of members in the cluster
2. Handles Node registering
3. Responds to DNS requests
