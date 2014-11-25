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

from Products.DataCollector.plugins.CollectorPlugin import CommandPlugin, PythonPlugin
from Products.DataCollector.plugins.DataMaps import ObjectMap, RelationshipMap
from Products.ZenUtils.Utils import prepId

from ZenPacks.zenoss.OpenvSwitch.utils import add_local_lib_path, zenpack_path
add_local_lib_path()


class OpenvSwitch(CommandPlugin):
    command = (
        '('
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

        # database
        dbs = self.__str_to_dict(command_strings[0])
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

        # bridges
        brdgs = self.__str_to_dict(command_strings[1])
        bridges = []
        for brdg in brdgs:
            dbid = [db['_uuid'] for db in dbs \
                    if brdg['_uuid'] in db['bridges']]
            bridges.append(ObjectMap(
                modname='ZenPacks.zenoss.OpenvSwitch.Bridge',
                data={
                'id':     'bridge-{0}'.format(brdg['_uuid']),
                'title':  brdg['name'],
                'bridgeId': brdg['_uuid'],
                'set_database':'database-{0}'.format(dbid[0]),
                }))


        if len(bridges) > 0:
            LOG.info('Found %d bridges on %s', len(bridges), device.id)
        else:
            LOG.info('No bridge found on %s', device.id)
            return None

        # ports
        prts = self.__str_to_dict(command_strings[2])
        ports = []
        # import pdb;pdb.set_trace()
        for port in prts:
            brdgId = [brdg['_uuid'] for brdg in brdgs \
                       if port['_uuid'] in brdg['ports']]
            dbid = [db['_uuid'] for db in dbs \
                    if brdgId[0] in db['bridges']]
            ports.append(ObjectMap(
                modname='ZenPacks.zenoss.OpenvSwitch.Port',
                data={
                'id':     'port-{0}'.format(port['_uuid']),
                'title':  port['name'],
                'portId': port['_uuid'],
                'tag_':   port['tag'],
                'set_bridge':'bridge-{0}'.format(brdgId[0]),
                'set_database':'database-{0}'.format(dbid[0]),
                }))


        if len(ports) > 0:
            LOG.info('Found %d ports on %s', len(ports), device.id)
        else:
            LOG.info('No port found on %s', device.id)
            return None

        # interfaces
        ifaces = self.__str_to_dict(command_strings[3])
        interfaces = []
        for iface in ifaces:
            if iface['link_speed'] == 10000000000:
                lspd = '10 Gb'
            elif iface['link_speed'] == 1000000000:
                lspd = '1 Gb'
            elif iface['link_speed'] == 100000000:
                lspd = '100 Mb'
            else:
                lspd = 'unknown'
            amac = ''
            if 'attached-mac' in iface['external_ids']:
                amac = iface['external_ids']['attached-mac'].upper()
            prtid = [prt['_uuid'] for prt in prts \
                    if iface['_uuid'] in prt['interfaces']]
            interfaces.append(ObjectMap(
                modname='ZenPacks.zenoss.OpenvSwitch.Interface',
                data={
                'id':     'interface-{0}'.format(iface['_uuid']),
                'title':  iface['name'],
                'interfaceId': iface['_uuid'],
                'type_': iface['type'],
                'mac': iface['mac_in_use'].upper(),
                'amac': amac,
                'lstate': iface['link_state'].upper(),
                'astate': iface['admin_state'].upper(),
                'lspeed': lspd,
                'mtu': iface['mtu'],
                'duplex': iface['duplex'],
                'set_port':'port-{0}'.format(prtid[0]),
                }))


        if len(interfaces) > 0:
            LOG.info('Found %d interfaces on %s', len(interfaces), device.id)
        else:
            LOG.info('No interface found on %s', device.id)
            return None

        objmaps = {
            'databases': databases,
            'bridges': bridges,
            'ports': ports,
            'interfaces': interfaces,
            }

        # Apply the objmaps in the right order.
        componentsMap = RelationshipMap(relname='components')
        for i in ('databases', 'bridges', 'ports', 'interfaces',):
            for objmap in objmaps[i]:
                componentsMap.append(objmap)

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
