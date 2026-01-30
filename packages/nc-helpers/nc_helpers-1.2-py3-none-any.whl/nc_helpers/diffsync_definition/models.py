from typing import List, Optional, Dict
from diffsync import DiffSyncModel, Adapter

class Tag(DiffSyncModel):

    _modelname = "tag"
    _identifiers = ("name",)
    _shortname = ()
    _attributes = ("slug", "color", "weight", "object_types", "description")


    name: str
    slug: str
    color: str
    weight: int
    object_types: List[str]
    description: Optional[str] = "" 
    database_pk: Optional[int] = None

class Manufacturer(DiffSyncModel):

    _modelname = "manufacturer"
    _identifiers = ("name",)
    _shortname = ()
    _attributes = ("slug", "description")
    _children = {"device_type": "device_types", 'module_type': "module_types"}

    name: str
    slug: str
    description: Optional[str] = "" 
    device_types: List = list()
    module_types: List = list()
    database_pk: Optional[int] = None

class DeviceType(DiffSyncModel):

    _modelname = "device_type"
    _identifiers = ("model",)
    _shortname = ()
    _attributes = (
        "slug",
        "manufacturer_name",
        "part_number",
        "is_full_depth", 
        "airflow", 
        "weight",
        "weight_unit",
        "description",
        "comments",)
    _children = {
        'interface_template': 'interface_templates', 
        'power_port_template': 'power_port_templates', 
        'power_outlet_template':'power_outlet_templates',
        'console_port_template': 'console_port_templates',
        'consoles_server_port_template': 'console_server_port_templates',
        'front_port_template': 'front_port_templates',
        'rear_port_template': 'rear_port_templates',
        'module_bay_template': 'module_bay_templates',
        }

    model: str
    slug: str
    manufacturer_name: str
    part_number: Optional[str] = ""
    is_full_depth: bool
    airflow: Optional[Dict|str] = ""
    weight: Optional[float] = 0
    weight_unit: Optional[Dict|str] = ""
    description: Optional[str] = ""
    comments: Optional[str] = ""
    interface_templates: List = list()
    power_port_templates: List = list()
    power_outlet_templates: List = list()
    console_port_templates: List = list()
    console_server_port_templates: List = list()
    rear_port_templates: List = list()
    front_port_templates: List = list()
    module_bay_templates: List = list()
    database_pk: Optional[int] = None

class ModuleType(DiffSyncModel):

    _modelname = "module_type"
    _identifiers = ("model",)
    _shortname = ()
    _attributes = (
        "manufacturer_name",
        "part_number",
        "weight",
        "weight_unit",
        "description",
        "comments",)
    _children = {'interface_template': 'interface_templates'}

    model: str
    manufacturer_name: str
    part_number: str
    weight: Optional[float]
    weight_unit: Optional[Dict]
    description: str 
    comments: str
    interface_templates: List = list()
    database_pk: Optional[int] = None
    

class InterfaceTemplate(DiffSyncModel):

    _modelname = "interface_template"
    _identifiers = ("device_type","module_type","name")
    _shortname = ()
    _attributes = (
        "interface_type",
        "enabled",
        "mgmt_only",
        "description", 
        "bridge", 
        "poe_mode",
        "poe_type",
        "rf_role",)
    _children = {}

    device_type: Optional[str] = ""
    name: str
    module_type: Optional[str] = ""
    interface_type: Dict|str
    enabled: bool = True
    mgmt_only: bool = False
    description: Optional[str] = ""
    bridge: Optional[Dict] = None
    poe_mode: Optional[Dict|str] = ""
    poe_type: Optional[Dict|str] = ""
    rf_role: Optional[Dict|str] = ""
    database_pk: Optional[int] = None

class PowerPortTemplate(DiffSyncModel):

    _modelname = "power_port_template"
    _identifiers = ("device_type","module_type","name")
    _shortname = ()
    _attributes = (
        "type",
        "maximum_draw",
        "allocated_draw", 
        "description", 
    )
    _children = {}

    device_type: Optional[str] = ""
    name: str
    module_type: Optional[str] = ""
    type: str
    maximum_draw: Optional[int] = None
    allocated_draw: Optional[int] = None
    description: Optional[str] = ""
    database_pk: Optional[int] = None

