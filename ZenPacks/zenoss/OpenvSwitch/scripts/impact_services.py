##############################################################################
#
# Copyright (C) Zenoss, Inc. 2014, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import sys
import os
import urllib2
import base64
import json
import subprocess

ZENPACK_NAME = 'ZenPacks.zenoss.OpenvSwitch'


def RunBashCommand(cmd):


    p = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    (stdout, stderr) = p.communicate()
    if p.returncode == 0:
        if len(stdout) > 0:
            return stdout[:stdout.index('\n')]
        else:
            return None
    elif len(stderr) > 0:
        return stderr
    else:
        try:
            message = json.loads(stdout)['error']
        except Exception:
            message = stderr
        return message

# Create a service organizer
#  returns: uid of the created organizer
def add_service_organizer(base, name):
    return RunBashCommand(["/bin/bash", "-c", '. impact_utils.sh; zenoss_add_service_organizer \"' + base + '\" \"' + name + '\"'])

# Add multiple entities to a service
def add_to_service (node, field):
    return RunBashCommand(["/bin/bash", "-c", '. impact_utils.sh; zenoss_add_service \"' + node + '\" \"' + field + '\"'])

# Add multiple entities to a service
def add_to_dynamic_service (svc, impactor):
    RunBashCommand(["/bin/bash", "-c", '. impact_utils.sh; zenoss_add_to_dynamic_service \"' + svc + '\" \"' + impactor + '\"'])

# delete node
def delete_node (nodeuid):
    return RunBashCommand(["/bin/bash", "-c", '. impact_utils.sh; zenoss_delete_node ' + nodeuid])

# Add standard global policy to a service
def add_global_polices(node_uid, meta_list):
    return RunBashCommand(["/bin/bash", "-c", '. impact_utils.sh; add_standard_global_polices ' + node_uid + ' ' + meta_list])

def get_data_from_components(credential, component_url, componentname = None):
    request = urllib2.Request(component_url)
    request.add_header("Authorization", "Basic %s" % credential)
    request.add_header("Content-Type", "application/json")
    result = urllib2.urlopen(request)
    data = result.readlines()

    ret_list = []
    if not componentname:
        # ad hoc at its best (or worst)
        # what we need is the text of the anchor tag
        # this text connects component id to component name
        # which is between the line with '<a href=' and the line with '/a>'
        next = False
        for line in data:
            if line.find('<a href=') > -1:
                next = True
                continue
            if next:
                ret_list.append(line.strip())
                next = False
    else:
        # ret_list is just component ids
        data=data[0].strip('[]')
        lines=data.split(', ')
        for line in lines:
            if line.find(componentname) > -1:
                ret_list.append(line[line.index('/'):line.index('>')])

    return ret_list

def find_item_name(items, id):
    name = None
    for item in items:
        if item.find(id) > -1:
            name = item[item.index('(') + 1:item.index(')')]
    return name

def get_node_data(url, username, password, deviceip):
    # Define device variables
    credential_base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
    device_root=url + "/zport/dmd/Devices/Network/OpenvSwitch/devices/"
    ovs_device = device_root + deviceip
    component_root = ovs_device + "/components"
    bridges = get_data_from_components(credential_base64string, component_root, 'Bridge')

    allitems_root = component_root + '/manage_main'
    allitems = get_data_from_components(credential_base64string, allitems_root)

    nodes = {}
    for bridge in bridges:
        bridge_id = bridge[bridge.rindex('/') + 1:]
        bridge_name = find_item_name(allitems, bridge_id)
        nodes[bridge_name] = {}
        nodes[bridge_name]['id'] = bridge

        port_root = ZENOSS_URL + bridge + '/ports'
        ports = get_data_from_components(credential_base64string, port_root, 'Port')
        nodes[bridge_name]['ports'] = []
        for port in ports:
            port_id = port[port.rindex('/') + 1:]
            port_name = find_item_name(allitems, port_id)
            items = {}
            items[port_name] = {}
            items[port_name]['id'] = port
            iface_root = ZENOSS_URL + port + '/interfaces'
            ifaces = get_data_from_components(credential_base64string, iface_root, 'Interface')

            items[port_name]['interfaces'] = []
            for iface in ifaces:
                items[port_name]['interfaces'].append(iface)

            nodes[bridge_name]['ports'].append(items)

        flow_root = ZENOSS_URL + bridge + '/flows'
        flows = get_data_from_components(credential_base64string, flow_root, 'Flow')

        nodes[bridge_name]['flows'] = []
        for flow in flows:
            nodes[bridge_name]['flows'].append(flow)

    return nodes

if __name__ == '__main__':
    # commandline operations for populating SERVICES for impact
    if len(sys.argv) != 4:
        print "Usage: python %s <Zenoss GUI username> <Zenoss GUI password> <OpenvSwitch device IP address>" % sys.argv[0]
        sys.exit(0)

    cwd = os.getcwd()
    utilmodule = cwd + '/impact_utils.sh'
    if not os.path.exists(utilmodule):
        print "The file, impact_utils.sh, must be located in the same directory as %s" % sys.argv[0]
        sys.exit(0)

    ZENOSS_URL="http://localhost:8080"
    ZENOSS_USERNAME=sys.argv[1]
    ZENOSS_PASSWORD=sys.argv[2]
    ZENOSS_DEVICE_IP=sys.argv[3]

    # UID = '/zport/dmd/DynamicServices/' + <organizer name>
    DASHBOARD_UID='/zport/dmd/DynamicServices/Dashboard'
    OVSAPP_UID='/zport/dmd/DynamicServices/OVS_Application'

    # for whatever reason, when an OVS device is created, the device name is its IP,
    # not the device name used during device creation
    nodes = get_node_data(ZENOSS_URL, ZENOSS_USERNAME, ZENOSS_PASSWORD, ZENOSS_DEVICE_IP)

    # delete existing organizers to start anew
    delete_node(DASHBOARD_UID)
    delete_node(OVSAPP_UID)

    # populate SERVICE for impact
    # Create service organizers
    ovs_org = add_service_organizer("/", "OVS_Application")

    # Create dashboard organizers
    dashboard_org = add_service_organizer("/", "Dashboard")

    # Create external bridge service nodes for Openv Switch
    # nodes.keys() contain bridge ids
    for nkey in nodes.keys():
        svc_node = add_to_service(ovs_org, nkey)
        add_global_polices(svc_node, 'DynamicService')

        for port in nodes[nkey]['ports']:
            for pkey in port.keys():
                add_to_dynamic_service(svc_node, port[pkey]['id'])
                for iface in port[pkey]['interfaces']:
                    add_to_dynamic_service(svc_node, iface)

        for flow in nodes[nkey]['flows']:
            add_to_dynamic_service(svc_node, flow)

    # Create Open vSwitch service node
    open_vSwitch = add_to_service(ovs_org, "Open_vSwitch")
    add_global_polices(open_vSwitch, 'DynamicService')
    for nkey in nodes.keys():
        add_to_dynamic_service(open_vSwitch, nodes[nkey]['id'])

    ovs_svc = add_to_service(dashboard_org, "OVS_Service")
    add_to_dynamic_service(ovs_svc, open_vSwitch)
