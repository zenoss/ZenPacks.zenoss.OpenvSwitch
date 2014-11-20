##############################################################################
#
# Copyright (C) Zenoss, Inc. 2013-2014, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import logging
LOG = logging.getLogger('zen.OpenvSwitch')

import re
import json

from twisted.internet.defer import inlineCallbacks, returnValue

from Products.DataCollector.plugins.CollectorPlugin import CommandPlugin, PythonPlugin
from Products.DataCollector.plugins.DataMaps import ObjectMap, RelationshipMap
from Products.ZenUtils.Utils import prepId
from sshclient import SSHClient

from ZenPacks.zenoss.OpenvSwitch.utils import add_local_lib_path
add_local_lib_path()


class OpenvSwitch(CommandPlugin):
    command = (
        '('
        'for ns in $(ip netns list) ; do '
        'echo "$ns" ; '
        'done ; '
        'echo "__COMMAND__" ; '
        'ovs-vsctl list Open_vSwitch ; '
        'echo "__COMMAND__" ; '
        'ovs-vsctl list bridge ; '
        'echo "__COMMAND__" ; '
        'ovs-vsctl list port ; '
        'echo "__COMMAND__" ; '
        'ovs-vsctl list interface ; '
        'echo "__COMMAND__" ; '
        ')'
        )

    def process(self, device, results, unused):
        LOG.info('Trying ovs-vsctl/ip netns on %s', device.id)

        command_strings = results.split('__COMMAND__')
        # namespaces
        nss = command_strings[0]
        # database
        dbs = command_strings[1]
        dbs = self.__str_to_dict(dbs)
        # bridges
        brdgs = command_strings[2]
        brdgs = self.__str_to_dict(brdgs)
        # ports
        prts = command_strings[3]
        prts = self.__str_to_dict(prts)
        # interfaces
        ifaces = command_strings[4]
        ifaces = self.__str_to_dict(ifaces)

        # namespace
        namespaces = []
        for ns in nss.split('\n'):
            if not ns:
                continue

            ns_id = prepId(ns)
            namespaces.append(ObjectMap(
                modname='ZenPacks.zenoss.OpenvSwitch.Namespace',
                data={
                'id': ns_id,
                'title': ns[:ns.index('-')],
                'namespaceId':ns_id[(ns_id.index('-') + 1):],
                }))

        if len(namespaces) > 0:
            LOG.info('Found %d namespaces on %s', len(namespaces), device.id)
        else:
            LOG.info('No namespace found on %s', device.id)
            return None

        # database
        databases = []
        for db in dbs:
            if 'name' in db:
                db_name = db['name']
            else:
                db_name = 'Open_vSwitch'
            databases.append(ObjectMap(
                modname='ZenPacks.zenoss.OpenvSwitch.Database',
                data={
                'id':     'database-{0}'.format(db['_uuid']),
                'title':  db_name,
                'databaseId': db['_uuid'],
                'DB_version': db['db_version'],
                'OVS_version': db['ovs_version'],
                }))


        if len(databases) > 0:
            LOG.info('Found %d databases on %s', len(databases), device.id)
        else:
            LOG.info('No database found on %s', device.id)
            return None

        # bridge
        bridges = []
        for brdg in brdgs:
            bridges.append(ObjectMap(
                modname='ZenPacks.zenoss.OpenvSwitch.Bridge',
                data={
                'id':     'bridge-{0}'.format(brdg['_uuid']),
                'title':  brdg['name'],
                'bridgeId': brdg['_uuid'],
                }))


        if len(bridges) > 0:
            LOG.info('Found %d bridges on %s', len(bridges), device.id)
        else:
            LOG.info('No bridge found on %s', device.id)
            return None

        # ports
        ports = []
        import pdb;pdb.set_trace()
        for port in prts:
            brdgId = [brdg['_uuid'] for brdg in brdgs \
                       if port['_uuid'] in brdg['ports']]
            ports.append(ObjectMap(
                modname='ZenPacks.zenoss.OpenvSwitch.Port',
                data={
                'id':     'port-{0}'.format(port['_uuid']),
                'title':  port['name'],
                'portId': port['_uuid'],
                'tag_':   port['tag'],
                # set_bridge='bridge-{0}'.format(brdgId[0]),
                }))


        if len(ports) > 0:
            LOG.info('Found %d ports on %s', len(ports), device.id)
        else:
            LOG.info('No port found on %s', device.id)
            return None

        # interfaces
        interfaces = []
        for interface in ifaces:
            if interface['link_speed'] == 10000000000:
                lspd = '10 GB'
            elif interface['link_speed'] == 1000000000:
                lspd = '1 GB'
            elif interface['link_speed'] == 100000000:
                lspd = '100 MB'
            else:
                lspd = 'unknown'
            amac = ''
            if 'attached-mac' in interface['external_ids']:
                amac = interface['external_ids']['attached-mac'].upper()
            interfaces.append(ObjectMap(
                modname='ZenPacks.zenoss.OpenvSwitch.Interface',
                data={
                'id':     'interface-{0}'.format(interface['_uuid']),
                'title':  interface['name'],
                'interfaceId': interface['_uuid'],
                'type_': interface['type'],
                'mac': interface['mac_in_use'].upper(),
                'amac': amac,
                'lstate': interface['link_state'].upper(),
                'astate': interface['admin_state'].upper(),
                'lspeed': lspd,
                'mtu': interface['mtu'],
                'duplex': interface['duplex'],
                }))


        if len(interfaces) > 0:
            LOG.info('Found %d interfaces on %s', len(interfaces), device.id)
        else:
            LOG.info('No interface found on %s', device.id)
            return None

        objmaps = {
            'namespaces': namespaces,
            'databases': databases,
            'bridges': bridges,
            'ports': ports,
            'interfaces': interfaces,
            }

        # Apply the objmaps in the right order.
        componentsMap = RelationshipMap(relname='components')
        for i in ('namespaces', 'databases', 'bridges', 'ports', 'interfaces',):
            for objmap in objmaps[i]:
                componentsMap.append(objmap)

        # import pdb;pdb.set_trace()
        return componentsMap

    def __str_to_dict(self, original):
        original = original.split('\n')
        # remove '' from head and tail
        if not original[0]:
            del original[0]
        if not original[-1]:
            del original[-1]

        rets = []
        ret = {}
        for orig in original:
            # an empty string as an item
            if not orig:
                rets.append(ret)
                ret = {}
                continue

            if orig.find(':') > -1:           # key-value pair
                pair = orig.split(':', 1)
                ret[pair[0].strip()] = self.__localparser(pair[1].strip())

        # add the last item to rets
        rets.append(ret)

        return rets

    def __localparser(self, text):
        text = text.strip()

        if text.find('{') == 0 and text.find('}') == (len(text) - 1):        # dict
            ret = {}
            if text.rindex('}') > text.index('{') + 1:                        # dict not empty
                # we are looking at something like {'x'="y", 'u'="v", 'a'='5'}
                content = text.strip('{}')
                if content.find('external_ids') > -1:
                    import pdb;pdb.set_trace()
                if content.find(', ') > -1:
                    clst = content.split(', ')
                    for cl in clst:
                        if cl.find('=') > -1:
                            lst = cl.split('=')
                            if lst[1].find('"') > -1:
                                ret[lst[0]] = lst[1].strip('"')
                            elif str.isdigit(lst[1]):
                                ret[lst[0]] = int(lst[1])
                            else:
                                ret[lst[0]] = lst[1]
                elif content.find('=') > -1:
                    lst = content.split('=')
                    if lst[1].find('"') > -1:
                        ret[lst[0]] = lst[1].strip('"')
                    elif str.isdigit(lst[1]):
                        ret[lst[0]] = int(lst[1])
                    else:
                        ret[lst[0]] = lst[1]
                else:
                    ret = content
        elif text.find('[') == 0 and text.find(']') == (len(text) - 1):        # list
            ret = []
            if (text.rindex(']') > text.index('[') + 1):
                if text.find(', ') > -1:
                    ret = text.strip('[]').split(', ')
                else:
                    ret.append(text.strip('[]'))
        elif text.find('"') > -1:        # string
            ret = text.strip('"')
        elif str.isdigit(text):
            ret = int(text)
        elif text == 'false':
            ret = False
        else:
            ret = text

        return ret
