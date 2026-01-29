from django.templatetags.static import static

from whitebox import import_whitebox_plugin_class
from whitebox_plugin_device_insta360.device_wizards import (
    Insta360X3Wizard,
    Insta360X4Wizard,
)


# Do not proxy as a proxy class cannot be subclassed
Device = import_whitebox_plugin_class("device.Device", proxy=False)
DeviceType = import_whitebox_plugin_class("device.DeviceType", proxy=False)


class Insta360Base(Device):
    device_type = DeviceType.CAMERA_360

    @classmethod
    def get_connection_types(cls):
        return {
            "wifi": {
                "name": "Wi-Fi",
                "fields": {
                    "ssid": {
                        "name": "Network Name",
                        "type": "text",
                        "required": True,
                    },
                    "password": {
                        "name": "Network Password",
                        "type": "password",
                        "required": True,
                    },
                },
            },
        }

    def validate_connection_settings(self, connection_type, connection_options):
        pass

    def check_connectivity(self):
        """
        Check whether the device has connection.

        Returns:
            Boolean whether the device has connection.
        """

        # TODO: Connect to WIFI, whether directly, or by controlling some kind
        #       of a relay that can connect to the device's WiFi
        #       Issue: whitebox#96
        return True


class Insta360X3(Insta360Base):
    codename = "insta360_x3"
    device_name = "Insta360 X3"
    device_image_url = static(
        "whitebox_plugin_device_insta360/insta360_x3/insta360_x3.webp",
    )
    wizard_class = Insta360X3Wizard


class Insta360X4(Insta360Base):
    codename = "insta360_x4"
    device_name = "Insta360 X4"
    device_image_url = static(
        "whitebox_plugin_device_insta360/insta360_x4/insta360_x4.webp",
    )
    wizard_class = Insta360X4Wizard
