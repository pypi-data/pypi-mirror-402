import logging
import glob
import yaml
import json
import traceback

from diffsync import Adapter, Diff, DiffSyncFlags
from diffsync.exceptions import ObjectAlreadyExists
from slugify import slugify
from .exceptions import *
from .models import (
    Tag,
    Manufacturer, 
    DeviceType, 
    InterfaceTemplate,
    ModuleType,
    PowerPortTemplate,
    ConsolePortTemplate,
    ConsoleServerPortTemplate,
    ModuleBayTemplate,
    VirtualChassis,
    PowerOutletTemplate,
    RearPortTemplate,
    FrontPortTemplate,
    Device,
    Interface,
    IPAddress,
    Site,
    DeviceRole,
    AlertRule, 
    AlertTemplate, 
    LibreNMSDeviceGroup,
)
from ..helper_functions import convert_interface_name, expand_ipv6
from ..librenms import LibreNMS
from pprint import pprint


# class NetboxDeviceTypeAdapter(Adapter):

#     manufacturer = Manufacturer
#     device_type = DeviceType
#     module_type = ModuleType
#     interface_template = InterfaceTemplate
#     power_port_template = PowerPortTemplate
#     console_port_template = ConsolePortTemplate
#     module_bay_template = ModuleBayTemplate
#     site = Site
#     # TODO https://demo.netbox.dev/static/docs/release-notes/version-4.0/#breaking-changes
#     # device_role = DEPRICATED and removed in > 4.0.0 ()
#     device_role = DeviceRole

#     # TODO https://demo.netbox.dev/static/docs/release-notes/version-4.0/#breaking-changes
#     # device_role = DEPRICATED and removed in > 4.0.0 ()
#     top_level = ["manufacturer", "site", "device_role"]

#     def __init__(self, netbox, type='customer'):
#         self.netbox = netbox
#         self.type = type
#         logging.basicConfig(filename='device-type-sync.log', level=logging.DEBUG)
#         self.logger = logging.getLogger()
#         super().__init__(self)

#     def load(self):
#         manufacturers = self.netbox._get('/api/dcim/manufacturers/')
#         for man in manufacturers:
#             item = self.manufacturer(name=man['name'], display=man['display'], description=man['description'], slug = man['slug'], database_pk = man['id'], device_types = [])
#             self.add(item)

#         device_types = self.netbox._get('/api/dcim/device-types/')
#         for dt in device_types:
#             item = self.device_type(
#                 model = dt['model'],
#                 slug = dt['slug'],
#                 manufacturer_name = dt['manufacturer']['name'],
#                 part_number = dt['part_number'],
#                 is_full_depth = dt['is_full_depth'],
#                 airflow = dt['airflow'],
#                 weight = dt['weight'],
#                 weight_unit = dt['weight_unit'],
#                 description = dt['description'],
#                 comments = dt['comments'],
#                 database_pk = dt['id']
                
#             )
#             self.add(item)
#             manufacturer_name = dt['manufacturer']['name']
#             self.store._data['manufacturer'][manufacturer_name].add_child(item)

#         module_types = self.netbox._get('/api/dcim/module-types/')
#         for mt in module_types:
#             item = self.module_type(
#                 model = mt['model'],
#                 manufacturer_name = mt['manufacturer']['name'],
#                 part_number = mt['part_number'],
#                 weight = mt['weight'],
#                 weight_unit = mt['weight_unit'],
#                 description = mt['description'],
#                 comments = mt['comments'],
#                 database_pk = mt['id']
                
#             )
#             self.add(item)
#             manufacturer_name = mt['manufacturer']['name']
#             self.store._data['manufacturer'][manufacturer_name].add_child(item)
        
#         interface_templates = self.netbox._get('/api/dcim/interface-templates/')
#         for it in interface_templates:
#             item = self.interface_template(
#                 device_type = it['device_type']['model'] if it['device_type'] else '',
#                 module_type = it['module_type']['model'] if it['module_type'] else '',
#                 name = it['name'],
#                 interface_type = it['type'],
#                 enabled = it['enabled'],
#                 mgmt_only = it['mgmt_only'],
#                 description = it['description'],
#                 bridge = it['bridge'],
#                 poe_mode = it['poe_mode'],
#                 poe_type = it['poe_type'],
#                 rf_role = it['rf_role'],
#                 database_pk = it['id'],
#             )
#             self.add(item)
#             device_type_name = it['device_type']['model'] if it['device_type'] else ''
#             if device_type_name:
#                 self.store._data['device_type'][device_type_name].add_child(item)

#         power_port_templates = self.netbox._get('/api/dcim/power-port-templates/')
#         for pt in power_port_templates:
#             item = self.power_port_template(
#                 device_type = pt['device_type']['model'] if pt['device_type'] else '',
#                 module_type = pt['module_type']['model'] if pt['module_type'] else '',
#                 name = pt['name'],
#                 type = pt['type']['value'],
#                 maximum_draw = pt['maximum_draw'],
#                 allocated_draw = pt['allocated_draw'],
#                 description = pt['description'],
#                 database_pk = pt['id'],
#             )
#             self.add(item)
#             device_type_name = pt['device_type']['model'] if pt['device_type'] else ''
#             if device_type_name:
#                 self.store._data['device_type'][device_type_name].add_child(item)

#         console_port_templates = self.netbox._get('/api/dcim/console-port-templates/')
#         for ct in console_port_templates:
#             item = self.console_port_template(
#                 device_type = ct['device_type']['model'] if ct['device_type'] else '',
#                 module_type = ct['module_type']['model'] if ct['module_type'] else '',
#                 name = ct['name'],
#                 type = ct['type']['value'],
#                 description = ct['description'],
#                 database_pk = ct['id'],
#             )
#             self.add(item)
#             device_type_name = ct['device_type']['model'] if ct['device_type'] else ''
#             if device_type_name:
#                 self.store._data['device_type'][device_type_name].add_child(item)

#         module_bay_templates = self.netbox._get("/api/dcim/module-bay-templates/")
#         for mb in module_bay_templates:
#             item = self.module_bay_template(
#                 device_type = mb['device_type']['model'] if mb['device_type'] else '',
#                 name = mb['name'],
#                 label = mb['label'],
#                 position = mb['position'],
#                 description = mb['description'],
#                 database_pk = mb['id'],
#             )
#             self.add(item)
#             device_type_name = mb['device_type']['model'] if mb['device_type'] else ''
#             if device_type_name:
#                 self.store._data['device_type'][device_type_name].add_child(item)

#         sites = self.netbox._get("/api/dcim/sites/")
#         for site in sites:
#             item = self.site(
#                 name = site['name'],
#                 slug = site['slug'],
#                 status = site['status']['value'],
#                 comments = site['comments'],
#                 description = site['description'],
#                 database_pk = site['id'],
#             )
#             self.add(item)

#         device_roles = self.netbox._get("/api/dcim/device-roles/")
#         for dr in device_roles:
#             item = self.device_role(
#                 name = dr['name'],
#                 slug = dr['slug'],
#                 color = dr['color'],
#                 vm_role = dr['vm_role'],
#                 description = dr['description'],
#                 database_pk = dr['id'],
#             )
#             self.add(item)

#     def sync_complete(self, source: Adapter, diff: Diff, flags: DiffSyncFlags, logger):
#         ## TODO add your own logic to update the remote system now.
#         # The various parameters passed to this method are for your convenience in implementing more complex logic, and
#         # can be ignored if you do not need them.
#         #
#         # The default DiffSync.sync_complete() method does nothing, but it's always a good habit to call super():
#         manufacturers_to_add = []
#         manufacturers_to_change = []
#         device_type_to_add = []
#         device_type_to_change = []
#         module_bay_template_to_add = []
#         module_bay_template_to_change = []
#         module_type_to_add = []
#         module_type_to_change = []
#         interface_template_to_add = []
#         interface_template_to_change = []
#         power_port_template_to_add = []
#         power_port_template_to_change = []
#         console_port_template_to_add = []
#         console_port_template_to_change = []

#         sites_to_add = []
#         sites_to_change = []
#         device_roles_to_add = []
#         device_roles_to_change = []

