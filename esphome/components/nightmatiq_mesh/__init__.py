import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import (
    esp32,
    binary_sensor,
    button,
    esp32_ble,
    number,
    select,
    sensor,
    switch,
    text_sensor,
    web_server_base,
)
from esphome.components.esphome import ota as esphome_ota
from esphome.components.web_server_base import CONF_WEB_SERVER_BASE_ID
from esphome.const import (
    CONF_ADDRESS,
    CONF_ID,
    CONF_NAME,
    DEVICE_CLASS_ILLUMINANCE,
    DEVICE_CLASS_MOTION,
    DEVICE_CLASS_SIGNAL_STRENGTH,
    ENTITY_CATEGORY_CONFIG,
    ENTITY_CATEGORY_DIAGNOSTIC,
    STATE_CLASS_MEASUREMENT,
    UNIT_DECIBEL_MILLIWATT,
    UNIT_LUX,
    UNIT_PERCENT,
    UNIT_SECOND,
)

CODEOWNERS = []
DEPENDENCIES = ["esp32", "web_server"]
AUTO_LOAD = [
    "binary_sensor",
    "button",
    "esp32_ble",
    "number",
    "select",
    "sensor",
    "switch",
    "text_sensor",
    "web_server_base",
]

# Mode historique : entites de la lampe principale declarees a la main dans le YAML
CONF_LUX_SENSOR_ID = "lux_sensor_id"
CONF_RSSI_SENSOR_ID = "rssi_sensor_id"
CONF_THRESHOLD_NUMBER_ID = "threshold_number_id"
CONF_MODE_SELECT_ID = "mode_select_id"
CONF_READY_BINARY_SENSOR_ID = "ready_binary_sensor_id"
CONF_ACTUAL_OUTPUT_BINARY_SENSOR_ID = "actual_output_binary_sensor_id"
CONF_STATUS_TEXT_SENSOR_ID = "status_text_sensor_id"
CONF_FIRMWARE_VERSION_TEXT_SENSOR_ID = "firmware_version_text_sensor_id"
CONF_HARDWARE_VERSION_SENSOR_ID = "hardware_version_sensor_id"
CONF_MANUFACTURER_TEXT_SENSOR_ID = "manufacturer_text_sensor_id"
CONF_COMPANY_ID_TEXT_SENSOR_ID = "company_id_text_sensor_id"
CONF_PRODUCT_ID_TEXT_SENSOR_ID = "product_id_text_sensor_id"
LEGACY_IDS = [
    CONF_LUX_SENSOR_ID,
    CONF_RSSI_SENSOR_ID,
    CONF_THRESHOLD_NUMBER_ID,
    CONF_MODE_SELECT_ID,
    CONF_READY_BINARY_SENSOR_ID,
    CONF_ACTUAL_OUTPUT_BINARY_SENSOR_ID,
    CONF_STATUS_TEXT_SENSOR_ID,
    CONF_FIRMWARE_VERSION_TEXT_SENSOR_ID,
    CONF_HARDWARE_VERSION_SENSOR_ID,
    CONF_MANUFACTURER_TEXT_SENSOR_ID,
    CONF_COMPANY_ID_TEXT_SENSOR_ID,
    CONF_PRODUCT_ID_TEXT_SENSOR_ID,
]

CONF_EXTENDED_DIAGNOSTICS = "extended_diagnostics"
CONF_WEB_USERNAME = "web_username"
CONF_WEB_PASSWORD = "web_password"
CONF_OTA_ID = "ota_id"

# Mode declaratif
CONF_PRIMARY = "primary"
CONF_LAMPS = "lamps"
CONF_GROUPS = "groups"
CONF_STATE_GROUPS = "state_groups"
CONF_GATEWAY = "gateway"
CONF_TAG = "tag"
CONF_SCENE = "scene"
CONF_ELEMENTS = "elements"
CONF_LC_PROPS = "lc_props"
CONF_DEVICE_KEY = "device_key"
CONF_PRODUCT_ID = "product_id"
CONF_MANUFACTURER = "manufacturer"
CONF_COMPANY = "company"

