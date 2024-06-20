"""
This file contains the class Device. 
The Device class is the class that the the device_executer receives.
"""
import dataclasses
from enum import Enum
from typing import Dict, Tuple, Optional, Any

from networkcommander.config import config


@dataclasses.dataclass(frozen=True, order=True)
class Device:
    """
    netmiko.ConnectHandler takes in a lot of arguments that change from execution to execution.
    this class is here to hold the data netmiko.ConnectHandler needs to run par device.
    """
    name: str
    username: str
    password: str
    host: str
    device_type: str
    optional_parameters: Dict[str, str]

    def __str__(self):
        device_string = ''
        if self.name:
            device_string += self.name
        if self.device_type:
            device_string += f'({str(self.device_type)})'
        if device_string:
            device_string += ' -> '
        device_string += self.get_ssh_string()
        return device_string

    def get_ssh_string(self):
        """
        this function takes the data in the class and convert it to a valid ssh string.
        example -
            Device(host="google", username="root", port="22"...).get_ssh_string()
            root@google:22
        then you can use it with ssh command to connect to the remote device.
        example - ssh root@google:22

        :return: an ssh string (username@{ip/hostname}:port)
        """
        ssh_string = ""

        if self.username:
            ssh_string += f"{self.username}@"

        ssh_string += self.host

        if 'port' in self.optional_parameters:
            ssh_string += f":{self.optional_parameters['port']}"

        return ssh_string

    @property
    def device_options(self) -> Dict[str, str]:
        """
        this property convert the data in this class to
        arguments netmiko.ConnectionHandler() can accept.
        example - netmiko.ConnectionHandler(**device.device_options).
        :return: a dictionary containing the arguments netmiko.ConnectionHandler() needs to run
        """
        return {
            "username": self.username,
            "password": self.password,
            "host": self.host,
            "device_type": self.device_type,
            **self.optional_parameters
        }


def device_from_string(
    device: str,
    password: str = "",
    optional_parameters: Optional[Dict[str, Any]] = None
):
    """
    this function convert a string in the format:
        {name}({device_type}) -> {username}@{hostname}:{port}
    to a Device.
    also you can add to the device some optional parameters
    :param optional_parameters: any optional parameters like 'secret'(enable secret)
    :param password: the password for the device
    :param device: a string representing a device in this format
    {name}({device_type}) -> {username}@{hostname}:{port}
    :return: a device
    """
    if optional_parameters is None:
        optional_parameters = {}

    if not device:
        raise ValueError("you can't have an empty device")
    device = device.strip(' \n')
    device_descriptor, connection_string = deconstruct_device(device)
    username, hostname, port = deconstruct_connection_string(connection_string)
    device_type = None
    if device_descriptor:
        name, device_type = deconstruct_device_descriptor(device_descriptor)
    else:
        name = hostname
    if not device_type:
        device_type = config["default_device_type"]

    if not username:
        username = ""
    if not password:
        password = ""

    if port:
        optional_parameters["port"] = str(port)
    return Device(name, username, password, hostname, device_type, optional_parameters)


def deconstruct_device_descriptor(device_descriptor: str) -> Tuple[str, Optional[str]]:
    """
    split the device descriptor and return the name and os type of it
    :param device_descriptor: is a device and possibly the os type of it.
    for example: r1(cisco_ios)

    :return: the device's name and the os type.
    for example: 'r1', 'cisco_ios'
    """
    is_supported_device = any(
        (f'({str(device_type.value)})' in device_descriptor for device_type in DeviceType)
    )
    if is_supported_device:
        name, device_type = device_descriptor.split('(')
        device_type = device_type.rstrip(')')
        return name, device_type

    return device_descriptor, None


