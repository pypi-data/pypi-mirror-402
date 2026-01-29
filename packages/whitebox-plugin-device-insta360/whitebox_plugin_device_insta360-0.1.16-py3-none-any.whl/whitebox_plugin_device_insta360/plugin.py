import django_rq

from whitebox import import_whitebox_model, Plugin
from .tasks import handle_recording_for_flight_session

DeviceConnection = import_whitebox_model("device.DeviceConnection")


class WhiteboxPluginDeviceInsta360(Plugin):
    """
    A plugin that enables support for Insta360 cameras.

    Attributes:
        name: The name of the plugin.
    """

    name = "Insta360 Camera Support"
    registered = False

    def get_device_classes(self) -> list:
        # Defer loading of device classes to allow for `device-manager` to first
        # register its base classes into the class registry, as base classes
        # cannot proxied
        from whitebox_plugin_device_insta360.devices import (
            Insta360X3,
            Insta360X4,
        )

        return [Insta360X3, Insta360X4]

    def on_load(self):
        self.whitebox.register_event_callback(
            "flight.start",
            self.on_flight_start,
        )

    def on_unload(self):
        self.whitebox.unregister_event_callback(
            "flight.start",
            self.on_flight_start,
        )

    async def on_flight_start(self, data, ctx):
        flight_session = ctx["flight_session"]

        targets = [device_class.codename for device_class in self.get_device_classes()]

        # Get all devices managed by this plugin
        connection_ids = DeviceConnection.objects.filter(
            codename__in=targets,
        ).values_list("pk", flat=True)

        device_count = await connection_ids.acount()
        self.logger.info(
            f"Flight session started (ID: {flight_session.id}), "
            f"initializing {device_count} Insta360 devices...",
        )

        async for connection_id in connection_ids:
            django_rq.enqueue(
                handle_recording_for_flight_session,
                device_connection_id=connection_id,
                flight_session_id=flight_session.id,
                # RQ queue requires every job to have a timeout, and this one
                # should last for the entirety of the flight, so give it a super
                # long timeout so that it never gets interrupted mid-flight
                job_timeout="24h",
            )


plugin_class = WhiteboxPluginDeviceInsta360