nightmatiq_ns = cg.esphome_ns.namespace("nightmatiq_mesh")
NightmatiqMesh = nightmatiq_ns.class_("NightmatiqMesh", cg.PollingComponent)

LampSensor = nightmatiq_ns.class_("LampSensor", sensor.Sensor, cg.PollingComponent)
LampBinarySensor = nightmatiq_ns.class_("LampBinarySensor", binary_sensor.BinarySensor, cg.PollingComponent)
LampNumber = nightmatiq_ns.class_("LampNumber", number.Number, cg.PollingComponent)
PrimaryThresholdNumber = nightmatiq_ns.class_("PrimaryThresholdNumber", number.Number, cg.Component)
LampModeSelect = nightmatiq_ns.class_("LampModeSelect", select.Select, cg.PollingComponent)
PrimaryModeSelect = nightmatiq_ns.class_("PrimaryModeSelect", select.Select, cg.Component)
LampTextSensor = nightmatiq_ns.class_("LampTextSensor", text_sensor.TextSensor, cg.PollingComponent)
LampRelaySwitch = nightmatiq_ns.class_("LampRelaySwitch", switch.Switch, cg.PollingComponent)
GatewayButton = nightmatiq_ns.class_("GatewayButton", button.Button, cg.Component)

LampSensorKind = nightmatiq_ns.enum("LampSensorKind", is_class=True)
LampBinaryKind = nightmatiq_ns.enum("LampBinaryKind", is_class=True)
LampNumberKind = nightmatiq_ns.enum("LampNumberKind", is_class=True)
LampTextKind = nightmatiq_ns.enum("LampTextKind", is_class=True)
GatewayButtonKind = nightmatiq_ns.enum("GatewayButtonKind", is_class=True)

MODE_OPTIONS = ["Auto", "Always On", "Always Off"]
LC_POWER, LC_BASE_LIGHT, LC_RUN_ON = 0x002E, 0x0030, 0x003C
POLL = cv.polling_component_schema("1s")