#         def add_diff(diff):
#             if diff.action == 'create':
#                 if diff.type == 'manufacturer':
#                     manufacturers_to_add.append(dict(**diff.keys, **diff.source_attrs))
#                 elif diff.type == 'device_type':
#                     device_type = dict(**diff.keys, **diff.source_attrs)
#                     # device_type['manufacturer'] = self.store._data['manufacturer'][device_type['manufacturer_name']].database_pk
#                     # del(device_type['manufacturer_name'])
                    
                    
#                     # GET api returns a dict:
#                     #   "airflow": {
#                     #       "value": "passive",
#                     #       "label": "Passive"
#                     #   } OR
#                     #   "airflow": null
#                     # But the POST api only accepts:
#                     #   "airflow": "passive"
#                     #   OR
#                     #   "airflow": ""
#                     # 
#                     device_type['airflow'] = '' if device_type.get('airflow', {}) == None else device_type.get('airflow', {}).get('value', None)
#                     # Same as with airflow
#                     device_type['weight_unit'] = '' if device_type.get('weight_unit', {}) == None else device_type.get('weight_unit', {}).get('value', None)
#                     device_type_to_add.append(device_type)
#                 elif diff.type == 'module_type':
#                     module_type = dict(**diff.keys, **diff.source_attrs)
#                     module_type['manufacturer'] = self.store._data['manufacturer'][module_type['manufacturer_name']].database_pk
#                     del(module_type['manufacturer_name'])
#                     module_type['weight_unit'] = '' if module_type.get('weight_unit', {}) == None else module_type.get('weight_unit', {}).get('value', None)
#                     module_type_to_add.append(module_type)
#                 elif diff.type == 'interface_template':
#                     diff_object = dict(**diff.keys, **diff.source_attrs)
#                     diff_object['type'] = diff_object['interface_type']['value']
#                     del(diff_object['interface_type'])
#                     diff_object['bridge'] = None
#                     diff_object['poe_mode'] = '' if diff_object.get('poe_mode', {}) == None else diff_object.get('poe_mode', {}).get('value', None)
#                     diff_object['poe_type'] = '' if diff_object.get('poe_type', {}) == None else diff_object.get('poe_type', {}).get('value', None)
#                     diff_object['rf_role'] = '' if diff_object.get('rf_role', {}) == None else diff_object.get('rf_role', {}).get('value', None)
#                     interface_template_to_add.append(diff_object)
#                 elif diff.type == 'power_port_template':
#                     diff_object = dict(**diff.keys, **diff.source_attrs)
#                     power_port_template_to_add.append(diff_object)
#                 elif diff.type == 'console_port_template':
#                     diff_object = dict(**diff.keys, **diff.source_attrs)
#                     if diff_object['device_type']:
#                         diff_object['device_type'] = self.store._data['device_type'][diff_object['device_type']].database_pk
#                     else:
#                         diff_object['device_type'] = None
#                     if diff_object['module_type']:
#                         diff_object['module_type'] = self.store._data['module_type'][diff_object['module_type']].database_pk
#                     else:
#                         diff_object['module_type'] = None
#                     console_port_template_to_add.append(diff_object)
#                 elif diff.type == 'module_bay_template':
#                     diff_object = dict(**diff.keys, **diff.source_attrs)
#                     if diff_object['device_type']:
#                         diff_object['device_type'] = self.store._data['device_type'][diff_object['device_type']].database_pk
#                     module_bay_template_to_add.append(diff_object)
#                 elif diff.type == 'site':
#                     diff_object = dict(**diff.keys, **diff.source_attrs)
#                     sites_to_add.append(diff_object)
#                 # TODO https://demo.netbox.dev/static/docs/release-notes/version-4.0/#breaking-changes
#                 # device_role = DEPRICATED and removed in > 4.0.0
#                 elif diff.type == 'device_role':
#                     diff_object = dict(**diff.keys, **diff.source_attrs)
#                     device_roles_to_add.append(diff_object)
#             elif diff.action == 'update':
#                 # Issue reported in https://github.com/networktocode/diffsync/issues/259
#                 pk = self.store._data[diff.type][diff.name].database_pk
#                 if diff.type == 'manufacturer':
#                     manufacturers_to_change.append(dict(**diff.source_attrs, **{'id': pk}))
#                 elif diff.type == 'device_type':
#                     device_type = dict(**diff.source_attrs, **{'id': pk})
#                     device_type['airflow'] = '' if device_type.get('airflow', {}) == None else device_type.get('airflow', {}).get('value', None)
#                     # Same as with airflow
#                     device_type['weight_unit'] = '' if device_type.get('weight_unit', {}) == None else device_type.get('weight_unit', {}).get('value', None)
#                     device_type['manufacturer'] = self.store._data['manufacturer'][device_type['manufacturer_name']].database_pk
#                     del(device_type['manufacturer_name'])
#                     device_type_to_change.append(device_type)
#                 elif diff.type == 'module_type':
#                     module_type = dict(**diff.source_attrs, **{'id': pk})
#                     module_type['weight_unit'] = '' if module_type.get('weight_unit', {}) == None else module_type.get('weight_unit', {}).get('value', None)
#                     module_type['manufacturer'] = self.store._data['manufacturer'][module_type['manufacturer_name']].database_pk
#                     del(module_type['manufacturer_name'])
#                     module_type_to_change.append(module_type)
#                 elif diff.type == 'interface_template':
#                     interface_template = dict(**diff.keys, **diff.source_attrs, **{'id': pk})
#                     if interface_template['device_type']:
#                         interface_template['device_type'] = self.store._data['device_type'][interface_template['device_type']].database_pk
#                     interface_template['module_type'] = None if interface_template['module_type'] == '' else interface_template['module_type']
#                     interface_template['bridge'] = None
#                     interface_template['poe_mode'] = '' if interface_template.get('poe_mode', {}) == None else interface_template.get('poe_mode', {}).get('value', None)
#                     interface_template['poe_type'] = '' if interface_template.get('poe_type', {}) == None else interface_template.get('poe_type', {}).get('value', None)
#                     interface_template['rf_role'] = '' if interface_template.get('rf_role', {}) == None else interface_template.get('rf_role', {}).get('value', None)
#                     interface_template_to_change.append(interface_template)
#                 elif diff.type == 'power_port_template':
#                     diff_object = dict(**diff.keys, **diff.source_attrs, **{'id': pk})
#                     if diff_object['device_type']:
#                         diff_object['device_type'] = self.store._data['device_type'][diff_object['device_type']].database_pk
#                     else:
#                         diff_object['device_type'] = None
#                     if diff_object['module_type']:
#                         diff_object['module_type'] = self.store._data['module_type'][diff_object['module_type']].database_pk
#                     else:
#                         diff_object['module_type'] = None
#                     power_port_template_to_change.append(diff_object)
#                 elif diff.type == 'console_port_template':
#                     diff_object = dict(**diff.keys, **diff.source_attrs, **{'id': pk})
#                     if diff_object['device_type']:
#                         diff_object['device_type'] = self.store._data['device_type'][diff_object['device_type']].database_pk
#                     else:
#                         diff_object['device_type'] = None
#                     if diff_object['module_type']:
#                         diff_object['module_type'] = self.store._data['module_type'][diff_object['module_type']].database_pk
#                     else:
#                         diff_object['module_type'] = None
#                     console_port_template_to_change.append(diff_object)
#                 elif diff.type == 'module_bay_template':
#                     diff_object = dict(**diff.keys, **diff.source_attrs, **{'id': pk})
#                     if diff_object['device_type']:
#                         diff_object['device_type'] = self.store._data['device_type'][diff_object['device_type']].database_pk
#                     module_bay_template_to_change.append(diff_object)
#                 elif diff.type == 'site':
#                     diff_object = dict(**diff.keys, **diff.source_attrs, **{'id': pk})
#                     sites_to_change.append(diff_object)
#                 # TODO https://demo.netbox.dev/static/docs/release-notes/version-4.0/#breaking-changes
#                 # device_role = DEPRICATED and removed in > 4.0.0
#                 elif diff.type == 'device_role':
#                     diff_object = dict(**diff.keys, **diff.source_attrs, **{'id': pk})
#                     device_roles_to_change.append(diff_object)


#         for diff1 in diff.get_children():
#             add_diff(diff1)
#             for child in diff1.child_diff.get_children():
#                 add_diff(child)
#                 for child2 in child.child_diff.get_children():
#                     add_diff(child2)
            

#         manufacturers = self.netbox._post("/api/dcim/manufacturers/", manufacturers_to_add, verify=True)
#         self.netbox._patch("/api/dcim/manufacturers/", manufacturers_to_change)

#         for manufacturer in manufacturers:
#             self.store._data['manufacturer'][manufacturer['name']].database_pk=manufacturer['id']

#         for device_type in device_type_to_add:
#             device_type['manufacturer'] = self.store._data['manufacturer'][device_type['manufacturer_name']].database_pk
#             del device_type['manufacturer_name']

#         for module_type in module_type_to_add:
#             module_type['manufacturer'] = self.store._data['manufacturer'][module_type['manufacturer_name']].database_pk
#             del module_type['manufacturer_name']

#         device_types = self.netbox._post("/api/dcim/device-types/", device_type_to_add, verify=True)
#         self.netbox._patch("/api/dcim/device-types/", device_type_to_change)

#         module_types = self.netbox._post("/api/dcim/module-types/", module_type_to_add, verify=True)
#         self.netbox._patch("/api/dcim/module-types/", module_type_to_change)

#         for device_type in device_types:
#             self.store._data['device_type'][device_type['model']].database_pk=device_type['id']

