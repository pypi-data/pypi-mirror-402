from .str_enum import StrEnum

TIMEOUT = 5 * 60
DEVICEINFOREFRESH = (
    30 * 60
)  # Number of seconds to wait before refreshing device info as it doesn't change very often

OAUTH_SCOPE = "api://f0ea23e1-8533-44ab-8592-509cff0774da/.default"
OAUTH_GRANT_TYPE = "client_credentials"

AUTH_ERROR_CODES = [
    "unauthorized_client",
    "Login session expired.",
]

INVERTER_MODES = [
    "Auto",
    "ChargeBattery",
    "DischargeBattery",
    "ImportPower",
    "ExportPower",
    "Conserve",
    "Offgrid",
    "Hibernate",
    "BuyPower",
    "SellPower",
    "ForceChargeBattery",
    "ForceDischargeBattery",
]

INVERTER_PORTAL_MODES = [
    "Auto",
    "ChargeBattery",
    "DischargeBattery",
    "ImportPower",
    "ExportPower",
    "Conserve",
]


class BaseUrl(StrEnum):
    OAUTH = "https://login.microsoftonline.com/"
    API = "https://api.redbacktech.com/"
    PORTAL = "https://portal.redbacktech.com/"


class Endpoint(StrEnum):
    API_OAUTH = "fb46c16c-9144-45e0-87b7-f578abed629f/oauth2/v2.0/token"
    API_AUTH = "Api/v2/Auth/token"
    API_SITES = "Api/v2/EnergyData"
    API_NODES = "Api/v2/EnergyData/With/Nodes"
    API_STATIC = "Api/v2/EnergyData/{self.siteId}/Static"
    API_STATIC_MULTIPLE_BY_SERIAL = (
        "Api/v2/Configuration/Multiple/BySerialNumber/Configuration"
    )
    API_CONFIG_BY_SERIAL = "Api/v2/Configuration/Configuration/BySerialNumber/"
    API_STATIC_BY_SERIAL = "Api/v2/EnergyData/Static/BySerialNumber/"
    API_ENERGY_DYNAMIC_MULTIPLE_BY_SERIAL = (
        "Api/v2.21/EnergyData/Multiple/BySerialNumber/Dynamic"
    )
    API_ENERGY_DYNAMIC_BY_SERIAL = "Api/v2.21/EnergyData/Dynamic/BySerialNumber/"
    API_ENERGY_DYNAMIC_BY_SITE = "Api/v2.21/EnergyData/{self.siteId}/Dynamic"
    API_SCHEDULE_CREATE = "Api/v2/Schedule/Create/By/SerialNumber"
    API_SCHEDULE_DELETE = (
        "Api/v2/Schedule/Delete/By/SerialNumber/"  # {serialNumber}/{scheduleId}
    )
    API_SCHEDULE_GET = "Api/v2/Schedule/By/SerialNumber/"  # {serialNumber}
    API_OPENVELOPE_DELETE_ALL = "Api/v2/OperatingEnvelope/All"
    API_OPENVELOPE_BY_EVENTID = (
        "Api/v2/OperatingEnvelope/By/EventId/"  # {eventId} DELETE & GET
    )
    API_OPENVELOPE_CREATE = "Api/v2/OperatingEnvelope/Create/By/Site"
    API_OPENVELOPE_BY_SITE_ALL = "Api/v2/OperatingEnvelope/By/Site/"  # {siteId}
    PORTAL_LOGIN = "Account/Login"
    PORTAL_CONFIGURE = "productcontrol/Configure?serialNumber="
    PORTAL_INVERTER_SET = "productcontrol/Index"
    PORTAL_LOGOFF = "Account/LogOff/"
    PORTAL_DETAILS = "productcontrol/Details?serialNumber="
    PORTAL_INSTALLATION_DETAILS = "installationdetails/Configure?serialNumber="
    API_SCHEDULE_BY_SERIALNUMBER = "Api/v2/Schedule/By/SerialNumber/"
    API_SCHEDULE_CREATE_BY_SERIALNUMBER = "Api/v2/Schedule/Create/By/SerialNumber/"
    API_SCHEDULE_DELETE_BY_SERIALNUMBER_SCHEDULEID = (
        "Api/v2/Schedule/By/SerialNumber/"  # {serialNumber}/{scheduleId}
    )


class InverterOperationType(StrEnum):
    SET = "Set"


class InverterModeControl(StrEnum):
    AUTO = "Auto"
    CHARGE_BATTERY = "ChargeBattery"
    DISCHARGE_BATTERY = "DischargeBattery"
    IMPORT_POWER = "ImportPower"
    EXPORT_POWER = "ExportPower"
    CONSERVE = "Conserve"


class Header(StrEnum):
    ACCEPT = "*/*"
    ENCODING = "gzip, deflate"
    CONTENT_TYPE = "application/x-www-form-urlencoded; charset=UTF-8"
    X_REQUESTED_WITH = "XMLHttpRequest"
    REFERER_UI = "https://portal.redbacktech.com/ui/"


class DeviceTypes(StrEnum):
    INVERTER = "Inverter"
    BATTERY = "Battery"
    METER = "Meter"
    LOAD = "Load"


class DeviceInfo(StrEnum):
    MODEL = "model"
    SW_VERSION = "sw_version"
    HW_VERSION = "hw_version"
    SERIAL_NUMBER = "serial_number"


PORTAL_SCHEDULE_CREATE_FORM = {
    "schedule[Mode]": "",  #'ChargeBattery'
    "schedule[PowerInWatts]": 0,  # 10000,
    "schedule[StartTIme]": "",  #'2024-06-16T03:00:00Z',
    "schedule[EndTime]": "",  #'2024-06-16T03:15:00Z',
    "schedule[IsRecurreingDaily]": "",  #'true',
    "schedule[Date]": "",  # Blank if recurring
    "schedule[ModeDisplay]": "",  #'Charge Battery',
    "schedule[Timezone]": "",  #'Australia/Brisbane',
    "_RequestVerificationToken": "",  #'sdfsdf'
}