# ---------------------------------------------------------------------------
# Catalogue des entites generees par lampe.
# Les noms ("<nom de la lampe> <suffixe>") sont ceux du YAML historique : ESPHome
# derive l'unique_id du nom, donc les entity_id Home Assistant sont conserves.
# Chaque entite peut etre surchargee (dict : name, icon, filters, internal...)
# ou supprimee (false) sous sa cle dans la lampe.
# ---------------------------------------------------------------------------
# role: "lamp" (lampes supplementaires), "primary", "both"
ENTITIES = {
    # --- binaires
    "light": dict(platform="binary_sensor", suffix="Lumière", role="both",
                  schema=lambda cls: binary_sensor.binary_sensor_schema(cls, icon="mdi:lightbulb")),
    "motion": dict(platform="binary_sensor", suffix="Mouvement", role="both",
                   schema=lambda cls: binary_sensor.binary_sensor_schema(cls, device_class=DEVICE_CLASS_MOTION),
                   filters=[{"delayed_off": "10s"}]),
    # --- capteurs
    "motion_level": dict(platform="sensor", suffix="Mouvement niveau", role="both",
                         schema=lambda cls: sensor.sensor_schema(
                             cls, unit_of_measurement=UNIT_PERCENT, accuracy_decimals=0,
                             entity_category=ENTITY_CATEGORY_DIAGNOSTIC),
                         filters=[{"delta": 0.4}]),
    "hardware": dict(platform="sensor", suffix="Révision matérielle", role="both",
                     schema=lambda cls: sensor.sensor_schema(
                         cls, accuracy_decimals=0, entity_category=ENTITY_CATEGORY_DIAGNOSTIC)),
    "signal": dict(platform="sensor", suffix="Signal", role="both",
                   schema=lambda cls: sensor.sensor_schema(
                       cls, unit_of_measurement=UNIT_DECIBEL_MILLIWATT, accuracy_decimals=0,
                       device_class=DEVICE_CLASS_SIGNAL_STRENGTH, state_class=STATE_CLASS_MEASUREMENT,
                       entity_category=ENTITY_CATEGORY_DIAGNOSTIC),
                   filters=[{"throttle_average": "60s"}, {"delta": 2}]),
    "illuminance": dict(platform="sensor", suffix="Luminosité", role="both",
                        schema=lambda cls, primary=False: sensor.sensor_schema(
                            cls, unit_of_measurement=UNIT_LUX, accuracy_decimals=2 if primary else 1,
                            device_class=DEVICE_CLASS_ILLUMINANCE, state_class=STATE_CLASS_MEASUREMENT),
                        filters=[{"delta": 0.5}]),
    # --- nombres (reglages LC : seulement si lc_props)
    "intensity": dict(platform="number", suffix="Intensité", role="both", lc=True,
                      schema=lambda cls: number.number_schema(
                          cls, icon="mdi:brightness-6", unit_of_measurement=UNIT_PERCENT),
                      mode="SLIDER", range=(0, 100, 1)),
    "power": dict(platform="number", suffix="Puissance", role="both", lc=True,
                  schema=lambda cls: number.number_schema(
                      cls, icon="mdi:brightness-percent", unit_of_measurement=UNIT_PERCENT),
                  mode="SLIDER", range=(1, 100, 1)),
    "base_light": dict(platform="number", suffix="Lumière de base", role="both", lc=True,
                       schema=lambda cls: number.number_schema(
                           cls, icon="mdi:lightbulb-night-outline", unit_of_measurement=UNIT_PERCENT),
                       mode="SLIDER", range=(0, 100, 1)),
    "run_on": dict(platform="number", suffix="Temporisation", role="both", lc=True,
                   schema=lambda cls: number.number_schema(
                       cls, icon="mdi:timer-outline", unit_of_measurement=UNIT_SECOND),
                   mode="BOX", range=(1, 3600, 1)),
    "threshold": dict(platform="number", suffix="Seuil", role="both",
                      schema=lambda cls: number.number_schema(
                          cls, icon="mdi:brightness-6", unit_of_measurement=UNIT_LUX),
                      mode="SLIDER", range=(1, 40, 1)),
    # --- select
    "mode": dict(platform="select", suffix="Mode", role="both",
                 schema=lambda cls: select.select_schema(cls, icon="mdi:theme-light-dark")),
    # --- textes
    "firmware": dict(platform="text_sensor", suffix="Firmware", role="both",
                     schema=lambda cls: text_sensor.text_sensor_schema(
                         cls, icon="mdi:chip", entity_category=ENTITY_CATEGORY_DIAGNOSTIC)),
    "manufacturer_text": dict(platform="text_sensor", suffix="Fabricant", role="both",
                         schema=lambda cls: text_sensor.text_sensor_schema(
                             cls, icon="mdi:factory", entity_category=ENTITY_CATEGORY_DIAGNOSTIC)),
    "company_id_text": dict(platform="text_sensor", suffix="Company ID", role="both",
                       schema=lambda cls: text_sensor.text_sensor_schema(
                           cls, icon="mdi:identifier", entity_category=ENTITY_CATEGORY_DIAGNOSTIC)),
    "product_id_text": dict(platform="text_sensor", suffix="Product ID", role="both",
                       schema=lambda cls: text_sensor.text_sensor_schema(
                           cls, icon="mdi:identifier", entity_category=ENTITY_CATEGORY_DIAGNOSTIC)),
    # --- relais Mesh
    "relay": dict(platform="switch", suffix="Relais Mesh", role="both",
                  schema=lambda cls: switch.switch_schema(
                      cls, icon="mdi:access-point-network", entity_category=ENTITY_CATEGORY_CONFIG)),
    "relay_retransmit": dict(platform="text_sensor", suffix="Relais Mesh retransmission", role="both",
                             schema=lambda cls: text_sensor.text_sensor_schema(
                                 cls, icon="mdi:repeat", entity_category=ENTITY_CATEGORY_DIAGNOSTIC)),
}