#         for module_type in module_types:
#             self.store._data['module_type'][module_type['model']].database_pk=module_type['id']

#         for template in interface_template_to_add:
#             if template['device_type']:
#                 if not isinstance(template['device_type'], int):
#                     template['device_type'] = self.store._data['device_type'][template['device_type']].database_pk
#             else:
#                 template['device_type'] = None
#             if template['module_type']:
#                 if not isinstance(template['module_type'], int):
#                     template['module_type'] = self.store._data['module_type'][template['module_type']].database_pk
#             else:
#                 template['module_type'] = None

#         self.netbox._post("/api/dcim/interface-templates/", interface_template_to_add, verify=True)
#         self.netbox._patch("/api/dcim/interface-templates/", interface_template_to_change)

#         for template in power_port_template_to_add:
#             if template['device_type']:
#                 if not isinstance(template['device_type'], int):
#                     template['device_type'] = self.store._data['device_type'][template['device_type']].database_pk
#             else:
#                 template['device_type'] = None
#             if template['module_type']:
#                 if not isinstance(template['module_type'], int):
#                     template['module_type'] = self.store._data['module_type'][template['module_type']].database_pk
#             else:
#                 template['module_type'] = None

#         self.netbox._post("/api/dcim/power-port-templates/", power_port_template_to_add, verify=True)
#         self.netbox._patch("/api/dcim/power-port-templates/", power_port_template_to_change)

#         for template in console_port_template_to_add:
#             if template['device_type']:
#                 if not isinstance(template['device_type'], int):
#                     template['device_type'] = self.store._data['device_type'][template['device_type']].database_pk
#             else:
#                 template['device_type'] = None
#             if template['module_type']:
#                 if not isinstance(template['module_type'], int):
#                     template['module_type'] = self.store._data['module_type'][template['module_type']].database_pk
#             else:
#                 template['module_type'] = None

#         self.netbox._post("/api/dcim/console-port-templates/", console_port_template_to_add, verify=True)
#         self.netbox._patch("/api/dcim/console-port-templates/", console_port_template_to_change)

#         self.netbox._post("/api/dcim/module-bay-templates/", module_bay_template_to_add, verify=True)
#         self.netbox._patch("/api/dcim/module-bay-templates/", module_bay_template_to_change)

#         self.netbox._post("/api/dcim/sites/", sites_to_add, verify=True)
#         self.netbox._patch("/api/dcim/sites/", sites_to_change)

#         self.netbox._post("/api/dcim/device-roles/", device_roles_to_add, verify=True)
#         self.netbox._patch("/api/dcim/device-roles/", device_roles_to_change)

#         super().sync_complete(source, diff, flags, logger)


