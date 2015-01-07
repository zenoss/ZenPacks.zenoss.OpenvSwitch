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

import Globals
from Products.ZenUtils.Utils import unused
unused(Globals)

from ZenPacks.zenoss.Impact.impactd import Trigger


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

# Add standard global policy to a service
# Constants to avoid typos.
AVAILABILITY = 'AVAILABILITY'
PERCENT = 'policyPercentageTrigger'
THRESHOLD = 'policyThresholdTrigger'
DOWN = 'DOWN'
DEGRADED = 'DEGRADED'
ATRISK = 'ATRISK'
def add_standard_global_polices(node_guid, node_uid, meta_list):

    triggers = [
        ('DOWN when 100% leafs DOWN', PERCENT, AVAILABILITY, {
            'dependentState': DOWN,
            'threshold': '100',
            'state': DOWN,
            'metaTypes': ["OpenvSwitch"],
            }),

        ('DEGRADED when 50% leafs DOWN', PERCENT, AVAILABILITY, {
            'dependentState': DOWN,
            'threshold': '50',
            'state': DEGRADED,
            'metaTypes': ["OpenvSwitch"],
            }),

        ('ATRISK when >=2 leafs DOWN', THRESHOLD, AVAILABILITY, {
            'dependentState': DOWN,
            'threshold': '2',
            'state': ATRISK,
            'metaTypes': ["OpenvSwitch"],
            }),
        ]

    for trigger_args in triggers:
        yield Trigger(node_guid, *trigger_args)

    # RunBashCommand(["/bin/bash",
    #                 "-c",
    #                 '. impact_utils.sh; zenoss_add_policy \"global\" ' + \
    #                 '\"' + node_uid + '\"' + \
    #                 " AVAILABILITY 50 policyPercentageTrigger ATRISK DOWN " + \
    #                 meta_list])

def get_data_from_components(credential, component_url, clue):
    request = urllib2.Request(component_url)
    request.add_header("Authorization", "Basic %s" % credential)
    request.add_header("Content-Type", "application/json")
    result = urllib2.urlopen(request)
    data = result.readlines()

    ret_list = []
    if len(clue) == 0:
        # ad hoc at its best (or worst)
        # what we need is the line (the text of a element)
        # next to the line with '<a href='
        # this list connects id to name
        next = False
        for x in data:
            if x.find('<a href=') > -1:
                next = True
                continue
            if next:
                ret_list.append(x.strip())
                next = False
    else:
        # this list is just ids
        x1=data[0].strip('[]')
        x2=x1.split(', ')
        for x in x2:
            if x.find(clue) > -1:
                ret_list.append(x[x.index('/'):x.index('>')])

    return ret_list

def find_item_name(items, id):
    name = None
    for item in items:
        if item.find(id) > -1:
            name = item[item.index('(') + 1:item.index(')')]
    return name

def get_node_data(url, username, password, ip):
    # Define device variables
    credential_base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
    device_root=url + "/zport/dmd/Devices/Network/OpenvSwitch/devices/"
    ovs_device = device_root + ip
    component_root = ovs_device + "/components"
    bridges = get_data_from_components(credential_base64string, component_root, 'Bridge')

    allitems_root = component_root + '/manage_main'
    allitems = get_data_from_components(credential_base64string, allitems_root, '')

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
    # commandline operations for populating SERVICES
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

    nodes = get_node_data(ZENOSS_URL, ZENOSS_USERNAME, ZENOSS_PASSWORD, ZENOSS_DEVICE_IP)
    # print nodes

    # populate SERVICE for impact

    # Create service organizers
    ovs_org = add_service_organizer("/", "OVS_Application")

    # Create dashboard organizers
    dashboard_org = add_service_organizer("/", "Dashboard")

    # Create external bridge service nodes for Openv Switch
    # nodes.keys() contain bridge ids
    # import pdb;pdb.set_trace()
    for nkey in nodes.keys():
        svc_node = add_to_service(ovs_org, nkey)
        #add_standard_global_polices(svc_node, '\"DynamicService\"')

        for port in nodes[nkey]['ports']:
            for pkey in port.keys():
                add_to_dynamic_service(svc_node, port[pkey]['id'])
                for iface in port[pkey]['interfaces']:
                    add_to_dynamic_service(svc_node, iface)

        # import pdb;pdb.set_trace()
        for flow in nodes[nkey]['flows']:
            add_to_dynamic_service(svc_node, flow)

    # Create Open vSwitch service node
    open_vSwitch = add_to_service(ovs_org, "Open_vSwitch")
    for nkey in nodes.keys():
        add_to_dynamic_service(open_vSwitch, nodes[nkey]['id'])

    ovs_svc = add_to_service(dashboard_org, "OVS_Service")
    add_to_dynamic_service(ovs_svc, open_vSwitch)

    # add_standard_global_polices "$bridge_integration" "DynamicService"
    # add_standard_global_polices "$open_vSwitch" "DynamicService"