# Classe C++ par entite, selon que la lampe est la principale ou une supplementaire
CLASSES = {
    "light": (LampBinarySensor, binary_sensor.BinarySensor),
    "motion": (LampBinarySensor, LampBinarySensor),
    "motion_level": (LampSensor, LampSensor),
    "hardware": (LampSensor, sensor.Sensor),
    "signal": (LampSensor, sensor.Sensor),
    "illuminance": (LampSensor, sensor.Sensor),
    "intensity": (LampNumber, LampNumber),
    "power": (LampNumber, LampNumber),
    "base_light": (LampNumber, LampNumber),
    "run_on": (LampNumber, LampNumber),
    "threshold": (LampNumber, PrimaryThresholdNumber),
    "mode": (LampModeSelect, PrimaryModeSelect),
    "firmware": (LampTextSensor, text_sensor.TextSensor),
    "manufacturer_text": (LampTextSensor, text_sensor.TextSensor),
    "company_id_text": (LampTextSensor, text_sensor.TextSensor),
    "product_id_text": (LampTextSensor, text_sensor.TextSensor),
    "relay": (LampRelaySwitch, LampRelaySwitch),
    "relay_retransmit": (LampTextSensor, LampTextSensor),
}

# Entites de la principale alimentees directement par le hub (pas de polling)
PRIMARY_HUB_ENTITIES = {"light", "hardware", "signal", "illuminance", "threshold", "mode",
                        "firmware", "manufacturer_text", "company_id_text", "product_id_text"}

GATEWAY_ENTITIES = {
    "mesh_ready": dict(platform="binary_sensor", name="Gateway Mesh Ready",
                       schema=lambda: binary_sensor.binary_sensor_schema(
                           binary_sensor.BinarySensor, entity_category=ENTITY_CATEGORY_DIAGNOSTIC)),
    "status": dict(platform="text_sensor", name="Gateway Status",
                   schema=lambda: text_sensor.text_sensor_schema(
                       text_sensor.TextSensor, icon="mdi:bluetooth-connect",
                       entity_category=ENTITY_CATEGORY_DIAGNOSTIC)),
    "refresh": dict(platform="button", name="Gateway Refresh",
                    schema=lambda: button.button_schema(
                        GatewayButton, icon="mdi:refresh", entity_category=ENTITY_CATEGORY_DIAGNOSTIC)),
    "relay_refresh": dict(platform="button", name="Relais Mesh Relire",
                          schema=lambda: button.button_schema(
                              GatewayButton, icon="mdi:refresh", entity_category=ENTITY_CATEGORY_DIAGNOSTIC)),
}


def _override(value):
    """Une entite se surcharge par un dict, ou se supprime avec false."""
    if value is False:
        return False
    if isinstance(value, dict):
        return value
    raise cv.Invalid("attendu : un dictionnaire de surcharge, ou false pour ne pas creer l'entite")


def _device_key(value):
    value = cv.string_strict(value).strip().replace(" ", "").replace("-", "")
    if len(value) != 32 or any(c not in "0123456789abcdefABCDEF" for c in value):
        raise cv.Invalid("DeviceKey : 32 caracteres hexadecimaux attendus")
    return value.upper()


def _expand(primary):
    """Construit et valide la config de chaque entite a partir du nom de la lampe."""

    def validator(conf):
        conf = dict(conf)
        lamp_name = conf[CONF_NAME]
        for key, spec in ENTITIES.items():
            user = conf.get(key, {})
            if user is False or (spec.get("lc") and not conf[CONF_LC_PROPS]):
                conf[key] = None
                continue
            if key == "product_id_text" and not primary and CONF_PRODUCT_ID not in conf:
                conf[key] = None  # rien a publier sans product_id declare
                continue
            cls = CLASSES[key][1 if primary else 0]
            make = spec["schema"]
            schema = make(cls, primary=True) if key == "illuminance" and primary else make(cls)
            needs_poll = not (primary and key in PRIMARY_HUB_ENTITIES)
            if needs_poll:
                schema = schema.extend(POLL)
            elif spec["platform"] in ("number", "select"):
                schema = schema.extend(cv.COMPONENT_SCHEMA)
            merged = {CONF_NAME: f"{lamp_name} {spec['suffix']}"}
            if "filters" in spec:
                merged["filters"] = spec["filters"]
            if spec["platform"] == "number":
                merged["mode"] = spec["mode"]
            merged.update(user)
            conf[key] = schema(merged)
        return conf

    return validator


