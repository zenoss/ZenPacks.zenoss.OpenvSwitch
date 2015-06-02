/*
 * Customizations to Endpoint Overview Page
 */
Ext.onReady(function() {
    var DEVICE_OVERVIEW_ID = 'deviceoverviewpanel_summary';
    Ext.ComponentMgr.onAvailable(DEVICE_OVERVIEW_ID, function(){
        var box = Ext.getCmp(DEVICE_OVERVIEW_ID);
        box.removeField('uptime');
        box.removeField('memory');
    });

    var DEVICE_OVERVIEW_IDSUMMARY = 'deviceoverviewpanel_idsummary';
    Ext.ComponentMgr.onAvailable(DEVICE_OVERVIEW_IDSUMMARY, function(){
        var box = Ext.getCmp(DEVICE_OVERVIEW_IDSUMMARY);
        box.removeField('tagNumber');
        box.replaceField('serialNumber');
    });

    var DEVICE_OVERVIEW_DESCRIPTION =
        'deviceoverviewpanel_descriptionsummary';
    Ext.ComponentMgr.onAvailable(DEVICE_OVERVIEW_DESCRIPTION, function(){
        var box = Ext.getCmp(DEVICE_OVERVIEW_DESCRIPTION);
        box.removeField('rackSlot');
        box.removeField('hwManufacturer');
        box.removeField('hwModel');
        box.removeField('osManufacturer');
        box.removeField('osModel');

        box.addField({name: 'ovsVersion',
                      fieldLabel: _t('Open vSwitch Version'),
                      xtype: 'displayfield'});
        box.addField({name: 'ovsDBVersion',
                      fieldLabel: _t('Open vSwitch Database Version'),
                      xtype: 'displayfield'});
        box.addField({name: 'ovsTitle',
                      fieldLabel: _t('Open vSwitch Database Name'),
                      xtype: 'displayfield'});
    });

    var DEVICE_OVERVIEW_SNMP = 'deviceoverviewpanel_snmpsummary';
    Ext.ComponentMgr.onAvailable(DEVICE_OVERVIEW_SNMP, function(){
        var box = Ext.getCmp(DEVICE_OVERVIEW_SNMP);
        box.removeField('snmpSysName');
        box.removeField('snmpLocation');
        box.removeField('snmpContact');
        box.removeField('snmpDescr');
        box.removeField('snmpCommunity');
        box.removeField('snmpVersion');

        box.addField({name: 'numberBridges',
                      fieldLabel: _t('Number of Bridges'),
                      xtype: 'displayfield'});
        box.addField({name: 'numberPorts',
                      fieldLabel: _t('Number of Ports'),
                      xtype: 'displayfield'});
        box.addField({name: 'numberFlows',
                      fieldLabel: _t('Number of Flows'),
                      xtype: 'displayfield'});
        box.addField({name: 'numberInterfaces',
                      fieldLabel: _t('Number of Interfaces'),
                      xtype: 'displayfield'});
    });

    /* Hide Software component, as it always empty */
    var DEVICE_ELEMENTS = "subselecttreepaneldeviceDetailNav"
    Ext.ComponentMgr.onAvailable(DEVICE_ELEMENTS, function(){
        var DEVICE_PANEL = Ext.getCmp(DEVICE_ELEMENTS);
        Ext.apply(DEVICE_PANEL, {
            listeners: {
                afterrender: function() {
                    var tree = Ext.getCmp(DEVICE_PANEL.items.items[0].id);
                    var items = tree.store.data.items;
                    for (i in items){
                        if (items[i].data.id.match(/software*/)){
                            try {
                                tree.store.remove(items[i]);
                                tree.store.sync();
                            } catch(err){}
                        }
                    }
                }
            }
        })
    })
});