class PowerOutletTemplate(DiffSyncModel):

    _modelname = "power_outlet_template"
    _identifiers = ("device_type","module_type","name")
    _shortname = ()
    _attributes = (
        "type",
        "label", 
        "power_port", 
        "feed_leg", 
        "description", 
    )
    _children = {}

    device_type: Optional[str] = ""
    module_type: Optional[str] = ""
    name: str
    type: str
    label: Optional[str] = ''
    power_port: str = ""
    feed_leg: Optional[str] = ''
    description: Optional[str] = ""
    database_pk: Optional[int] = None
    
class ConsolePortTemplate(DiffSyncModel):

    _modelname = "console_port_template"
    _identifiers = ("device_type","module_type","name")
    _shortname = ()
    _attributes = (
        "type",
        "label",
        "description", 
    )
    _children = {}

    device_type: Optional[str] = ""    
    module_type: Optional[str] = ""
    name: str
    type: str
    label: Optional[str] = ""
    description: Optional[str] = ""
    database_pk: Optional[int] = None

class ConsoleServerPortTemplate(DiffSyncModel):

    _modelname = "console_server_port_template"
    _identifiers = ("device_type","module_type","name")
    _shortname = ()
    _attributes = (
        "type",
        "description", 
        "label", 
    )
    _children = {}

    device_type: Optional[str] = ""
    name: str
    module_type: Optional[str] = ""
    type: str
    label: Optional[str] = ""
    description: Optional[str] = ""
    database_pk: Optional[int] = None

class RearPortTemplate(DiffSyncModel):

    _modelname = "rear_port_template"
    _identifiers = ("device_type","module_type","name")
    _shortname = ()
    _attributes = (
        "type",
        "label", 
        "color", 
        "positions", 
        "description", 
    )
    _children = {}

    device_type: Optional[str] = ""
    module_type: Optional[str] = ""
    name: str
    type: str
    label: Optional[str] = ""
    color: Optional[str] = ""
    positions: int
    description: Optional[str] = ""
    database_pk: Optional[int] = None

class FrontPortTemplate(DiffSyncModel):

    _modelname = "front_port_template"
    _identifiers = ("device_type","module_type","name")
    _shortname = ()
    _attributes = (
        "type",
        "label", 
        "color", 
        "rear_port", 
        "rear_port_position", 
        "description", 
    )
    _children = {}

    device_type: Optional[str] = ""
    module_type: Optional[str] = ""
    name: str
    type: str
    label: Optional[str] = ""
    color: Optional[str] = ""
    rear_port: str
    rear_port_position: int
    description: Optional[str] = ""
    database_pk: Optional[int] = None

class ModuleBayTemplate(DiffSyncModel):

    _modelname = "module_bay_template"
    _identifiers = ("device_type","name")
    _shortname = ()
    _attributes = (
        "label",
        "position",
        "description", 
    )
    _children = {}

    device_type: str
    name: str
    label: Optional[str] = ""
    position: Optional[str] = ""
    description: Optional[str] = ""
    database_pk: Optional[int] = None
    

class Site(DiffSyncModel):

    _modelname = "site"
    _identifiers = ("name",)
    _shortname = ()
    _attributes = (
        "slug",
        "status",
        "description",
        "comments", 
    )
    _children = {}

    name: str
    slug: str
    status: str
    description: str
    comments: str
    database_pk: Optional[int] = None

class DeviceRole(DiffSyncModel):

    _modelname = "device_role"
    _identifiers = ("name",)
    _shortname = ()
    _attributes = (
        "slug",
        "color",
        "vm_role",
        "description", 
    )
    _children = {}

    name: str
    slug: str
    color: str
    vm_role: bool
    description: str
    database_pk: Optional[int] = None

class VirtualChassis(DiffSyncModel):

    _modelname = "virtual_chassis"
    _identifiers = ("name",)
    _shortname = ()
    _attributes = (
        "domain",
        "description",
    )
    _children = {}

    name: str
    domain: Optional[str] = ''
    description: Optional[str] = ''
    database_pk: Optional[int] = None

class Device(DiffSyncModel):

    _modelname = "device"
    _identifiers = ("hostname",)
    _shortname = ()
    _attributes = (
        "serial",
        "device_type",
        "status", 
        "virtual_chassis",
        "vc_position",
        "mgmt_ip",
    )
    _children = {'interface':'interfaces'}

    serial: str
    hostname: str
    device_type: str
    status: str
    mgmt_ip: Optional[str] = ""
    virtual_chassis: Optional[str] = ""
    vc_position: Optional[int] = None
    interfaces: List = list()
    database_pk: Optional[int] = None

    # @classmethod
    # def create(cls, adapter, ids, attrs):
    #     pass

    # def update(self, attrs):
    #     pass
    # def delete(self):
    #     pass