ENTITY_KEYS = {cv.Optional(key): _override for key in ENTITIES}

PRIMARY_SCHEMA = cv.All(
    cv.Schema(
        {
            cv.Required(CONF_ADDRESS): cv.hex_uint16_t,
            cv.Required(CONF_NAME): cv.string_strict,
            cv.Optional(CONF_TAG): cv.hex_uint16_t,
            cv.Optional(CONF_LC_PROPS, default=True): cv.boolean,
            cv.Optional(CONF_DEVICE_KEY): cv.All(cv.sensitive(_device_key)),
            **ENTITY_KEYS,
        }
    ),
    _expand(primary=True),
)

LAMP_SCHEMA = cv.All(
    cv.Schema(
        {
            cv.Required(CONF_ADDRESS): cv.hex_uint16_t,
            cv.Required(CONF_NAME): cv.string_strict,
            cv.Optional(CONF_TAG): cv.hex_uint16_t,
            cv.Optional(CONF_SCENE, default=0): cv.hex_uint16_t,
            cv.Optional(CONF_ELEMENTS, default=4): cv.int_range(min=1, max=8),
            cv.Optional(CONF_LC_PROPS, default=True): cv.boolean,
            cv.Optional(CONF_DEVICE_KEY): cv.All(cv.sensitive(_device_key)),
            cv.Optional(CONF_PRODUCT_ID): cv.hex_uint16_t,
            cv.Optional(CONF_MANUFACTURER, default="Steinel GmbH"): cv.string_strict,
            cv.Optional(CONF_COMPANY, default="0x0563 (Steinel GmbH)"): cv.string_strict,
            **ENTITY_KEYS,
        }
    ),
    _expand(primary=False),
)


def _expand_gateway(conf):
    conf = dict(conf or {})
    for key, spec in GATEWAY_ENTITIES.items():
        user = conf.get(key, {})
        if user is False:
            if key in ("mesh_ready", "status"):
                raise cv.Invalid(f"gateway.{key} est requis par le hub et ne peut pas etre desactive")
            conf[key] = None
            continue
        merged = {CONF_NAME: spec["name"]}
        merged.update(user)
        schema = spec["schema"]()
        if spec["platform"] == "button":
            schema = schema.extend(cv.COMPONENT_SCHEMA)
        conf[key] = schema(merged)
    return conf


GATEWAY_SCHEMA = cv.All(
    cv.Schema({cv.Optional(key): _override for key in GATEWAY_ENTITIES}), _expand_gateway
)


def _check_mode(config):
    declarative = CONF_PRIMARY in config
    legacy = [key for key in LEGACY_IDS if key in config]
    if declarative and legacy:
        raise cv.Invalid(
            "Mode declaratif (primary:) : retirer les options historiques " + ", ".join(legacy)
        )
    if not declarative:
        missing = [key for key in LEGACY_IDS if key not in config]
        if missing:
            raise cv.Invalid(
                "Declarer la lampe principale avec 'primary:' (recommande), "
                "ou fournir les options historiques : " + ", ".join(missing)
            )
        if config.get(CONF_LAMPS):
            raise cv.Invalid("'lamps:' necessite le mode declaratif ('primary:')")
    addresses = [config[CONF_PRIMARY][CONF_ADDRESS]] if declarative else []
    addresses += [lamp[CONF_ADDRESS] for lamp in config.get(CONF_LAMPS, [])]
    if len(addresses) != len(set(addresses)):
        raise cv.Invalid("Deux lampes declarent la meme adresse")
    return config