def deconstruct_device(device: str):
    """
    split a device string to a device descriptor and a connection string.


    :param device: a string with the connection information for the device.
    for example: "r1(cisco_ios) -> root@google.com:22"

    :return: a tuple with a device descriptor and a connection string.
    for example: ('r1(cisco_ios)', 'root@google.com:22')
    """
    if device.count('->') > 1:
        raise ValueError(f"{device} has more then 1 '->'")
    if device.count('\n') > 1:
        raise ValueError(f"device {device} shouldn't have a line break.")
    if '->' in device:
        device_descriptor, connection_string = device.split('->')
        device_descriptor = device_descriptor.strip()
        connection_string = connection_string.strip()
        return device_descriptor, connection_string
    connection_string: str = device
    return None, connection_string


def deconstruct_socket_id(socket_id: str) -> Tuple[str, int]:
    """
    this function returns the variables contained inside an IPv4 socket_id
    :param socket_id: a hostname or ip (IPv4) with a port,
        like: 1.1.1.1:234, 12312:22, google.com:5000
    :raise: ValueError if the socket_id is not a real one or doesn't contain a port
     (for example, kjnjsl::: is not a valid socket id)
    :return: the hostname or ip address and port number
    """
    if socket_id.count(':') != 1:
        raise ValueError(
            f"{socket_id} is not a valid IPv4 socket id, it has more then 1 ':'."
        )
    hostname, port = socket_id.split(':')
    if not port or not port.isnumeric():
        raise ValueError(f"{socket_id} doesn't contain a valid port number")
    port = int(port)
    if 0 > port or port > 65535:
        raise ValueError(f"{port} is not in the valid port range")

    return hostname, port