class NetboxDeviceAdapter(Adapter):

    device = Device
    virtual_chassis = VirtualChassis
    interface = Interface
    ip = IPAddress
    manufacturer = Manufacturer
    device_type = DeviceType
    module_type = ModuleType
    interface_template = InterfaceTemplate
    power_port_template = PowerPortTemplate
    power_outlet_template = PowerOutletTemplate
    console_port_template = ConsolePortTemplate
    console_server_port_template = ConsoleServerPortTemplate
    rear_port_template = RearPortTemplate
    front_port_template = FrontPortTemplate
    module_bay_template = ModuleBayTemplate
    site = Site
    device_role = DeviceRole
    tag = Tag

    
    top_level = ["virtual_chassis","device", "ip", "manufacturer", "site", "device_role", "tag"]

    def __init__(self):
        logging.basicConfig(filename='device-sync.log', level=logging.DEBUG)
        self.logger = logging.getLogger('netbox-adapter')
        super().__init__(self)

    def convert_components_parent_to_ids(self, components):
        for template in components:
            if template['device_type']:
                if not isinstance(template['device_type'], int):
                    template['device_type'] = self.store._data['device_type'][template['device_type']].database_pk
            else:
                template['device_type'] = None
            if template['module_type']:
                if not isinstance(template['module_type'], int):
                    template['module_type'] = self.store._data['module_type'][template['module_type']].database_pk
            else:
                template['module_type'] = None
        return components

    def load(self):
        tags = self.netbox._get('/api/extras/tags/')
        for tag in tags:
            item = self.tag(
                name = tag['name'],
                slug = tag['slug'],
                color = tag['color'],
                weight = tag['weight'],
                object_types = tag['object_types'],
                description = tag['description'],
                database_pk = tag['id'],
            )
            self.add(item)

        sites = self.netbox._get('/api/dcim/sites/')
        for site in sites:
            item = self.site(
                name=site['name'], 
                description=site['description'], 
                slug = site['slug'], 
                status = site['status']['value'],
                database_pk = site['id'], 
                comments = site['comments'])
            self.add(item)

        ###### CHANGE INPUT ########
        device_roles = self.netbox._get('/api/dcim/device-roles/')
        for device_role in device_roles:
            item = self.device_role(
                name = device_role['name'],
                description = device_role['description'],
                slug=device_role['slug'],
                color=device_role['color'],
                vm_role=device_role['vm_role'],
                database_pk=device_role['id']
            )
            self.add(item)

        manufacturers = self.netbox._get('/api/dcim/manufacturers/')
        for man in manufacturers:
            item = self.manufacturer(
                name=man['name'], 
                display=man['display'], 
                description=man['description'], 
                slug = man['slug'], 
                database_pk = man['id'], 
                device_types = [])
            self.add(item)

        device_types = self.netbox._get('/api/dcim/device-types/')
        for dt in device_types:
            item = self.device_type(
                model = dt['model'],
                slug = dt['slug'],
                manufacturer_name = dt['manufacturer']['name'],
                part_number = dt['part_number'],
                is_full_depth = dt['is_full_depth'],
                airflow = dt['airflow'].get('value', '') if dt['airflow'] else '',
                weight = dt['weight'],
                weight_unit = dt['weight_unit'].get('value', '') if dt['weight_unit'] else '',
                description = dt['description'],
                comments = dt['comments'],
                database_pk = dt['id']
                
            )
            self.add(item)
            manufacturer_name = dt['manufacturer']['name']
            self.store._data['manufacturer'][manufacturer_name].add_child(item)

        module_types = self.netbox._get('/api/dcim/module-types/')
        for mt in module_types:
            item = self.module_type(
                model = mt['model'],
                manufacturer_name = mt['manufacturer']['name'],
                part_number = mt['part_number'],
                weight = mt['weight'],
                weight_unit = mt['weight_unit'].get('value', '') if mt['weight_unit'] else '',
                description = mt['description'],
                comments = mt['comments'],
                database_pk = mt['id']
                
            )
            self.add(item)
            manufacturer_name = mt['manufacturer']['name']
            self.store._data['manufacturer'][manufacturer_name].add_child(item)
        
        interface_templates = self.netbox._get('/api/dcim/interface-templates/')
        for it in interface_templates:
            item = self.interface_template(
                device_type = it['device_type']['model'] if it['device_type'] else '',
                module_type = it['module_type']['model'] if it['module_type'] else '',
                name = convert_interface_name(it['name']),
                interface_type = it['type']['value'],
                enabled = it['enabled'],
                mgmt_only = it['mgmt_only'],
                description = it['description'],
                bridge = it['bridge'],
                poe_mode = it['poe_mode'].get('value', '') if it['poe_mode'] else '',
                poe_type = it['poe_type'].get('value', '') if it['poe_type'] else '',
                rf_role = it['rf_role'].get('value', '') if it['rf_role'] else '',
                database_pk = it['id'],
            )
            self.add(item)
            device_type_name = it['device_type']['model'] if it['device_type'] else ''
            if device_type_name:
                self.store._data['device_type'][device_type_name].add_child(item)

        power_port_templates = self.netbox._get('/api/dcim/power-port-templates/')
        for pt in power_port_templates:
            item = self.power_port_template(
                device_type = pt['device_type']['model'] if pt['device_type'] else '',
                module_type = pt['module_type']['model'] if pt['module_type'] else '',
                name = pt['name'],
                type = pt['type']['value'],
                maximum_draw = pt['maximum_draw'],
                allocated_draw = pt['allocated_draw'],
                description = pt['description'],
                database_pk = pt['id'],
            )
            self.add(item)
            device_type_name = pt['device_type']['model'] if pt['device_type'] else ''
            if device_type_name:
                self.store._data['device_type'][device_type_name].add_child(item)

        power_outlet_templates = self.netbox._get('/api/dcim/power-outlet-templates/')
        for pt in power_outlet_templates:
            item = self.power_outlet_template(
                device_type = pt['device_type']['model'] if pt['device_type'] else '',
                module_type = pt['module_type']['model'] if pt['module_type'] else '',
                name = pt['name'],
                type = pt['type']['value'],
                label = pt['label'],
                power_port = pt['power_port']['name'] if pt['power_port'] else '',
                feed_leg = pt['feed_leg']['value'] if pt['feed_leg'] else '',
                description = pt['description'],
                database_pk = pt['id'],
            )
            self.add(item)
            device_type_name = pt['device_type']['model'] if pt['device_type'] else ''
            if device_type_name:
                self.store._data['device_type'][device_type_name].add_child(item)

        console_port_templates = self.netbox._get('/api/dcim/console-port-templates/')
        for ct in console_port_templates:
            item = self.console_port_template(
                device_type = ct['device_type']['model'] if ct['device_type'] else '',
                module_type = ct['module_type']['model'] if ct['module_type'] else '',
                name = ct['name'],
                type = ct['type']['value'],
                label = ct['label'],
                description = ct['description'],
                database_pk = ct['id'],
            )
            self.add(item)
            device_type_name = ct['device_type']['model'] if ct['device_type'] else ''
            if device_type_name:
                self.store._data['device_type'][device_type_name].add_child(item)

        console_server_port_templates = self.netbox._get('/api/dcim/console-server-port-templates/')
        for ct in console_server_port_templates:
            item = self.console_server_port_template(
                device_type = ct['device_type']['model'] if ct['device_type'] else '',
                module_type = ct['module_type']['model'] if ct['module_type'] else '',
                name = ct['name'],
                type = ct['type']['value'],
                label = ct['label'],
                description = ct['description'],
                database_pk = ct['id'],
            )
            self.add(item)
            device_type_name = ct['device_type']['model'] if ct['device_type'] else ''
            if device_type_name:
                self.store._data['device_type'][device_type_name].add_child(item)

        rear_port_templates = self.netbox._get('/api/dcim/rear-port-templates/')
        for t in rear_port_templates:
            item = self.rear_port_template(
                device_type = t['device_type']['model'] if t['device_type'] else '',
                module_type = t['module_type']['model'] if t['module_type'] else '',
                name = t['name'],
                type = t['type']['value'],
                label = t['label'],
                color = t['color'],
                positions = t['positions'],
                description = t['description'],
                database_pk = t['id'],
            )
            self.add(item)
            device_type_name = t['device_type']['model'] if t['device_type'] else ''
            if device_type_name:
                self.store._data['device_type'][device_type_name].add_child(item)

        front_port_templates = self.netbox._get('/api/dcim/front-port-templates/')
        for t in front_port_templates:
            item = self.front_port_template(
                device_type = t['device_type']['model'] if t['device_type'] else '',
                module_type = t['module_type']['model'] if t['module_type'] else '',
                name = t['name'],
                type = t['type']['value'],
                label = t['label'],
                color = t['color'],
                rear_port = t['rear_port']['name'],
                rear_port_positions = t['rear_port_positions'],
                description = t['description'],
                database_pk = t['id'],
            )
            self.add(item)
            device_type_name = t['device_type']['model'] if t['device_type'] else ''
            if device_type_name:
                self.store._data['device_type'][device_type_name].add_child(item)

        module_bay_templates = self.netbox._get("/api/dcim/module-bay-templates/")
        for mb in module_bay_templates:
            item = self.module_bay_template(
                device_type = mb['device_type']['model'] if mb['device_type'] else '',
                name = mb['name'],
                label = mb['label'],
                position = mb['position'],
                description = mb['description'],
                database_pk = mb['id'],
            )
            self.add(item)
            device_type_name = mb['device_type']['model'] if mb['device_type'] else ''
            if device_type_name:
                self.store._data['device_type'][device_type_name].add_child(item)
        # Add virtual chassis to compare db
        virtual_chassis = self.netbox.get_all_virtual_chassis()
        for vc in virtual_chassis:
            item = self.virtual_chassis(
                name=vc.get('name').lower(),
                domain = vc.get('domain', ''),
                description=vc.get('description', ''),
                database_pk=vc['id'],
            )
            member_devices = vc.get('members', [])
            self.add(item)

        # Add devices to compare db
        devices = self.netbox.get_all_devices()
        for device in devices:
            try:
                item = self.device(
                    hostname=device['name'].lower(), 
                    serial=device['serial'],
                    mgmt_ip=device.get('primary_ip', {}).get('address', '') if device.get('primary_ip', {}) else '',
                    device_type=device['device_type']['model'], 
                    status = device['status']['value'],
                    virtual_chassis = device.get('virtual_chassis', {}).get('name') if device.get('virtual_chassis') else '',
                    vc_position = device.get('vc_position'),
                    database_pk = device['id'],
                )
                self.add(item)
            except Exception as e:
                print(f"could not add: {device['name']} -> {e}")
                pass

        # Add interfaces to compare db
        self.interfaces = {}
        interfaces = self.netbox.get_all_interfaces()
        for interface in interfaces:
            try:
                interface_item = self.interface(
                    hostname=interface.get('device', {}).get('name').lower(),
                    interface=convert_interface_name(interface.get('name')),
                    database_pk=interface.get('id'),
                )
                self.add(interface_item)
                parent_device_id = interface.get('device', {}).get('name').lower()
                self.store._data['device'][parent_device_id].add_child(interface_item)
            except Exception as e:
                print(f"could not add: {interface_item.hostname}:{interface_item.interface} -> {e}")
                pass


        # Add ips to compare db
        ips = self.netbox.get_all_ips()
        for ip in ips:
            try:
                if ip.get('assigned_object_type', '') == 'dcim.interface':
                    assigned_object_device_name = ip.get('assigned_object', {}).get('device', {}).get('name', '').lower()
                    assigned_object_name = ip.get('assigned_object', {}).get('name', '')

                    parent_interface_id = f'{assigned_object_device_name}__{assigned_object_name}'
                else:
                    parent_interface_id = None
                ip_item = self.ip(
                    ip = expand_ipv6(ip.get('address').split('/')[0]),
                    subnet= ip.get('address').split('/')[1],
                    database_pk=ip.get('id'),
                    #TODO Add logic to find parent
                    parent=parent_interface_id,
                )
                self.add(ip_item)
            except Exception as e:
                print(f"could not add: {ip_item.ip}/{ip_item.subnet} -> {e}")
                pass

    def sync_complete(self, source: Adapter, diff: Diff, flags: DiffSyncFlags, logger):
        
        tags_to_add = []
        tags_to_change = []

        sites_to_add = []
        sites_to_change = []

        device_roles_to_add = []
        device_roles_to_change = []

        manufacturers_to_add = []
        manufacturers_to_change = []

        device_types_to_add = []
        device_types_to_change = []

        module_bay_template_to_add = []
        module_bay_template_to_change = []

        module_type_to_add = []
        module_type_to_change = []

        interface_template_to_add = []
        interface_template_to_change = []

        power_port_template_to_add = []
        power_port_template_to_change = []

        power_outlet_template_to_add = []
        power_outlet_template_to_change = []

        console_port_template_to_add = []
        console_port_template_to_change = []

        console_server_port_template_to_add = []
        console_server_port_template_to_change = []

        rear_port_template_to_add = []
        rear_port_template_to_change = []

        front_port_template_to_add = []
        front_port_template_to_change = []

        devices_to_add = []
        devices_to_change = []

        vcs_to_add = []
        unique_vcs = set()
        vcs_to_change = []


        interfaces_to_add = []
        interfaces_to_change = []

        ips_to_add = []
        ips_to_change = []

        def prep_device_type_for_netbox(device_type):      
            # GET api returns a dict:
            #   "airflow": {
            #       "value": "passive",
            #       "label": "Passive"
            #   } OR
            #   "airflow": null
            # But the POST api only accepts:
            #   "airflow": "passive"
            #   OR
            #   "airflow": ""
            # 
            if not isinstance(device_type['airflow'], str):
                device_type['airflow'] = '' if device_type.get('airflow', {}) == None else device_type.get('airflow', {}).get('value', '')
            # Same as with airflow
            if not isinstance(device_type['weight_unit'], str):
                device_type['weight_unit'] = '' if device_type.get('weight_unit', {}) == None else device_type.get('weight_unit', {}).get('value', '')
            return device_type
        
        def prep_module_type_for_netbox(module_type):
            module_type['manufacturer'] = self.store._data['manufacturer'][module_type['manufacturer_name']].database_pk
            del(module_type['manufacturer_name'])
            module_type['weight_unit'] = '' if module_type.get('weight_unit', {}) == None else module_type.get('weight_unit', {}).get('value', '')
            return module_type

        def prep_interface_template_for_netbox(interface_template):
            if not isinstance(interface_template['interface_type'], str):
                interface_template['type'] = interface_template['interface_type']['value']
            else:
                interface_template['type'] = interface_template['interface_type']
            del(interface_template['interface_type'])
            return interface_template

        def prep_power_port_template_for_netbox(power_port_template):
            return power_port_template

        def prep_console_port_template_for_netbox(console_port_template):
            return console_port_template

        def prep_module_bay_template_for_netbox(module_bay_template):
            if module_bay_template['device_type']:
                module_bay_template['device_type'] = self.store._data['device_type'][module_bay_template['device_type']].database_pk
            return module_bay_template

        def prep_device_for_netbox(device):
            device['device_type'] = {'model': device['device_type']}
            device['name'] = device['hostname']
            return device

        def prep_virtual_chassis_for_netbox(virtual_chassis):
            return virtual_chassis

        def prep_interface_for_netbox(interface):
            interface['name'] = interface['interface']
            return interface

        def prep_ip_for_netbox(ip):
            ip['address'] = ip['ip'] +"/"+ ip['subnet']
            ip['status'] = 'active'
            return ip

        def procces_layer(diff):
            for child_diff in diff.get_children():
                if child_diff.action == 'create':
                    item = dict(**child_diff.keys, **child_diff.source_attrs)
                    if child_diff.type == 'site':
                        sites_to_add.append(item)
                    elif child_diff.type == 'device_role':
                        device_roles_to_add.append(item)
                    elif child_diff.type == 'manufacturer':
                        manufacturers_to_add.append(item)
                    elif child_diff.type == 'device_type':
                        item = prep_device_type_for_netbox(item)
                        device_types_to_add.append(item)
                    elif child_diff.type == 'module_type':
                        item = prep_module_type_for_netbox(item)
                        module_type_to_add.append(item)
                    elif child_diff.type == 'interface_template':
                        item = prep_interface_template_for_netbox(item)
                        interface_template_to_add.append(item)
                    elif child_diff.type == 'power_port_template':
                        power_port_template_to_add.append(item)
                    elif child_diff.type == 'power_outlet_template':
                        power_outlet_template_to_add.append(item)
                    elif child_diff.type == 'console_port_template':
                        console_port_template_to_add.append(item)
                    elif child_diff.type == 'console_server_port_template':
                        console_server_port_template_to_add.append(item)
                    elif child_diff.type == 'front_port_template':
                        front_port_template_to_add.append(item)
                    elif child_diff.type == 'rear_port_template':
                        rear_port_template_to_add.append(item)
                    elif child_diff.type == 'module_bay_template':
                        item = prep_module_bay_template_for_netbox(item)
                        module_bay_template_to_add.append(item)
                    elif child_diff.type == 'device':
                        item = prep_device_for_netbox(item)
                        item['site'] = {'name':'Unknown'}
                        item['role'] = {'name':'Unknown'}
                        if not item['virtual_chassis']:
                            del item['virtual_chassis']
                        else:
                            unique_vcs.add(item['virtual_chassis'])
                        devices_to_add.append(item)
                    elif child_diff.type == 'virtual_chassis':
                        vcs_to_add.append(item)
                    elif child_diff.type == 'interface':
                        item = prep_interface_for_netbox(item)
                        item['type'] = 'virtual'
                        interfaces_to_add.append(item)
                    elif child_diff.type == 'ip':
                        item = prep_ip_for_netbox(item)
                        ips_to_add.append(item)
                    elif child_diff.type == 'tag':
                        tags_to_add.append(item)
                elif child_diff.action == 'update':
                    # Issue reported in https://github.com/networktocode/diffsync/issues/259
                    pk = self.store._data[child_diff.type][child_diff.name].database_pk
                    item = dict(**child_diff.keys, **child_diff.source_attrs, **{'id': pk})
                    if child_diff.type == 'device':
                        item = prep_device_for_netbox(item)
                        if not item['virtual_chassis']:
                            del item['virtual_chassis']
                        devices_to_change.append(item)
                    elif child_diff.type == 'device_type':
                        item = prep_device_type_for_netbox(item)
                        device_types_to_change.append(item)
                    elif child_diff.type == 'module_type':
                        item = prep_module_type_for_netbox(item)
                        module_type_to_change.append(item)
                    elif child_diff.type == 'interface_template':
                        item = prep_interface_template_for_netbox(item)
                        interface_template_to_change.append(item)
                    elif child_diff.type == 'power_port_template':
                        power_port_template_to_change.append(item)
                    elif child_diff.type == 'power_outlet_template':
                        power_outlet_template_to_change.append(item)
                    elif child_diff.type == 'console_port_template':
                        console_port_template_to_change.append(item)
                    elif child_diff.type == 'console_server_port_template':
                        console_server_port_template_to_change.append(item)
                    elif child_diff.type == 'front_port_template':
                        front_port_template_to_change.append(item)
                    elif child_diff.type == 'rear_port_template':
                        rear_port_template_to_change.append(item)
                    elif child_diff.type == 'module_bay_template':
                        item = prep_module_bay_template_for_netbox(item)
                        module_bay_template_to_change.append(item)
                    elif child_diff.type == 'virtual_chassis':
                        vcs_to_change.append(item)
                    elif child_diff.type == 'interface':
                        item = prep_interface_for_netbox(item)
                        interfaces_to_change.append(item)
                    elif child_diff.type == 'ip':
                        # interface_name = source.store._data['ip'][item['ip']+"__"+item['subnet']].parent
                        item['parent'] = source.store._data['ip'][item['ip']+"__"+item['subnet']].parent
                        # interface = source.store._data['interface'][interface_name]
                        item['assigned_object_type'] = "dcim.interface"
                        # item['assigned_object_id'] = interface.database_pk
                        ips_to_change.append(item)
                    elif child_diff.type == 'tag':
                        tags_to_change.append(item)
                procces_layer(child_diff) # Recursive function to process all diff children
        procces_layer(diff)

        ##########
        # Tags
        ##########
        if len(tags_to_add) > 0:
            created_tags = self.netbox._post("/api/extras/tags/", tags_to_add, verify=True)
            for tag in created_tags:
                self.store._data['tag'][tag['name']].database_pk = tag['id']
        self.netbox._patch("/api/extras/tags/", tags_to_change)

        ##########
        # Sites
        ##########
        self.netbox._post("/api/dcim/sites/", sites_to_add, verify=True)
        self.netbox._patch("/api/dcim/sites/", sites_to_change)


        ##########
        # Device roles
        ##########
        self.netbox._post("/api/dcim/device-roles/", device_roles_to_add, verify=True)
        self.netbox._patch("/api/dcim/device-roles/", device_roles_to_change)


        ##########
        # Manufacturers
        ##########
        manufacturers = self.netbox._post("/api/dcim/manufacturers/", manufacturers_to_add, verify=True)
        self.netbox._patch("/api/dcim/manufacturers/", manufacturers_to_change)

        for manufacturer in manufacturers:
            self.store._data['manufacturer'][manufacturer['name']].database_pk=manufacturer['id']


        ##########
        # Device types
        ##########
        for device_type in device_types_to_add:
            device_type['manufacturer'] = self.store._data['manufacturer'][device_type['manufacturer_name']].database_pk
            del device_type['manufacturer_name']
        device_types = self.netbox._post("/api/dcim/device-types/", device_types_to_add, verify=True)
        self.netbox._patch("/api/dcim/device-types/", device_types_to_change)

        for device_type in device_types:
            self.store._data['device_type'][device_type['model']].database_pk=device_type['id']


        ##########
        # Module types
        ##########
        for module_type in module_type_to_add:
            module_type['manufacturer'] = self.store._data['manufacturer'][module_type['manufacturer_name']].database_pk
            del module_type['manufacturer_name']
        module_types = self.netbox._post("/api/dcim/module-types/", module_type_to_add, verify=True)
        self.netbox._patch("/api/dcim/module-types/", module_type_to_change)

        for module_type in module_types:
            self.store._data['module_type'][module_type['model']].database_pk=module_type['id']


        ##########
        # Interface templates
        ##########
        interface_template_to_add = self.convert_components_parent_to_ids(interface_template_to_add)
        interface_template_to_change = self.convert_components_parent_to_ids(interface_template_to_change)

        self.netbox._post("/api/dcim/interface-templates/", interface_template_to_add, verify=True)
        self.netbox._patch("/api/dcim/interface-templates/", interface_template_to_change)


        ##########
        # Power port templates
        ##########
        power_port_template_to_add = self.convert_components_parent_to_ids(power_port_template_to_add)
        power_port_template_to_change = self.convert_components_parent_to_ids(power_port_template_to_change)

        for power_port in self.netbox._post("/api/dcim/power-port-templates/", power_port_template_to_add, verify=True):
            self.store._data['power_port_template'][f'{power_port['device_type']['model'] if power_port['device_type'] else ''}__{power_port['module_type']['model'] if power_port['module_type'] else ''}__{power_port['name']}'].database_pk = power_port['id']
        self.netbox._patch("/api/dcim/power-port-templates/", power_port_template_to_change)


        ##########
        # Power outlet templates
        ##########
        for component in power_outlet_template_to_add:
            power_port_id = f'{component['device_type'] if component['device_type'] else ''}__{component['module_type'] if component['module_type'] else ''}__{component['power_port']}'
            print(power_port_id)
            pprint(self.store._data['power_port_template'])
            component['power_port'] = self.store._data['power_port_template'][power_port_id].database_pk
        power_outlet_template_to_add = self.convert_components_parent_to_ids(power_outlet_template_to_add)
        pprint(power_outlet_template_to_add)
        
        for component in power_outlet_template_to_change:
            component['power_port'] = self.store._data['power_port_template'][f'{component['device_type'] if component['device_type'] else ''}__{component['module_type']['model'] if component['module_type'] else ''}__{component['power_port']}'].database_pk
        power_outlet_template_to_change = self.convert_components_parent_to_ids(power_outlet_template_to_change)
        
        self.netbox._post("/api/dcim/power-outlet-templates/", power_outlet_template_to_add, verify=True)
        self.netbox._patch("/api/dcim/power-outlet-templates/", power_outlet_template_to_change)


        ##########
        # Console port templates
        ##########
        console_port_template_to_add = self.convert_components_parent_to_ids(console_port_template_to_add)
        console_port_template_to_change = self.convert_components_parent_to_ids(console_port_template_to_change)

        self.netbox._post("/api/dcim/console-port-templates/", console_port_template_to_add, verify=True)
        self.netbox._patch("/api/dcim/console-port-templates/", console_port_template_to_change)


        ##########
        # Console server port templates
        ##########
        console_server_port_template_to_add = self.convert_components_parent_to_ids(console_server_port_template_to_add)
        console_server_port_template_to_change = self.convert_components_parent_to_ids(console_server_port_template_to_change)

        self.netbox._post("/api/dcim/console-server-port-templates/", console_server_port_template_to_add, verify=True)
        self.netbox._patch("/api/dcim/console-server-port-templates/", console_server_port_template_to_change)


        ##########
        # Rear port templates
        ##########
        
        rear_port_template_to_add = self.convert_components_parent_to_ids(rear_port_template_to_add)
        
       

        rear_port_template_to_change = self.convert_components_parent_to_ids(rear_port_template_to_change)
        
        for rear_port in self.netbox._post("/api/dcim/rear-port-templates/", rear_port_template_to_add, verify=True):
            self.store._data['rear_port_template'][f'{rear_port['device_type']['model'] if rear_port['device_type'] else ''}__{rear_port['module_type']['model'] if rear_port['module_type'] else ''}__{rear_port['name']}'].database_pk = rear_port['id']
        self.netbox._patch("/api/dcim/rear-port-templates/", rear_port_template_to_change)


        ##########
        # Front port templates
        ##########
        for component in front_port_template_to_add:
            component['rear_port'] = self.store._data['rear_port_template'][f'{component['device_type']}__{component['module_type']}__{component['rear_port']}'].database_pk

        front_port_template_to_add = self.convert_components_parent_to_ids(front_port_template_to_add)

        for component in front_port_template_to_change:
            component['rear_port'] = self.store._data['rear_port_template'][f'{component['device_type']}__{component['module_type']}__{component['rear_port']}'].database_pk

        front_port_template_to_change = self.convert_components_parent_to_ids(front_port_template_to_change)

        for front_port in self.netbox._post("/api/dcim/front-port-templates/", front_port_template_to_add, verify=True):
            self.store._data['front_port_template'][f'{front_port['device_type']['model'] if front_port['device_type'] else ''}__{front_port['module_type']['model'] if front_port['module_type'] else ''}__{front_port['name']}'].database_pk = front_port['id']
        
        self.netbox._patch("/api/dcim/front-port-templates/", front_port_template_to_change)

        
        ##########
        # Module bay templates
        ##########
        self.netbox._post("/api/dcim/module-bay-templates/", module_bay_template_to_add, verify=True)
        self.netbox._patch("/api/dcim/module-bay-templates/", module_bay_template_to_change)


        loaded_from_libre_tag_id = self.store._data['tag']['Loaded from Librenms'].database_pk

        ##########
        # Virtual chassis's
        ##########
        self.logger.debug(f"Adding virtual chassis's: {vcs_to_add}")
        for vc in vcs_to_add:
            vc['tags'] = [loaded_from_libre_tag_id]
        if len(vcs_to_add) > 0:
            added_vcs = self.netbox._post("/api/dcim/virtual-chassis/", vcs_to_add, verify=True)
            for vc in added_vcs:
                self.store._data['virtual_chassis'][vc['name']].database_pk=vc['id']
        for vc in vcs_to_change:
            vc['tags'] = [loaded_from_libre_tag_id]
        self.netbox._patch("/api/dcim/virtual-chassis/", vcs_to_change)


        

        ##########
        # Devices
        ########## 
        self.logger.debug("Adding devices")
        for device in devices_to_add:
            device['tags'] = [loaded_from_libre_tag_id]
            if device.get('virtual_chassis'):
                try:
                    device['virtual_chassis'] = [y.database_pk for x,y in self.store._data['virtual_chassis'].items() if x == device['virtual_chassis']][0]
                except:
                    self.logger.error(f'Error adding device: {device['hostname']} to virtual chassis: {device['virtual_chassis']}')
        self.logger.debug(devices_to_add)
        if len(devices_to_add) > 0:
            added_devices = self.netbox._post("/api/dcim/devices/", devices_to_add, verify=True)
            self.logger.debug(f"Response for adding devices: {added_devices}")
            for device in added_devices:
                self.store._data['device'][device['name']].database_pk=device['id']
                

        ##########
        # Interfaces
        ##########
        self.logger.debug("Adding interfaces")
        if len(interfaces_to_add) > 0:
            new_interfaces_to_add = []
            for interface in interfaces_to_add:
                interface['tags'] = [loaded_from_libre_tag_id]
                # Check if interface was already created from the device_type
                device_type = self.store._data['device'][interface['hostname']].device_type
                interface['device'] = self.store._data['device'][interface.get('hostname')].database_pk
                if self.store._data['interface_template'].get(f'{device_type}____{interface['name']}'):
                    # Interface was created when the device was created from template
                    # Get id of interface created by device_type
                    interfaces = self.netbox.get_interfaces_from_device(interface['device'])
                    for interface2 in interfaces:
                        if interface['name'] == interface2['name']:
                            self.store._data['interface'][interface.get('hostname')+"__"+interface['name']].database_pk=interface2['id']
                            interface['id'] = interface2['id']
                            interfaces_to_change.append(interface)
                else:
                    # Interface was NOT created when the device was created from template
                    new_interfaces_to_add.append(interface)
                    
            added_interfaces = self.netbox._post("/api/dcim/interfaces/", new_interfaces_to_add)
            self.logger.debug(f"Response for adding interfaces: {added_interfaces}")
            for interface in added_interfaces:
                self.store._data['interface'][interface.get('device', {}).get('name')+"__"+interface['name']].database_pk=interface['id']
        # Updating interfaces
        changed_interface = self.netbox._patch("/api/dcim/interfaces/", interfaces_to_change)
        self.logger.debug(changed_interface)


        ##########
        # Ip addresses
        ##########
        self.logger.debug("Adding ips")
        if len(ips_to_add) > 0:
            for ip in ips_to_add:
                ip['tags'] = [loaded_from_libre_tag_id]
                # if ip.get('parent'):
                ip['assigned_object_type'] = 'dcim.interface'
                ip['assigned_object_id'] = self.store._data['interface'][ip['parent']].database_pk
            added_ips = self.netbox._post("/api/ipam/ip-addresses/", ips_to_add, verify=True)
            self.logger.debug(f"Response for adding ips: {added_ips}")
            for ip in added_ips:
                ip_address, ip_subnet = ip['address'].split('/')
                if ':' in ip_address:
                    ip_address = expand_ipv6(ip_address)
                self.store._data['ip'][f"{ip_address}__{ip_subnet}"].database_pk=ip['id']
        # Updating ip addresses
        for ip in ips_to_change:
            ip['assigned_object_id'] = self.store._data['interface'][ip['parent']].database_pk
        self.logger.debug(self.netbox._patch("/api/ipam/ip-addresses/", ips_to_change))


        ##########
        # Management ip's
        ##########
        devices_to_add_primary_ip = []
        for device in devices_to_add + devices_to_change:
            stored_device = self.store._data['device'][device['name']]
            if not stored_device.mgmt_ip:
                continue
            ip_id = '__'.join(stored_device.mgmt_ip.split('/'))
            if not ip_id:
                continue
            primary_ip = self.store._data['ip'].get(ip_id)
            if not primary_ip:
                continue
            if ':' in primary_ip.ip:
                # IPv6 Address
                device = {
                    'id': self.store._data['device'][device['name']].database_pk,
                    'primary_ip6': primary_ip.database_pk,
                }
            else:
                # IPv4 Address
                device = {
                    'id': self.store._data['device'][device['name']].database_pk,
                    'primary_ip4': primary_ip.database_pk,
                }
            devices_to_add_primary_ip.append(device)
        self.netbox._patch("/api/dcim/devices/", devices_to_add_primary_ip)