CONFIG_SCHEMA = cv.All(
    cv.Schema(
        {
            cv.GenerateID(): cv.declare_id(NightmatiqMesh),
            cv.GenerateID(esp32_ble.CONF_BLE_ID): cv.use_id(esp32_ble.ESP32BLE),
            cv.GenerateID(CONF_WEB_SERVER_BASE_ID): cv.use_id(web_server_base.WebServerBase),
            cv.Required(CONF_OTA_ID): cv.use_id(esphome_ota.ESPHomeOTAComponent),
            # --- mode declaratif
            cv.Optional(CONF_PRIMARY): PRIMARY_SCHEMA,
            cv.Optional(CONF_LAMPS, default=[]): cv.All(cv.ensure_list(LAMP_SCHEMA), cv.Length(max=4)),
            cv.Optional(CONF_GROUPS, default=[]): cv.All(cv.ensure_list(cv.hex_uint16_t), cv.Length(max=4)),
            cv.Optional(CONF_STATE_GROUPS, default=[]): cv.All(
                cv.ensure_list(cv.hex_uint16_t), cv.Length(max=4)
            ),
            cv.Optional(CONF_GATEWAY, default={}): GATEWAY_SCHEMA,
            # --- mode historique
            cv.Optional(CONF_LUX_SENSOR_ID): cv.use_id(sensor.Sensor),
            cv.Optional(CONF_RSSI_SENSOR_ID): cv.use_id(sensor.Sensor),
            cv.Optional(CONF_THRESHOLD_NUMBER_ID): cv.use_id(number.Number),
            cv.Optional(CONF_MODE_SELECT_ID): cv.use_id(select.Select),
            cv.Optional(CONF_READY_BINARY_SENSOR_ID): cv.use_id(binary_sensor.BinarySensor),
            cv.Optional(CONF_ACTUAL_OUTPUT_BINARY_SENSOR_ID): cv.use_id(binary_sensor.BinarySensor),
            cv.Optional(CONF_STATUS_TEXT_SENSOR_ID): cv.use_id(text_sensor.TextSensor),
            cv.Optional(CONF_FIRMWARE_VERSION_TEXT_SENSOR_ID): cv.use_id(text_sensor.TextSensor),
            cv.Optional(CONF_HARDWARE_VERSION_SENSOR_ID): cv.use_id(sensor.Sensor),
            cv.Optional(CONF_MANUFACTURER_TEXT_SENSOR_ID): cv.use_id(text_sensor.TextSensor),
            cv.Optional(CONF_COMPANY_ID_TEXT_SENSOR_ID): cv.use_id(text_sensor.TextSensor),
            cv.Optional(CONF_PRODUCT_ID_TEXT_SENSOR_ID): cv.use_id(text_sensor.TextSensor),
            # --- commun
            cv.Optional(CONF_EXTENDED_DIAGNOSTICS, default=True): cv.boolean,
            cv.Required(CONF_WEB_USERNAME): cv.string_strict,
            cv.Required(CONF_WEB_PASSWORD): cv.sensitive(cv.string_strict),
        }
    ).extend(cv.polling_component_schema("30s")),
    _check_mode,
)


# ---------------------------------------------------------------------------
# Generation de code
# ---------------------------------------------------------------------------
async def _child(var, conf, hub, base):
    cg.add(var.set_parent(hub))
    cg.add(var.set_base(base))
    await cg.register_component(var, conf)