class Interface(DiffSyncModel):

    _modelname = "interface"
    _identifiers = ("hostname","interface")
    _shortname = ()
    _attributes = ()
    _children = {}

    hostname: str
    interface: str
    ips: List = list()
    database_pk: Optional[int] = None

class IPAddress(DiffSyncModel):

    _modelname = "ip"
    _identifiers = ("ip","subnet")
    _shortname = ()
    _attributes = ("parent",)
    _children = {}

    ip: str
    subnet: str
    parent: Optional[str] = None
    database_pk: Optional[int] = None


class AlertRule(DiffSyncModel):

    _modelname = "alert_rule"
    _identifiers = ("name",)
    _shortname = ()
    _attributes = (
        "severity",
        "mute",
        "count",
        "delay",
        "invert",
        "interval",
        "disabled",
        "query",
        "builder",
        "proc",
        "invert_map",
        "override_query",
        "notes",
        "groups",
    )
    _children = {}

    name: str
    severity: str
    mute: bool
    count: int
    delay: int
    invert: bool
    interval: int
    disabled: int
    query: str
    builder: dict
    proc: Optional[str]
    invert_map: int
    override_query: Optional[str]
    notes: Optional[str]
    groups: list

    database_pk: Optional[int] = None

    @classmethod
    def fix_inconsistent_api(self, current_item):
        if current_item.get("id"):
            current_item["rule_id"] = current_item["id"]

        extra = current_item["extra"] if "extra" in current_item else {}
        if extra.get("mute"):
            current_item["mute"] = extra["mute"]
        if extra.get("count"):
            current_item["count"] = extra["count"]
        if extra.get("delay"):
            current_item["delay"] = str(extra["delay"])
        if extra.get("invert"):
            current_item["invert"] = extra["invert"]
        if extra.get("interval"):
            current_item["interval"] = str(extra["interval"])
        if extra.get("options", {}).get("override_query"):
            current_item["override_query"] = extra.get("options", {}).get(
                "override_query"
            )
            current_item["adv_query"] = current_item["query"]

        if current_item["devices"] == []:
            current_item["devices"] = -1

        # current_item['extra']['delay'] = str(current_item['extra']['delay'])
        # current_item['extra']['interval'] = str(current_item['extra']['delay'])
        return current_item

    @classmethod
    def create(cls, adapter: Adapter, ids: dict, attrs: dict):
        """Create a new alert rule in LibreNMS.

        Args:
            adapter: The master data store for other DiffSyncModel instances that we might need to reference
            ids: Dictionary of unique-identifiers needed to create the new object
            attrs: Dictionary of additional attributes to set on the new object

        Returns:
            AlertRule: DiffSync object newly created
        """
        groups = []
        for group in attrs["groups"]:
            groups.append(adapter.store._data['librenms_device_group'][group].database_pk)
        data = {
            "severity": attrs["severity"],
            "mute": attrs["mute"],
            "count": attrs["count"],
            "delay": attrs["delay"],
            "invert": attrs["invert"],
            "interval": attrs["interval"],
            "disabled": attrs["disabled"],
            "name": ids["name"],
            # "query": attrs['query'],
            "builder": attrs["builder"],
            "proc": attrs["proc"],
            "invert_map": attrs["invert_map"],
            "override_query": attrs["override_query"],
            "notes": attrs["notes"],
            "devices": -1,
            "groups": groups,
            "locations": [],
        }
        if attrs["override_query"]:
            data["adv_query"] = attrs["query"]
        data = AlertRule.fix_inconsistent_api(data)
        result = adapter.librenms.add_alert_rule(alert_rule=data)

        # TODO: Add the newly created remote_id and create the internal object for this resource.
        # Librenms API does not return id after creation of rules :/
        item = super().create(ids=ids, adapter=adapter, attrs=attrs)
        return item

    def update(self, attrs: dict):
        """Update an alert rule in librenms.

        Args:
            attrs: Dictionary of attributes to update on the object

        Returns:
            DiffSyncModel: this instance, if all data was successfully updated.
            None: if data updates failed in such a way that child objects of this model should not be modified.

        Raises:
            ObjectNotUpdated: if an error occurred.
        """
        libre = self.adapter.librenms
        current_item = libre.get_alert_rule(self.database_pk)[0]
        print(current_item)

        current_item.update(attrs)
        current_item = AlertRule.fix_inconsistent_api(current_item)

        libre.add_alert_rule(alert_rule=current_item)
        print(f"Updated alert rule: {attrs}")

        return super().update(attrs)


