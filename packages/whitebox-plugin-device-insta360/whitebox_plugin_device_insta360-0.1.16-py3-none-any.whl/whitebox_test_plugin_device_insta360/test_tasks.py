import datetime
from pathlib import Path
from unittest.mock import Mock, patch

from django.test.testcases import TransactionTestCase

from tests.test_utils import patch_model_registry
from whitebox_plugin_device_insta360.tasks import (
    _get_client_for_device_connection,
    _handle_camera_connection_for_flight_session,
    handle_recording_for_flight_session,
    post_flight_operations,
)


class TestTasks(TransactionTestCase):
    def setUp(self):
        self.mock_device_connection = Mock()
        self.mock_device_connection.connection_settings = {
            "ip_address": "192.168.1.100",
            "port": 8080,
        }
        self.mock_device_connection.id = 1

        self.mock_flight_session = Mock()
        self.mock_flight_session.id = 1
        self.mock_flight_session.is_active = True

    @patch("logging.Logger.info")
    @patch("whitebox_plugin_device_insta360.tasks.Client")
    def test_get_client_for_device_connection(
        self,
        mock_client_class,
        _mock_log_info,
    ):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        client = _get_client_for_device_connection(self.mock_device_connection)

        mock_client_class.assert_called_once_with()
        mock_client.ensure_camera_connected.assert_called_once()
        self.assertEqual(client, mock_client)

    @patch("logging.Logger.info")
    @patch("time.sleep")
    @patch("whitebox_plugin_device_insta360.tasks.Thread")
    @patch("whitebox_plugin_device_insta360.tasks.prepare_stream_handler")
    def test_handle_camera_connection_for_flight_session(
        self,
        mock_prepare_handler,
        mock_thread_class,
        _mock_sleep,
        _mock_log_info,
    ):
        mock_client = Mock()
        mock_handler = Mock()
        mock_prepare_handler.return_value = mock_handler
        mock_thread = Mock()
        mock_thread_class.return_value = mock_thread

        # Mock flight session state changes
        self.mock_flight_session.is_active = True

        def side_effect():
            # First call returns active, second call returns inactive
            if hasattr(side_effect, "call_count"):
                side_effect.call_count += 1
            else:
                side_effect.call_count = 1
            return side_effect.call_count <= 1

        type(self.mock_flight_session).is_active = property(lambda self: side_effect())

        output_file = "/tmp/test_output.raw"

        mock_fsr = Mock()
        with patch_model_registry("flight.FlightSessionRecording", mock_fsr):
            _handle_camera_connection_for_flight_session(
                self.mock_flight_session,
                self.mock_device_connection,
                mock_client,
                output_file,
            )

        # Verify stream handler setup
        mock_prepare_handler.assert_called_once()
        mock_client.on_video_stream.assert_called_once_with(
            uid="insta360-on-flight-start-video-stream-handler"
        )

        # Verify thread creation and execution
        mock_thread_class.assert_called_once()
        mock_thread.start.assert_called_once()

        # Verify camera operations
        mock_client.start_preview_stream.assert_called_once()
        mock_client.stop_preview_stream.assert_called_once()
        mock_client.close.assert_called_once()
        mock_thread.join.assert_called_once()

    @patch("logging.Logger.info")
    @patch("django.utils.timezone.now")
    @patch("django_rq.enqueue")
    @patch("whitebox_plugin_device_insta360.tasks.Path")
    @patch(
        "whitebox_plugin_device_insta360.tasks._handle_camera_connection_for_flight_session"
    )
    @patch("whitebox_plugin_device_insta360.tasks._get_client_for_device_connection")
    @patch("whitebox_plugin_device_insta360.tasks.DeviceConnection")
    @patch("whitebox_plugin_device_insta360.tasks.FlightSession")
    def test_handle_recording_for_flight_session(
        self,
        mock_flight_session_model,
        mock_device_connection_model,
        mock_get_client,
        mock_handle_connection,
        mock_path_class,
        mock_enqueue,
        mock_timezone_now,
        _mock_log_info,
    ):
        now_value = datetime.datetime(1234, 5, 6, 7, 8, 9)
        mock_timezone_now.return_value = now_value

        mock_flight_session_model.objects.get.return_value = self.mock_flight_session
        mock_device_connection_model.objects.get.return_value = (
            self.mock_device_connection
        )
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_path = Mock()
        mock_path.exists.return_value = False
        mock_path_class.return_value = mock_path

        flight_recording_path = Path(
            "/opt/whitebox/media/flight_recordings/1_1/insta360_f1_d1_{}.mp4".format(
                now_value.isoformat().replace(":", "-").replace("T", "_")
            ),
        )

        flight_session_id = 1
        device_connection_id = 1

        handle_recording_for_flight_session(flight_session_id, device_connection_id)

        # Verify database queries
        mock_flight_session_model.objects.get.assert_called_once_with(
            id=flight_session_id,
        )
        mock_device_connection_model.objects.get.assert_called_once_with(
            id=device_connection_id,
        )

        # Verify file path operations
        mock_path_class.assert_called_once_with(flight_recording_path)
        mock_path.exists.assert_called_once()

        # Verify client operations
        mock_get_client.assert_called_once_with(self.mock_device_connection)
        mock_client.open.assert_called_once()
        mock_client.close.assert_called_once()

        # Verify connection handling
        mock_handle_connection.assert_called_once_with(
            flight_session=self.mock_flight_session,
            device_connection=self.mock_device_connection,
            client=mock_client,
            output_filename=flight_recording_path,
        )

        # Verify that the post-flight task is scheduled
        mock_enqueue.assert_called_once_with(
            post_flight_operations,
            flight_session_id=flight_session_id,
            device_connection_id=device_connection_id,
            job_timeout="24h",
        )

    @patch("whitebox_plugin_device_insta360.tasks.Path")
    @patch("whitebox_plugin_device_insta360.tasks._get_client_for_device_connection")
    def test_handle_recording_file_exists_error(self, mock_get_client, mock_path_class):
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path_class.return_value = mock_path

        mock_fs = Mock()
        mock_dc = Mock()

        with (
            patch_model_registry("flight.FlightSession", mock_fs),
            patch_model_registry("device.DeviceConnection", mock_dc),
        ):
            mock_fs.objects.get.return_value = self.mock_flight_session
            mock_dc.objects.get.return_value = self.mock_device_connection

            with self.assertRaises(ValueError) as context:
                handle_recording_for_flight_session(1, 1)

            self.assertEqual(str(context.exception), "Target file already exists")