async def _lamp_entities(hub, lamp, primary):
    base = lamp[CONF_ADDRESS]
    hub_owned = {}
    for key, spec in ENTITIES.items():
        conf = lamp.get(key)
        if conf is None:
            continue
        platform = spec["platform"]

        if primary and key in PRIMARY_HUB_ENTITIES:
            # Entite publiee par le hub : objet ESPHome simple, rattache au hub.
            if platform == "sensor":
                var = await sensor.new_sensor(conf)
            elif platform == "binary_sensor":
                var = await binary_sensor.new_binary_sensor(conf)
            elif platform == "text_sensor":
                var = await text_sensor.new_text_sensor(conf)
            elif platform == "number":
                lo, hi, step = spec["range"]
                var = await number.new_number(conf, min_value=lo, max_value=hi, step=step)
                cg.add(var.set_parent(hub))
                await cg.register_component(var, conf)
            elif platform == "select":
                var = await select.new_select(conf, options=MODE_OPTIONS)
                cg.add(var.set_parent(hub))
                await cg.register_component(var, conf)
            hub_owned[key] = var
            continue

        if platform == "sensor":
            var = await sensor.new_sensor(conf)
            kind = {
                "illuminance": LampSensorKind.LUX,
                "signal": LampSensorKind.RSSI,
                "hardware": LampSensorKind.HARDWARE,
                "motion_level": LampSensorKind.PRIMARY_MOTION_LEVEL if primary else LampSensorKind.MOTION_LEVEL,
            }[key]
            cg.add(var.set_kind(kind))
        elif platform == "binary_sensor":
            var = await binary_sensor.new_binary_sensor(conf)
            kind = {
                "light": LampBinaryKind.OUTPUT,
                "motion": LampBinaryKind.PRIMARY_MOTION if primary else LampBinaryKind.MOTION,
            }[key]
            cg.add(var.set_kind(kind))
        elif platform == "number":
            lo, hi, step = spec["range"]
            var = await number.new_number(conf, min_value=lo, max_value=hi, step=step)
            if key == "intensity":
                cg.add(var.set_kind(LampNumberKind.LIGHTNESS))
            elif key == "threshold":
                cg.add(var.set_kind(LampNumberKind.THRESHOLD))
            else:
                cg.add(var.set_kind(LampNumberKind.LC_PROP))
                cg.add(var.set_property({"power": LC_POWER, "base_light": LC_BASE_LIGHT,
                                         "run_on": LC_RUN_ON}[key]))
        elif platform == "select":
            var = await select.new_select(conf, options=MODE_OPTIONS)
        elif platform == "text_sensor":
            var = await text_sensor.new_text_sensor(conf)
            if key == "firmware":
                cg.add(var.set_kind(LampTextKind.FIRMWARE))
            elif key == "relay_retransmit":
                cg.add(var.set_kind(LampTextKind.RELAY_RETRANSMIT))
            else:
                cg.add(var.set_kind(LampTextKind.CONSTANT))
                text = {
                    "manufacturer_text": lamp.get(CONF_MANUFACTURER, ""),
                    "company_id_text": lamp.get(CONF_COMPANY, ""),
                    "product_id_text": f"0x{lamp.get(CONF_PRODUCT_ID, 0):04x}",
                }[key]
                cg.add(var.set_constant(text))
        elif platform == "switch":
            var = await switch.new_switch(conf)
        else:
            continue
        await _child(var, conf, hub, base)
    return hub_owned