class AlertTemplate(DiffSyncModel):

    _modelname = "alert_template"
    _identifiers = ("name",)
    _shortname = ()
    _attributes = (
        "template",
        "title",
        "title_rec",
        "alert_rules",
    )
    _children = {}

    name: str
    template: str
    title: Optional[str]
    title_rec: Optional[str]
    alert_rules: list

    database_pk: Optional[int] = None

    @classmethod
    def create(cls, adapter: Adapter, ids: dict, attrs: dict):
        """Create a new alert template in LibreNMS.

        Args:
            adapter: The master data store for other DiffSyncModel instances that we might need to reference
            ids: Dictionary of unique-identifiers needed to create the new object
            attrs: Dictionary of additional attributes to set on the new object

        Returns:
            AlertTemplate: DiffSync object newly created
        """
        data = {
            "name": ids["name"],
            "template": attrs["template"],
            "title": ids["title"],
            "title_rec": attrs["title_rec"],
            "alert_rules": attrs["alert_rules"],
        }
        result = adapter.librenms.add_alert_template(alert_rule=data)

        # TODO: Add the newly created remote_id and create the internal object for this resource.
        # Librenms API does not return id after creation of rules :/
        item = super().create(ids=ids, adapter=adapter, attrs=attrs)
        item.database_pk = result.get("id")
        return item

    def update(self, attrs: dict):
        """Update a alert template in librenms.

        Args:
            attrs: Dictionary of attributes to update on the object

        Returns:
            DiffSyncModel: this instance, if all data was successfully updated.
            None: if data updates failed in such a way that child objects of this model should not be modified.

        Raises:
            ObjectNotUpdated: if an error occurred.
        """
        libre = self.adapter.librenms
        current_item = libre.get_alert_template(self.database_pk)[0]

        current_item.update(attrs)

        libre.add_alert_template(alert_template=current_item)
        print(f"Updated alert template: {self.slug} | {attrs}")

        return super().update(attrs)


class LibreNMSDeviceGroup(DiffSyncModel):

    _modelname = "librenms_device_group"
    _identifiers = ("name",)
    _shortname = ()
    _attributes = (
        "desc",
        "type",
        "rules",
        "pattern",
    )
    _children = {}

    name: str
    desc: Optional[str]
    type: Optional[str]
    rules: Optional[dict]
    pattern: Optional[str]

    database_pk: Optional[int] = None

    @classmethod
    def create(cls, adapter: Adapter, ids: dict, attrs: dict):
        """Create a new devicegroup in LibreNMS.

        Args:
            adapter: The master data store for other DiffSyncModel instances that we might need to reference
            ids: Dictionary of unique-identifiers needed to create the new object
            attrs: Dictionary of additional attributes to set on the new object

        Returns:
            LibreNMSDeviceGroup: DiffSync object newly created
        """
        default_rule = {
            "condition": "AND",
            "rules": [
                {
                    "id": "devices.hostname",
                    "field": "devices.hostname",
                    "type": "string",
                    "input": "text",
                    "operator": "not_equal",
                    "value": "-",
                },
            ],
            "valid": True,
            "joins": [],
        }
        data = {
            "name": ids["name"],
            "desc": attrs["desc"],
            "type": 'dynamic',
            "rules": (
                json.dumps(attrs["rules"])
                if attrs["type"] == "dynamic"
                else json.dumps(default_rule)
            ),
            "pattern": attrs["pattern"],
        }
        result = adapter.librenms.add_device_group(device_group=data)

        # TODO: Add the newly created remote_id and create the internal object for this resource.
        # Librenms API does not return id after creation of rules :/
        item = super().create(ids=ids, adapter=adapter, attrs=attrs)
        # item.database_pk = result.get('id')
        return item

    def update(self, attrs: dict):
        """Update a devicegroup in librenms.

        Args:
            attrs: Dictionary of attributes to update on the object

        Returns:
            DiffSyncModel: this instance, if all data was successfully updated.
            None: if data updates failed in such a way that child objects of this model should not be modified.

        Raises:
            ObjectNotUpdated: if an error occurred.
        """

        #
        # We should not be changing devicegroups.....
        #

        # libre = self.adapter.librenms
        # attrs["name"] = self.name
        # attrs['rules'] = json.dumps(attrs['rules'])

        # libre.update_device_group(device_group=attrs)
        # print(f"Updated alert template: {attrs}")

        return super().update(attrs)