class NetboxBootstrapAdapter(Adapter):
    manufacturer = Manufacturer
    device_type = DeviceType
    site = Site
    device_role = DeviceRole
    top_level = ["manufacturer", "site", "device_role"]
    def load(self):
        unknown_manufacturer = self.manufacturer(
            name = "Unknown",
            description = "Assigned automaticly during onboarding",
            display = "Unknown",
            slug="unknown"
        )
        self.add(unknown_manufacturer)

        unknown_device_type = self.device_type(
            model = "Unknown",
            description = "Assigned automaticly during onboarding",
            manufacturer_name = "Unknown",
            slug="unknown",
            part_number="",
            is_full_depth=True,
            weight=None,
            weight_unit=None,
            airflow=None,
            comments="",

        )
        self.add(unknown_device_type)
        unknown_manufacturer.add_child(unknown_device_type)

        unknown_site = self.site(
            name = "Unknown",
            description = "Assigned automaticly during onboarding",
            slug="unknown",
            status='active',
            comments="",

        )
        self.add(unknown_site)
        

        unknown_device_role = self.device_role(
            name = "Unknown",
            description = "Assigned automaticly during onboarding",
            slug="unknown",
            color='00ff00',
            vm_role=True,
        )
        self.add(unknown_device_role)


class LibreNMSDeviceAdapter(Adapter):

    device = Device
    device_role = DeviceRole
    virtual_chassis = VirtualChassis
    interface = Interface
    ip = IPAddress
    site = Site
    manufacturer = Manufacturer
    device_type = DeviceType
    interface_template = InterfaceTemplate
    power_port_template = PowerPortTemplate
    power_outlet_template = PowerOutletTemplate
    console_port_template = ConsolePortTemplate
    console_server_port_template = ConsoleServerPortTemplate
    rear_port_template = RearPortTemplate
    front_port_template = FrontPortTemplate
    module_bay_template = ModuleBayTemplate
    # device_bay = DeviceBayTemplate]
    tag = Tag
    
    top_level = ["virtual_chassis","device", "ip", "manufacturer", "site", "device_role", "tag"]

    devicetype_dict = {}

    def __init__(self):
        logging.basicConfig(filename='device-sync-libre.log', level=logging.DEBUG)
        self.logger = logging.getLogger('librenms-adapter')
        super().__init__(self)
    

    # def __init__(self, librenms):
    #     self.librenms = librenms
        # del librenms
        # super().__init__()

    def get_devicetype_from_name(self, library_dir:str, devicetype_name:str):
        # for each file in library_dir:
        if len(self.devicetype_dict) < 1:
            for file in glob.glob(root_dir=library_dir, pathname="device-types/*/*.yaml"):
                with open(library_dir+"/"+file) as f:
                    data = yaml.safe_load(f)
                    self.devicetype_dict[data.get('model')] = data
                  
        return self.devicetype_dict.get(devicetype_name, None)
    
    def add_device_type(self, device_type_info):
        device_type_name = device_type_info['model']
        # print(f'Adding dt: {device_type_info['model']}')
        # device_type_info = self.get_devicetype_from_name('/home/jasper/devicetype-library', device_type_name)
        # device_type_info = self.librenms.get_devicetype_from_name(device_type_name)

        if device_type_info:
            if device_type_info['manufacturer'] not in self.store._data['manufacturer']:
                manufacturer = self.manufacturer(
                    name=device_type_info['manufacturer'],
                    slug=slugify(device_type_info['manufacturer'])
                    )
                self.add(manufacturer)
            else:
                manufacturer = self.store._data['manufacturer'][device_type_info['manufacturer']]
            device_type_info['manufacturer_name'] = device_type_info['manufacturer']
            device_type = self.device_type(**device_type_info)
            self.add(device_type)
            manufacturer.add_child(device_type)
            if 'interfaces' in device_type_info:
                # print('Found interfaces')
                for interface in device_type_info['interfaces']:
                    itt = self.add_interface_template(interface, device_type_name)
                    device_type.add_child(itt)
            if 'power-ports' in device_type_info:
                for component in device_type_info['power-ports']:
                    new_component = self.add_generic_component(self.power_port_template, component, device_type_name)
                    device_type.add_child(new_component)
            if 'power-port' in device_type_info:
                    component = device_type_info['power-port']
                    new_component = self.add_generic_component(self.power_port_template, component, device_type_name)
                    device_type.add_child(new_component)
            if 'console-ports' in device_type_info:
                for component in device_type_info['console-ports']:
                    new_component = self.add_generic_component(self.console_port_template, component, device_type_name)
                    device_type.add_child(new_component)
            if 'power-outlets' in device_type_info:
                for component in device_type_info['power-outlets']:
                    new_component = self.add_generic_component(self.power_outlet_template, component, device_type_name)
                    device_type.add_child(new_component)
            if 'console-server-ports' in device_type_info:
                for component in device_type_info['console-server-ports']:
                    new_component = self.add_generic_component(self.console_server_port_template, component, device_type_name)
                    device_type.add_child(new_component)
            if 'rear-ports' in device_type_info:
                for component in device_type_info['rear-ports']:
                    new_component = self.add_generic_component(self.rear_port_template, component, device_type_name)
                    device_type.add_child(new_component)
            if 'front-ports' in device_type_info:
                for component in device_type_info['front-ports']:
                    new_component = self.add_generic_component(self.front_port_template, component, device_type_name)
                    device_type.add_child(new_component)
            if 'device-bays' in device_type_info:
                pass
                # for db in device_type_info['device-bays-bays']:
                #     component = self.add_generic_component(self.device_bay ,db, device_type_name)
                #     device_type.add_child(component)
            if 'module-bays' in device_type_info:
                for component in device_type_info['module-bays']:
                    new_component = self.add_generic_component(self.module_bay_template, component, device_type_name)
                    device_type.add_child(new_component)
            # Add images?

    def add_generic_component(self, type, component:dict, device_type:str):
        component['device_type'] = device_type
        new_component = type(**component)
        self.add(new_component)
        return new_component


    def add_interface_template(self, interface_template: dict, device_type: str):
        interface_template['interface_type'] = interface_template['type']
        interface_template['device_type'] = device_type
        interface_template['name'] = convert_interface_name(interface_template['name'])
        new_interface_template = self.interface_template(**interface_template)
        self.add(new_interface_template)
        return new_interface_template
        

    def load(self):
        ################ 
        #  Bootstrap   #
        ################
        tag = self.tag(
            name = "Loaded from Librenms",
            slug = "loaded-from-librenms",
            color = "e91e63",
            weight = 1000,
            object_types = [],
            description = "Objects created from sync from LibreNms",
        )
        self.add(tag)

        unknown_manufacturer = self.manufacturer(
            name = "Unknown",
            description = "Assigned automaticly during onboarding",
            display = "Unknown",
            slug="unknown"
        )
        self.add(unknown_manufacturer)

        unknown_device_type = self.device_type(
            model = "Unknown",
            description = "Assigned automaticly during onboarding",
            manufacturer_name = "Unknown",
            slug="unknown",
            part_number="",
            is_full_depth=True,
            weight=None,
            weight_unit='',
            airflow='',
            comments='',

        )
        self.add(unknown_device_type)
        unknown_manufacturer.add_child(unknown_device_type)

        unknown_site = self.site(
            name = "Unknown",
            description = "Assigned automaticly during onboarding",
            slug="unknown",
            status='active',
            comments="",

        )
        self.add(unknown_site)
        

        unknown_device_role = self.device_role(
            name = "Unknown",
            description = "Assigned automaticly during onboarding",
            slug="unknown",
            color='00ff00',
            vm_role=True,
        )
        self.add(unknown_device_role)

        # self.add_device_type(self.librenms.get_devicetype_from_name('HD5-24A'))
        # self.add_device_type(self.librenms.get_devicetype_from_model('AP7911'))
        # return

        ###############
        # Actual sync #
        ###############
        devices = self.librenms.get_all_devices()
        devices_by_id = {}
        for device in devices:
            devices_by_id[device['device_id']] = device
        raw_ports = self.librenms.get_all_ports()
        ports = {}
        for port in raw_ports:
            ports[port['port_id']] = port
        raw_ips = self.librenms.get_all_ips()
        ips = {}
        for ip in raw_ips:
            try:
                portinfo = ports[ip['port_id']]
                portinfo['ifName'] = convert_interface_name(portinfo['ifName'])
                portinfo['device_name'] = devices_by_id[portinfo['device_id']]['sysName'].lower()
                if 'ipv4_prefixlen' in ip.keys():
                    # Skip loopbacks
                    if ip['ipv4_address'] == '127.0.0.1':
                        continue
                    ipv4 = True
                    if ip['ipv4_prefixlen'] == 0:
                        ip['ipv4_prefixlen'] = 32
                    ips[ip['ipv4_address']] = ip | portinfo
                elif 'ipv6_prefixlen' in ip.keys():
                    ipv4 = False
                    if ip['ipv6_prefixlen'] == 0:
                        ip['ipv6_prefixlen'] = 64
                    ips[expand_ipv6(ip['ipv6_address'])] = ip | portinfo
            except Exception as e:
                print(f"Problem adding IP: {ip} -> {e}")
                print(traceback.format_exc())
                pass
                
        unknown_device_types: set = set()
        for i, device in enumerate(devices):
            if i % 10 == 0:
                print(f'Gathered {i} devices of {len(devices)}: {(i/len(devices))*100}%')
            device_ips = self.librenms.get_device_ips(device['device_id'])
            try:
                if device['os'] != 'ping' and device['hardware']:
                    extended_info = self.librenms.get_extended_device_info(device['device_id'])
                    try:
                        ip_info = ips[device['ip']]
                        if ip_info.get('ipv4_prefixlen') == 0:
                            ip_info['ipv4_prefixlen'] = 32
                    except:
                        ip_info = {}
                        
                    interface_name = ip_info.get('ifName', 'unknown') # interface name
                

                    if len(extended_info.get('stacks', [])) > 1:
                        # Device is a stack of multiple members
                        for stack_id, stack_member in enumerate(extended_info.get('stacks', [])):
                            # Prevents unknown devicetypes being created
                            device_type = self.librenms.get_devicetype_from_name(stack_member['model'])
                            if not device_type:
                                unknown_device_types.add(stack_member['entPhysicalDescr'])
                                raise UnknownDeviceTypeException(stack_member['entPhysicalDescr'])
                            device_type_name = device_type['model']
                            if not device_type:
                                print(f"Not adding {device['sysName'].lower()}-member-{stack_id}. Devicetype not known: {stack_member['entPhysicalDescr']}")
                                continue
                            item = self.device(
                                hostname=f"{device['sysName'].lower()}-member-{stack_id}", 
                                serial=stack_member['entPhysicalSerialNum'] if stack_member['entPhysicalSerialNum'] != None else '',
                                mgmt_ip = expand_ipv6(device['ip'])+"/"+str(ip_info.get('ipv4_prefixlen') or ip_info.get('ipv6_prefixlen') or 32) if stack_id==0 else '',
                                device_type=device_type_name, 
                                status = 'active' if device['status'] == 1 else 'offline',
                                database_pk = device['device_id'],
                                virtual_chassis = device['sysName'].lower(),
                                vc_position = stack_id,

                            )
                            if not self.store._data['device_type'].get(device_type_name):
                                dt = self.add_device_type(device_type)
                            self.add(item)
                            if stack_id == 0:
                                if device_ips:
                                    for ip in device_ips:
                                        try:
                                            interface_item = self.interface(
                                                hostname=f"{device['sysName'].lower()}-member-{stack_id}", 
                                                interface=convert_interface_name(ports[ip['port_id']]['ifName']),
                                            )
                                            self.add(interface_item)
                                            item.add_child(interface_item)
                                        except ObjectAlreadyExists:
                                            pass
                                        except Exception as e:
                                            print(e)

                                        try:
                                            ip_item = self.ip(
                                                ip = ip['ipv4_address'] if ip.get('ipv4_address') else expand_ipv6(ip['ipv6_address']),
                                                subnet = str(ip_info.get('ipv4_prefixlen') or ip_info.get('ipv6_prefixlen') or 32),
                                                parent = interface_item.hostname+"__"+interface_item.interface,
                                            )
                                            self.add(ip_item)
                                        except ObjectAlreadyExists:
                                            pass
                                        except Exception as e:
                                            print(e)
                                    
                        vc = self.virtual_chassis(
                            name=device['sysName'].lower(),
                        )
                        self.add(vc)
                    else:
                        device_type = self.librenms.get_devicetype_from_name(device['hardware'])
                        if not device_type:
                            unknown_device_types.add(device['hardware'])
                            raise UnknownDeviceTypeException(device['hardware'])
                        device_type_name = device_type['model']
                        if not device_type:
                            print(f"Not adding {device['sysName'].lower()}. Devicetype not known: {device['hardware']}")
                            continue
                        if not self.store._data['device_type'].get(device_type_name):
                            dt = self.add_device_type(device_type)
                        item = self.device(
                            hostname=device['sysName'].lower(), 
                            mgmt_ip = expand_ipv6(device['ip'])+"/"+str(ip_info.get('ipv4_prefixlen') or ip_info.get('ipv6_prefixlen') or 32),
                            serial=device['serial'] if device['serial'] != None else '', 
                            device_type= device_type_name,
                            status = 'active' if device['status'] == 1 else 'offline',
                            database_pk = device['device_id'],
                        )
                        if device_ips:
                            for ip in device_ips:
                                try:
                                    interface_item = self.interface(
                                        hostname=f"{device['sysName'].lower()}", 
                                        interface=convert_interface_name(ports[ip['port_id']]['ifName']),
                                    )
                                    self.add(interface_item)
                                    item.add_child(interface_item)
                                except ObjectAlreadyExists:
                                    pass
                                except Exception as e:
                                    print(e)

                                try:
                                    ip_item = self.ip(
                                        ip = ip['ipv4_address'] if ip.get('ipv4_address') else expand_ipv6(ip['ipv6_address']),
                                        subnet = str(ip_info.get('ipv4_prefixlen') or ip_info.get('ipv6_prefixlen') or 32),
                                        parent = interface_item.hostname+"__"+interface_item.interface,
                                    )
                                    self.add(ip_item)

                                except ObjectAlreadyExists:
                                    pass
                                except Exception as e:
                                    print(e)
                                
                            self.add(item)
            except UnknownDeviceTypeException as e:
                pass
            except Exception as e:
                self.logger.error(traceback.format_exc())
                print(f"Error adding device Device: {device} \n {e}")
            
        print(f"The following devices were not added because they could not be found in the devicetype_mapping or as part_number in the devicetype library: \n{unknown_device_types}")

