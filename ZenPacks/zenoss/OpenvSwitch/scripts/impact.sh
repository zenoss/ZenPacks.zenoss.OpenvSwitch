#!/bin/bash
##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

if  [ $# -ne 2 ]; then
    echo $#
    echo "Usage: ./impact.sh <Zenoss GUI username> <Zenoss GUI password>"
    exit
fi

ZENOSS_URL="http://localhost:8080"
ZENOSS_USERNAME=$1
ZENOSS_PASSWORD=$2

source ./impact_utils.sh

if [ "$1" = "--cleanup" ]; then
    zenoss_delete_node "/zport/dmd/DynamicServices/OVS - Application"
    zenoss_delete_node "/zport/dmd/DynamicServices/Dashboard"
    exit 1
elif [ "$1" = "--help" -o "$1" = "-h" ]; then
    echo $0 [options]
    echo "  --cleanup      delete nodes created by this script"
    echo "  -h, --help     show this message and exit"
    exit
fi

# Add multiple entities to a service
add_to_service () {
    local service_uid="$1"
    for i in "$@" ; do
        zenoss_add_to_dynamic_service "$service_uid" "$i"
    done
}

# Add standard global policy to a service
add_standard_global_polices() {
    local node_uid="$1"
	local meta_list="$2"
    zenoss_add_policy "global" "$node_uid" AVAILABILITY 50 policyPercentageTrigger ATRISK DOWN \"$meta_list\"
    zenoss_add_policy "global" "$node_uid" AVAILABILITY 100 policyPercentageTrigger DOWN DOWN \"$meta_list\"
}

# Define device variables
device_root="/zport/dmd/Devices/Network/OpenvSwitch/devices"
ovs_device=$device_root/192.168.56.122
component_root=$ovs_device/components

# external bridge
port_bridge_ex=$component_root/port-1074d480-c9ba-4d8e-9bf4-8812b48f593a
port_tap_70f86603=$component_root/port-2e4958e1-7617-4c17-ab2c-5cb3d5f64e6d
flow_bridge_ex=$component_root/flow-d5c91680-5192-4298-80a4-12ee9337a56e
iface_bridge_ex=$component_root/interface-6228b836-b028-4c4e-a8ee-3bd6457801a7
iface_tap_70f86603=$component_root/interface-43dfc185-bf6e-4493-8cbd-a3223cd19d7d

# integration bridge
port_bridge_int=$component_root/port-2e4958e1-7617-4c17-ab2c-5cb3d5f64e6d
port_tap_acadae3c=$component_root/port-2bf1b254-1563-4336-bca2-0bc07eeb33de
port_tap_fe15d807=$component_root/port-c364efc5-6ec4-4190-a306-8251df8dd942
port_qvo_f374855e=$component_root/port-90c17eef-b3c6-4fba-bf3b-21ccf5fb2cb0
port_qvo_4fc74179=$component_root/port-a848e976-6439-4f72-b369-463c1fd1c71a
port_qvo_4330319b=$component_root/port-db918c55-ade6-40a2-8903-c19f65710606
port_qvo_43758471=$component_root/port-efcf1700-fe92-42f3-af2b-cfc98aef58aa
flow_bridge_int_1=$component_root/flow-6bce89cc-5f9e-412e-8aee-05bf3cd13fad
flow_bridge_int_2=$component_root/flow-e9cc3647-3f36-4ef3-8e9c-801c6ab686d0
iface_bridge_int=$component_root/interface-43dfc185-bf6e-4493-8cbd-a3223cd19d7d
iface_tap_acadae3c=$component_root/interface-99ae1898-a385-4f65-8bc1-6a54064cb51a
iface_tap_fe15d807=$component_root/interface-cacdc306-d00d-4c08-b29c-9209e04e65b3
iface_qvo_f374855e=$component_root/interface-836f6413-eeb7-4945-9900-0c70b8be136c
iface_qvo_4fc74179=$component_root/interface-4dca1f6e-2dd3-45d8-9ee4-699378af8fbc
iface_qvo_4330319b=$component_root/interface-64c3456c-d655-49cc-bba3-d533202b5ad5
iface_qvo_43758471=$component_root/interface-5867fc9e-5fd5-480a-97e0-a6be9f4c07c6


# Create service organizers
ovs_org=$(zenoss_add_service_organizer "/" "OVS - Application")
echo -n "ovs_org: "; echo $ovs_org

dashboard_org=$(zenoss_add_service_organizer "/" "Dashboard")
echo -n "dashboard_org: "; echo $dashboard_org

# Create external bridge service nodes for Openv Switch
bridge_external=$(zenoss_add_service "$ovs_org" "Bridge - External")
echo -n "bridge_external: "; echo $bridge_external
echo -n "port_bridge_ex: "; echo $port_bridge_ex
echo -n "flow_bridge_ex: "; echo $flow_bridge_ex
echo -n "iface_tap_70f86603: "; echo $iface_tap_70f86603
exit

add_to_service "$bridge_external" "$port_bridge_ex" $port_tap_70f86603 "$flow_bridge_ex" "$iface_bridge_ex" "$iface_tap_70f86603"

# Create integration bridge service nodes for Openv Switch
bridge_integration=$(zenoss_add_service "$ovs_org" "Bridge - Integration")
add_to_service "$bridge_integration" "$port_bridge_int" "$iface_bridge_int"
add_to_service "$bridge_integration" "$port_tap_acadae3c" "$iface_tap_acadae3c"
add_to_service "$bridge_integration" "$port_tap_fe15d807" "$iface_tap_fe15d807"
add_to_service "$bridge_integration" "$port_qvo_f374855e" "$iface_qvo_f374855e"
add_to_service "$bridge_integration" "$port_qvo_4fc74179" "$iface_qvo_4fc74179"
add_to_service "$bridge_integration" "$port_qvo_4330319b" "$iface_qvo_4330319b"
add_to_service "$bridge_integration" "$port_qvo_43758471" "$iface_qvo_43758471"
add_to_service "$bridge_integration" "$flow_bridge_int_1" "$flow_bridge_int_2"

# Create Open vSwitch service node
open_vSwitch=$(zenoss_add_service "$ovs_org" "Open vSwitch")
add_to_service "$open_vSwitch" "$bridge_external" "$bridge_integration"

ovs_svc=$(zenoss_add_service "$dashboard_org" "OVS Service")
add_to_service "$ovs_svc" "$open_vSwitch"

add_standard_global_polices "$bridge_external" "DynamicService"
add_standard_global_polices "$bridge_integration" "DynamicService"
add_standard_global_polices "$open_vSwitch" "DynamicService"