class DeviceType(str, Enum):
    """
    An Enum to represent the device types netmiko supports.
    USE AT YOUR OWN CAUTION, NOT EVERY DEVICE IN THIS LIST WAS TESTED!
    """

    A10 = "a10"
    A10_TELNET = "a10_telnet"
    ACCEDIAN = "accedian"
    ACCEDIAN_TELNET = "accedian_telnet"
    ADTRAN_OS = "adtran_os"
    ADTRAN_OS_TELNET = "adtran_os_telnet"
    ADVA_FSP150F2 = "adva_fsp150f2"
    ADVA_FSP150F2_TELNET = "adva_fsp150f2_telnet"
    ADVA_FSP150F3 = "adva_fsp150f3"
    ADVA_FSP150F3_TELNET = "adva_fsp150f3_telnet"
    ALCATEL_AOS = "alcatel_aos"
    ALCATEL_AOS_TELNET = "alcatel_aos_telnet"
    ALCATEL_SROS = "alcatel_sros"
    ALCATEL_SROS_TELNET = "alcatel_sros_telnet"
    ALLIED_TELESIS_AWPLUS = "allied_telesis_awplus"
    ALLIED_TELESIS_AWPLUS_TELNET = "allied_telesis_awplus_telnet"
    APRESIA_AEOS = "apresia_aeos"
    APRESIA_AEOS_TELNET = "apresia_aeos_telnet"
    ARISTA_EOS = "arista_eos"
    ARISTA_EOS_TELNET = "arista_eos_telnet"
    ARRIS_CER = "arris_cer"
    ARRIS_CER_TELNET = "arris_cer_telnet"
    ARUBA_OS = "aruba_os"
    ARUBA_OS_TELNET = "aruba_os_telnet"
    ARUBA_OSSWITCH = "aruba_osswitch"
    ARUBA_OSSWITCH_TELNET = "aruba_osswitch_telnet"
    ARUBA_PROCURVE = "aruba_procurve"
    ARUBA_PROCURVE_TELNET = "aruba_procurve_telnet"
    AUDIOCODE_66 = "audiocode_66"
    AUDIOCODE_66_TELNET = "audiocode_66_telnet"
    AUDIOCODE_72 = "audiocode_72"
    AUDIOCODE_72_TELNET = "audiocode_72_telnet"
    AUDIOCODE_SHELL = "audiocode_shell"
    AUDIOCODE_SHELL_TELNET = "audiocode_shell_telnet"
    AVAYA_ERS = "avaya_ers"
    AVAYA_ERS_TELNET = "avaya_ers_telnet"
    AVAYA_VSP = "avaya_vsp"
    AVAYA_VSP_TELNET = "avaya_vsp_telnet"
    BROADCOM_ICOS = "broadcom_icos"
    BROADCOM_ICOS_TELNET = "broadcom_icos_telnet"
    BROCADE_FASTIRON = "brocade_fastiron"
    BROCADE_FASTIRON_TELNET = "brocade_fastiron_telnet"
    BROCADE_FOS = "brocade_fos"
    BROCADE_FOS_TELNET = "brocade_fos_telnet"
    BROCADE_NETIRON = "brocade_netiron"
    BROCADE_NETIRON_TELNET = "brocade_netiron_telnet"
    BROCADE_NOS = "brocade_nos"
    BROCADE_NOS_TELNET = "brocade_nos_telnet"
    BROCADE_VDX = "brocade_vdx"
    BROCADE_VDX_TELNET = "brocade_vdx_telnet"
    BROCADE_VYOS = "brocade_vyos"
    BROCADE_VYOS_TELNET = "brocade_vyos_telnet"
    CALIX_B6 = "calix_b6"
    CALIX_B6_TELNET = "calix_b6_telnet"
    CASA_CMTS = "casa_cmts"
    CASA_CMTS_TELNET = "casa_cmts_telnet"
    CDOT_CROS = "cdot_cros"
    CDOT_CROS_TELNET = "cdot_cros_telnet"
    CENTEC_OS = "centec_os"
    CENTEC_OS_TELNET = "centec_os_telnet"
    CHECKPOINT_GAIA = "checkpoint_gaia"
    CHECKPOINT_GAIA_TELNET = "checkpoint_gaia_telnet"
    CIENA_SAOS = "ciena_saos"
    CIENA_SAOS_TELNET = "ciena_saos_telnet"
    CISCO_ASA = "cisco_asa"
    CISCO_ASA_TELNET = "cisco_asa_telnet"
    CISCO_FTD = "cisco_ftd"
    CISCO_FTD_TELNET = "cisco_ftd_telnet"
    CISCO_IOS = "cisco_ios"
    CISCO_IOS_TELNET = "cisco_ios_telnet"
    CISCO_NXOS = "cisco_nxos"
    CISCO_NXOS_TELNET = "cisco_nxos_telnet"
    CISCO_S200 = "cisco_s200"
    CISCO_S200_TELNET = "cisco_s200_telnet"
    CISCO_S300 = "cisco_s300"
    CISCO_S300_TELNET = "cisco_s300_telnet"
    CISCO_TP = "cisco_tp"
    CISCO_TP_TELNET = "cisco_tp_telnet"
    CISCO_VIPTELA = "cisco_viptela"
    CISCO_VIPTELA_TELNET = "cisco_viptela_telnet"
    CISCO_WLC = "cisco_wlc"
    CISCO_WLC_TELNET = "cisco_wlc_telnet"
    CISCO_XE = "cisco_xe"
    CISCO_XE_TELNET = "cisco_xe_telnet"
    CISCO_XR = "cisco_xr"
    CISCO_XR_TELNET = "cisco_xr_telnet"
    CLOUDGENIX_ION = "cloudgenix_ion"
    CLOUDGENIX_ION_TELNET = "cloudgenix_ion_telnet"
    CORIANT = "coriant"
    CORIANT_TELNET = "coriant_telnet"
    DELL_DNOS9 = "dell_dnos9"
    DELL_DNOS9_TELNET = "dell_dnos9_telnet"
    DELL_FORCE10 = "dell_force10"
    DELL_FORCE10_TELNET = "dell_force10_telnet"
    DELL_ISILON = "dell_isilon"
    DELL_ISILON_TELNET = "dell_isilon_telnet"
    DELL_OS10 = "dell_os10"
    DELL_OS10_TELNET = "dell_os10_telnet"
    DELL_OS6 = "dell_os6"
    DELL_OS6_TELNET = "dell_os6_telnet"
    DELL_OS9 = "dell_os9"
    DELL_OS9_TELNET = "dell_os9_telnet"
    DELL_POWERCONNECT = "dell_powerconnect"
    DELL_POWERCONNECT_TELNET = "dell_powerconnect_telnet"
    DELL_SONIC = "dell_sonic"
    DELL_SONIC_TELNET = "dell_sonic_telnet"
    DIGI_TRANSPORT = "digi_transport"
    DIGI_TRANSPORT_TELNET = "digi_transport_telnet"
    DLINK_DS = "dlink_ds"
    DLINK_DS_TELNET = "dlink_ds_telnet"
    ELTEX = "eltex"
    ELTEX_TELNET = "eltex_telnet"
    ELTEX_ESR = "eltex_esr"
    ELTEX_ESR_TELNET = "eltex_esr_telnet"
    ENDACE = "endace"
    ENDACE_TELNET = "endace_telnet"
    ENTERASYS = "enterasys"
    ENTERASYS_TELNET = "enterasys_telnet"
    ERICSSON_IPOS = "ericsson_ipos"
    ERICSSON_IPOS_TELNET = "ericsson_ipos_telnet"
    ERICSSON_MLTN63 = "ericsson_mltn63"
    ERICSSON_MLTN63_TELNET = "ericsson_mltn63_telnet"
    ERICSSON_MLTN66 = "ericsson_mltn66"
    ERICSSON_MLTN66_TELNET = "ericsson_mltn66_telnet"
    EXTREME = "extreme"
    EXTREME_TELNET = "extreme_telnet"
    EXTREME_ERS = "extreme_ers"
    EXTREME_ERS_TELNET = "extreme_ers_telnet"
    EXTREME_EXOS = "extreme_exos"
    EXTREME_EXOS_TELNET = "extreme_exos_telnet"
    EXTREME_NETIRON = "extreme_netiron"
    EXTREME_NETIRON_TELNET = "extreme_netiron_telnet"
    EXTREME_NOS = "extreme_nos"
    EXTREME_NOS_TELNET = "extreme_nos_telnet"
    EXTREME_SLX = "extreme_slx"
    EXTREME_SLX_TELNET = "extreme_slx_telnet"
    EXTREME_TIERRA = "extreme_tierra"
    EXTREME_TIERRA_TELNET = "extreme_tierra_telnet"
    EXTREME_VDX = "extreme_vdx"
    EXTREME_VDX_TELNET = "extreme_vdx_telnet"
    EXTREME_VSP = "extreme_vsp"
    EXTREME_VSP_TELNET = "extreme_vsp_telnet"
    EXTREME_WING = "extreme_wing"
    EXTREME_WING_TELNET = "extreme_wing_telnet"
    F5_LINUX = "f5_linux"
    F5_LINUX_TELNET = "f5_linux_telnet"
    F5_LTM = "f5_ltm"
    F5_LTM_TELNET = "f5_ltm_telnet"
    F5_TMSH = "f5_tmsh"
    F5_TMSH_TELNET = "f5_tmsh_telnet"
    FIBERSTORE_FSOS = "fiberstore_fsos"
    FIBERSTORE_FSOS_TELNET = "fiberstore_fsos_telnet"
    FLEXVNF = "flexvnf"
    FLEXVNF_TELNET = "flexvnf_telnet"
    FORTINET = "fortinet"
    FORTINET_TELNET = "fortinet_telnet"
    GENERIC = "generic"
    GENERIC_TELNET = "generic_telnet"
    HILLSTONE_STONEOS = "hillstone_stoneos"
    HILLSTONE_STONEOS_TELNET = "hillstone_stoneos_telnet"
    HP_COMWARE = "hp_comware"
    HP_COMWARE_TELNET = "hp_comware_telnet"
    HP_PROCURVE = "hp_procurve"
    HP_PROCURVE_TELNET = "hp_procurve_telnet"
    HUAWEI = "huawei"
    HUAWEI_TELNET = "huawei_telnet"
    HUAWEI_OLT = "huawei_olt"
    HUAWEI_OLT_TELNET = "huawei_olt_telnet"
    HUAWEI_SMARTAX = "huawei_smartax"
    HUAWEI_SMARTAX_TELNET = "huawei_smartax_telnet"
    HUAWEI_VRP = "huawei_vrp"
    HUAWEI_VRP_TELNET = "huawei_vrp_telnet"
    HUAWEI_VRPV8 = "huawei_vrpv8"
    HUAWEI_VRPV8_TELNET = "huawei_vrpv8_telnet"
    IPINFUSION_OCNOS = "ipinfusion_ocnos"
    IPINFUSION_OCNOS_TELNET = "ipinfusion_ocnos_telnet"
    JUNIPER = "juniper"
    JUNIPER_TELNET = "juniper_telnet"
    JUNIPER_JUNOS = "juniper_junos"
    JUNIPER_JUNOS_TELNET = "juniper_junos_telnet"
    JUNIPER_SCREENOS = "juniper_screenos"
    JUNIPER_SCREENOS_TELNET = "juniper_screenos_telnet"
    KEYMILE = "keymile"
    KEYMILE_TELNET = "keymile_telnet"
    KEYMILE_NOS = "keymile_nos"
    KEYMILE_NOS_TELNET = "keymile_nos_telnet"
    LINUX = "linux"
    LINUX_TELNET = "linux_telnet"
    MAIPU = "maipu"
    MAIPU_TELNET = "maipu_telnet"
    MELLANOX = "mellanox"
    MELLANOX_TELNET = "mellanox_telnet"
    MELLANOX_MLNXOS = "mellanox_mlnxos"
    MELLANOX_MLNXOS_TELNET = "mellanox_mlnxos_telnet"
    MIKROTIK_ROUTEROS = "mikrotik_routeros"
    MIKROTIK_ROUTEROS_TELNET = "mikrotik_routeros_telnet"
    MIKROTIK_SWITCHOS = "mikrotik_switchos"
    MIKROTIK_SWITCHOS_TELNET = "mikrotik_switchos_telnet"
    MRV_LX = "mrv_lx"
    MRV_LX_TELNET = "mrv_lx_telnet"
    MRV_OPTISWITCH = "mrv_optiswitch"
    MRV_OPTISWITCH_TELNET = "mrv_optiswitch_telnet"
    NETAPP_CDOT = "netapp_cdot"
    NETAPP_CDOT_TELNET = "netapp_cdot_telnet"
    NETGEAR_PROSAFE = "netgear_prosafe"
    NETGEAR_PROSAFE_TELNET = "netgear_prosafe_telnet"
    NETSCALER = "netscaler"
    NETSCALER_TELNET = "netscaler_telnet"
    NOKIA_SRL = "nokia_srl"
    NOKIA_SRL_TELNET = "nokia_srl_telnet"
    NOKIA_SROS = "nokia_sros"
    NOKIA_SROS_TELNET = "nokia_sros_telnet"
    ONEACCESS_ONEOS = "oneaccess_oneos"
    ONEACCESS_ONEOS_TELNET = "oneaccess_oneos_telnet"
    OVS_LINUX = "ovs_linux"
    OVS_LINUX_TELNET = "ovs_linux_telnet"
    PALOALTO_PANOS = "paloalto_panos"
    PALOALTO_PANOS_TELNET = "paloalto_panos_telnet"
    PLURIBUS = "pluribus"
    PLURIBUS_TELNET = "pluribus_telnet"
    QUANTA_MESH = "quanta_mesh"
    QUANTA_MESH_TELNET = "quanta_mesh_telnet"
    RAD_ETX = "rad_etx"
    RAD_ETX_TELNET = "rad_etx_telnet"
    RAISECOM_ROAP = "raisecom_roap"
    RAISECOM_ROAP_TELNET = "raisecom_roap_telnet"
    RUCKUS_FASTIRON = "ruckus_fastiron"
    RUCKUS_FASTIRON_TELNET = "ruckus_fastiron_telnet"
    RUIJIE_OS = "ruijie_os"
    RUIJIE_OS_TELNET = "ruijie_os_telnet"
    SIXWIND_OS = "sixwind_os"
    SIXWIND_OS_TELNET = "sixwind_os_telnet"
    SOPHOS_SFOS = "sophos_sfos"
    SOPHOS_SFOS_TELNET = "sophos_sfos_telnet"
    SUPERMICRO_SMIS = "supermicro_smis"
    SUPERMICRO_SMIS_TELNET = "supermicro_smis_telnet"
    TELDAT_CIT = "teldat_cit"
    TELDAT_CIT_TELNET = "teldat_cit_telnet"
    TPLINK_JETSTREAM = "tplink_jetstream"
    TPLINK_JETSTREAM_TELNET = "tplink_jetstream_telnet"
    UBIQUITI_EDGE = "ubiquiti_edge"
    UBIQUITI_EDGE_TELNET = "ubiquiti_edge_telnet"
    UBIQUITI_EDGEROUTER = "ubiquiti_edgerouter"
    UBIQUITI_EDGEROUTER_TELNET = "ubiquiti_edgerouter_telnet"
    UBIQUITI_EDGESWITCH = "ubiquiti_edgeswitch"
    UBIQUITI_EDGESWITCH_TELNET = "ubiquiti_edgeswitch_telnet"
    UBIQUITI_UNIFISWITCH = "ubiquiti_unifiswitch"
    UBIQUITI_UNIFISWITCH_TELNET = "ubiquiti_unifiswitch_telnet"
    VYATTA_VYOS = "vyatta_vyos"
    VYATTA_VYOS_TELNET = "vyatta_vyos_telnet"
    VYOS = "vyos"
    VYOS_TELNET = "vyos_telnet"
    WATCHGUARD_FIREWARE = "watchguard_fireware"
    WATCHGUARD_FIREWARE_TELNET = "watchguard_fireware_telnet"
    YAMAHA = "yamaha"
    YAMAHA_TELNET = "yamaha_telnet"
    ZTE_ZXROS = "zte_zxros"
    ZTE_ZXROS_TELNET = "zte_zxros_telnet"
    ZYXEL_OS = "zyxel_os"
    ZYXEL_OS_TELNET = "zyxel_os_telnet"

    def __str__(self):
        return self.value


def deconstruct_connection_string(connection: str) -> Tuple[Optional[str], str, Optional[int]]:
    """
    this function extracts the variables of an ssh connection string from the string.
    :param connection: a string representing a session with a remote device
    (example: root@google.com:22, alice@exemple.com, YouTube.com:5000, 1.1.1.1)
    :return: username, hostname, port
    :raises: ValueError if the connection string is invalid
    """
    if connection.count('@') > 1:
        raise ValueError(
            f"{connection} is not a valid ssh connection string, it has more then 1 '@'."
        )

    # extract username and socket_id from connection
    if '@' in connection:
        username, socket_id = connection.split('@')

        if not username:
            username = None

    else:
        socket_id = connection
        username = None

    # extract hostname and port from socket_id
    port = None

    if socket_id[-1] == ':':
        hostname = socket_id.rstrip(':')
    elif ':' in socket_id and not socket_id[-1] == ':':
        hostname, port = deconstruct_socket_id(socket_id)
    else:
        hostname = socket_id

    # return the connection variables
    return username, hostname, port