class LibreNMSTemplateAdapter(Adapter):

    alert_rule = AlertRule
    alert_template = AlertTemplate
    librenms_device_group = LibreNMSDeviceGroup
    top_level = ["librenms_device_group", "alert_template", "alert_rule"]

    def __init__(self, librenms, name=""):
        self.librenms: LibreNMS = librenms
        super().__init__(name=name)

    def load(self):
        try:
            device_groups = self.librenms.get_device_groups()
        except Exception as e:
            print(f"Error getting devicegroups: {e}")
        try:
            rules = self.librenms.get_alert_rules()
        except Exception as e:
            print(f"Error getting rules: {e}")
        try:
            templates = self.librenms.get_alert_templates()
        except Exception as e:
            print(f"Error getting alert templates: {e}")

        if device_groups:
            for group in device_groups:
                try:
                    item = self.librenms_device_group(
                        name=group['name'],
                        desc=group['desc'],
                        type=group['type'],
                        rules=group['rules'],
                        pattern=group['pattern'],
                        database_pk=group['id']
                    )
                    self.add(item)
                except Exception as e:
                    print(f"Error parsing Device group: {group} -> {e}")

        if rules:
            for rule in rules:
                try:
                    if isinstance(rule['extra'], str):
                        rule['extra'] = json.loads(rule['extra'])
                    if isinstance(rule['builder'], str):
                        rule['builder'] = json.loads(rule['builder'])

                    named_groups = []
                    for group_id in rule['groups']:
                        group_name = [k for k, v in list(self.store._data['librenms_device_group'].items()) if v.database_pk == group_id][0]
                        named_groups.append(group_name)
                    item = self.alert_rule(
                        name=rule['name'],
                        severity=rule['severity'],
                        mute=rule['extra']['mute'],
                        count=int(rule['extra']['count']) if 'count' in rule['extra'] and rule['extra']['count'] else 0,
                        delay=rule['extra']['delay'],
                        invert=rule['extra']['invert'] if 'invert' in rule['extra'].keys() else False,
                        interval=rule['extra']['interval'],
                        disabled=rule['disabled'],
                        query=rule['query'].replace('\r', '').replace('\n', ''),
                        builder=rule['builder'],
                        proc=rule['proc'] if rule['proc'] else '',
                        invert_map=rule['invert_map'],
                        override_query=rule['extra']['options']['override_query'] if rule.get('extra',{}).get('options',{}).get('override_query') else None,
                        notes=rule['notes'],
                        groups=named_groups,
                        database_pk=rule['id']
                    )
                    
                    self.add(item)
                except Exception as e:
                    print(f"Error parsing Alert Rule: {rule} -> {e}")
        if templates:
            for template in templates:
                try:
                    item = self.alert_template(
                        name=template['name'],
                        template=template['template'],
                        title=template['title'],
                        title_rec=template['title_rec'],
                        alert_rules=template['alert_rules'],
                        database_pk=template['id']
                    )
                    self.add(item)
                except Exception as e:
                    print(f"Error parsing Alert template: {template} -> {e}")