async def to_code(config):
    # ESPHome >= 2026.9 exclut ces composants ESP-IDF par defaut
    esp32.include_builtin_idf_component("esp_http_client")
    esp32.include_builtin_idf_component("json")
    if config[CONF_EXTENDED_DIAGNOSTICS]:
        cg.add_define("USE_NIGHTMATIQ_EXTENDED_DIAGNOSTICS")
    # Le relais Mesh appelle esp_ble_tx_power_set & co depuis les lambdas du YAML
    cg.add_global(cg.RawStatement("#include <esp_bt.h>"))

    base = await cg.get_variable(config[CONF_WEB_SERVER_BASE_ID])
    ota = await cg.get_variable(config[CONF_OTA_ID])
    var = cg.new_Pvariable(config[CONF_ID], base, ota)
    await cg.register_component(var, config)
    ble = await cg.get_variable(config[esp32_ble.CONF_BLE_ID])
    esp32_ble.register_gap_event_handler(ble, var)
    esp32_ble.register_gap_scan_event_handler(ble, var)
    cg.add(var.set_web_credentials(config[CONF_WEB_USERNAME], config[CONF_WEB_PASSWORD]))

    if CONF_PRIMARY not in config:
        await _legacy_to_code(var, config)
        return

    # --- topologie (remplace les add_lamp / set_lamp_* de on_boot)
    for group in config[CONF_GROUPS]:
        cg.add(var.add_group(group))
    for group in config[CONF_STATE_GROUPS]:
        cg.add(var.add_state_group(group))
    primary = config[CONF_PRIMARY]
    cg.add(var.set_primary_name(primary[CONF_NAME]))
    if CONF_TAG in primary:
        cg.add(var.set_primary_tag(primary[CONF_TAG]))
    if primary[CONF_LC_PROPS]:
        cg.add(var.add_lc_props(primary[CONF_ADDRESS]))
    if CONF_DEVICE_KEY in primary:
        cg.add(var.set_primary_device_key(primary[CONF_DEVICE_KEY]))
    for lamp in config[CONF_LAMPS]:
        address = lamp[CONF_ADDRESS]
        cg.add(var.add_lamp(address, lamp[CONF_SCENE], lamp[CONF_ELEMENTS]))
        if CONF_TAG in lamp:
            cg.add(var.set_lamp_tag(address, lamp[CONF_TAG]))
        cg.add(var.set_lamp_name(address, lamp[CONF_NAME]))
        if lamp[CONF_LC_PROPS]:
            cg.add(var.add_lc_props(address))
        if CONF_DEVICE_KEY in lamp:
            cg.add(var.set_lamp_device_key(address, lamp[CONF_DEVICE_KEY]))

    # --- entites de la passerelle
    gateway = config[CONF_GATEWAY]
    ready = await binary_sensor.new_binary_sensor(gateway["mesh_ready"])
    cg.add(var.set_ready_binary_sensor(ready))
    status = await text_sensor.new_text_sensor(gateway["status"])
    cg.add(var.set_status_text_sensor(status))
    for key, kind in (("refresh", GatewayButtonKind.REFRESH), ("relay_refresh", GatewayButtonKind.RELAY_REFRESH)):
        if gateway.get(key) is None:
            continue
        btn = await button.new_button(gateway[key])
        cg.add(btn.set_kind(kind))
        cg.add(btn.set_parent(var))
        await cg.register_component(btn, gateway[key])

    # --- entites de la lampe principale (une partie est alimentee par le hub)
    owned = await _lamp_entities(var, primary, primary=True)
    setters = {
        "illuminance": "set_lux_sensor",
        "signal": "set_rssi_sensor",
        "threshold": "set_threshold_number",
        "mode": "set_mode_select",
        "light": "set_actual_output_binary_sensor",
        "firmware": "set_firmware_version_text_sensor",
        "hardware": "set_hardware_version_sensor",
        "manufacturer_text": "set_manufacturer_text_sensor",
        "company_id_text": "set_company_id_text_sensor",
        "product_id_text": "set_product_id_text_sensor",
    }
    for key, setter in setters.items():
        if key in owned:
            cg.add(getattr(var, setter)(owned[key]))

    # --- entites des lampes supplementaires
    for lamp in config[CONF_LAMPS]:
        await _lamp_entities(var, lamp, primary=False)


async def _legacy_to_code(var, config):
    for key, setter in (
        (CONF_LUX_SENSOR_ID, "set_lux_sensor"),
        (CONF_RSSI_SENSOR_ID, "set_rssi_sensor"),
        (CONF_THRESHOLD_NUMBER_ID, "set_threshold_number"),
        (CONF_MODE_SELECT_ID, "set_mode_select"),
        (CONF_READY_BINARY_SENSOR_ID, "set_ready_binary_sensor"),
        (CONF_ACTUAL_OUTPUT_BINARY_SENSOR_ID, "set_actual_output_binary_sensor"),
        (CONF_STATUS_TEXT_SENSOR_ID, "set_status_text_sensor"),
        (CONF_FIRMWARE_VERSION_TEXT_SENSOR_ID, "set_firmware_version_text_sensor"),
        (CONF_HARDWARE_VERSION_SENSOR_ID, "set_hardware_version_sensor"),
        (CONF_MANUFACTURER_TEXT_SENSOR_ID, "set_manufacturer_text_sensor"),
        (CONF_COMPANY_ID_TEXT_SENSOR_ID, "set_company_id_text_sensor"),
        (CONF_PRODUCT_ID_TEXT_SENSOR_ID, "set_product_id_text_sensor"),
    ):
        entity = await cg.get_variable(config[key])
        cg.add(getattr(var, setter)(entity))
