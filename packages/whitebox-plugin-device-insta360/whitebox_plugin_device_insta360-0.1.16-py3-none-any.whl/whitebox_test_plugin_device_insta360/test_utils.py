import struct
import asyncio
import queue
import subprocess
import threading
import time
from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock, patch, mock_open, MagicMock

from whitebox_plugin_device_insta360.utils import (
    VideoQueueProcessor,
    _prepare_ffmpeg_command,
    start_ffmpeg_process,
    prepare_stream_handler,
    _base_video_stream_handler,
    _send_to_frontend,
    _readable,
    _parse_box_len,
)


class TestUtils(TestCase):
    def test_prepare_ffmpeg_command_with_input_file(self):
        command = _prepare_ffmpeg_command(
            input_file="/tmp/input.h264",
            output_file="/tmp/output.mp4",
            width=1920,
            height=1080,
        )

        command_line = " ".join(command)

        self.assertIn("/tmp/input.h264", command_line)
        self.assertIn("scale=1920:1080", command_line)
        self.assertIn("ffmpeg", command_line)

    def test_prepare_ffmpeg_command_with_stdin(self):
        command = _prepare_ffmpeg_command(
            input_stdin=True, output_stdout=True, width=1440, height=720
        )

        command_line = " ".join(command)

        self.assertIn("pipe:0", command_line)
        self.assertIn("pipe:1", command_line)
        self.assertIn("scale=1440:720", command_line)

    def test_prepare_ffmpeg_command_validation(self):
        # Test missing input
        with self.assertRaises(ValueError):
            _prepare_ffmpeg_command(output_file="/tmp/output.mp4")

        # Test missing output
        with self.assertRaises(ValueError):
            _prepare_ffmpeg_command(input_file="/tmp/input.h264")

        # Test conflicting inputs
        with self.assertRaises(ValueError):
            _prepare_ffmpeg_command(
                input_file="/tmp/input.h264",
                input_stdin=True,
                output_file="/tmp/output.mp4",
            )

    @patch("logging.Logger.info")
    @patch("subprocess.Popen")
    def test_start_ffmpeg_process(self, mock_popen, _mock_log_info):
        mock_process = Mock()
        mock_popen.return_value = mock_process

        process = start_ffmpeg_process(input_stdin=True, output_stdout=True)

        self.assertEqual(process, mock_process)
        mock_popen.assert_called_once()

        # Verify subprocess.PIPE is used for stdin and stdout
        args, kwargs = mock_popen.call_args
        self.assertEqual(kwargs["stdin"], subprocess.PIPE)
        self.assertEqual(kwargs["stdout"], subprocess.PIPE)
        self.assertEqual(kwargs["stderr"], subprocess.PIPE)

    def test_prepare_stream_handler(self):
        test_queue = queue.Queue()
        handler = prepare_stream_handler(test_queue)

        # Test that handler is callable
        self.assertTrue(callable(handler))

    @patch("queue.Queue")
    def test_base_video_stream_handler(self, mock_queue_class):
        mock_queue = Mock()
        test_content = b"test video data"

        # Test the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                _base_video_stream_handler(test_content, mock_queue),
            )
            mock_queue.put.assert_called_once_with(test_content)
        finally:
            loop.close()

    @patch("whitebox_plugin_device_insta360.utils.async_to_sync")
    @patch("whitebox_plugin_device_insta360.utils.channel_layer")
    def test_send_to_frontend(self, mock_channel_layer, mock_async_to_sync):
        mock_send = Mock()
        mock_async_to_sync.return_value = mock_send

        test_content = b"test content"
        _send_to_frontend("test.type", test_content)

        mock_async_to_sync.assert_called_once_with(mock_channel_layer.group_send)
        mock_send.assert_called_once_with(
            "video_stream",
            {
                "type": "test.type",
                "content": test_content,
            },
        )

    @patch("select.select")
    def test_readable(self, mock_select):
        mock_fp = Mock()

        # Test readable case
        mock_select.return_value = ([mock_fp], [], [])
        self.assertTrue(_readable(mock_fp))

        # Test not readable case
        mock_select.return_value = ([], [], [])
        self.assertFalse(_readable(mock_fp))

        # Test exception case
        mock_select.side_effect = Exception("Select error")
        self.assertFalse(_readable(mock_fp))

    def test_parse_box_len(self):
        # Create test data with ftyp box
        box_data = struct.pack(">I", 32) + b"ftyp" + b"x" * 24
        mv = memoryview(box_data)

        result = _parse_box_len(mv, 0)
        self.assertIsNotNone(result)
        size, typ = result
        self.assertEqual(size, 32)
        self.assertEqual(typ, "ftyp")

        # Test insufficient data
        short_data = struct.pack(">I", 32) + b"fty"  # incomplete
        mv_short = memoryview(short_data)
        result = _parse_box_len(mv_short, 0)
        self.assertIsNone(result)


class TestVideoQueueProcessor(TestCase):
    def setUp(self):
        self.stop_event = threading.Event()
        self.test_queue = queue.Queue()
        self.processor = VideoQueueProcessor(
            self.stop_event,
            self.test_queue,
            stream_to_websocket=True,
        )

    @patch("time.time")
    @patch("whitebox_plugin_device_insta360.utils._send_to_frontend")
    def test_maybe_resend_init_segment(self, mock_send, mock_time):
        self.processor.stream_to_websocket = True
        self.processor._fmp4_state = state = {
            "init_segment": b"test init segment",
            "last_init_sent": 7.0,  # 3 seconds ago
        }

        mock_time.return_value = 10.0

        self.processor._maybe_resend_init_segment()

        mock_send.assert_called_once_with("stream.init", b"test init segment")
        self.assertEqual(state["last_init_sent"], 10.0)

    @patch("logging.Logger.info")
    @patch("os.set_blocking")
    @patch("whitebox_plugin_device_insta360.utils.start_ffmpeg_process")
    def test_process_stream_basic(
        self,
        mock_start_ffmpeg,
        mock_set_blocking,
        _mock_log_info,
    ):
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_process.stdin = Mock()
        mock_process.stdout = Mock()
        mock_process.stderr = Mock()
        mock_start_ffmpeg.return_value = mock_process

        output_file = Path("/tmp/test_output.mp4")

        # Add some test data and then stop
        test_content = b"test video data"
        self.test_queue.put(test_content)

        # Set stop event after a short delay to prevent infinite loop
        def stop_after_delay():
            time.sleep(0.1)
            self.stop_event.set()

        stop_thread = threading.Thread(target=stop_after_delay)
        stop_thread.start()

        self.processor._ffmpeg_process = mock_process
        self.processor.stream_to_websocket = True
        self.processor.save_to_file = output_file

        with (
            patch("builtins.open", mock_open()) as mock_file,
            patch(
                "whitebox_plugin_device_insta360.utils.VideoQueueProcessor._drain_fmp4"
            ),
        ):
            self.processor.run()

            # Verify file writing
            mock_file.assert_called()

            # Verify FFmpeg process setup
            mock_start_ffmpeg.assert_called_once()
            mock_set_blocking.assert_called()

        stop_thread.join()

    @patch("logging.Logger.info")
    @patch("os.set_blocking")
    @patch("whitebox_plugin_device_insta360.utils.start_ffmpeg_process")
    def test_process_stream_without_stream_to_websocket(
        self,
        mock_start_ffmpeg,
        _mock_set_blocking,
        _mock_log_info,
    ):
        test_content = b"test video data"

        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_start_ffmpeg.return_value = mock_process

        output_file = Path("/tmp/test_output.mp4")
        raw_output_file = output_file.with_suffix(".raw")

        self.test_queue.put(test_content)

        # Set stop event after a short delay to allow processing
        def stop_after_delay():
            time.sleep(0.05)  # Short delay to allow queue processing
            self.stop_event.set()

        stop_thread = threading.Thread(target=stop_after_delay)
        stop_thread.start()

        self.processor.stream_to_websocket = False
        self.processor._ffmpeg_process = mock_process
        self.processor.save_to_file = output_file
        self.processor.save_to_file_raw = True

        with patch("builtins.open", mock_open()) as mock_file:
            self.processor.run()

            # Should write to file when data is available
            mock_file.assert_called_with(raw_output_file, "wb")
            # Verify write was called with the test content
            handle = mock_file.return_value.__enter__.return_value
            handle.write.assert_called_with(test_content)

        stop_thread.join()

    @patch("logging.Logger.info")
    @patch("os.read")
    @patch("whitebox_plugin_device_insta360.utils._readable")
    @patch("whitebox_plugin_device_insta360.utils._send_to_frontend")
    def test_drain_fmp4_init_segment(
        self,
        mock_send,
        mock_readable,
        mock_read,
        _mock_log_info,
    ):
        # Mock FFmpeg process
        mock_process = Mock()
        mock_process.stdout = Mock()
        mock_process.stdout.fileno.return_value = 3
        mock_process.stderr = Mock()
        mock_process.stderr.read.return_value = b""

        # Create ftyp + moov boxes
        ftyp_data = struct.pack(">I", 20) + b"ftyp" + b"x" * 12
        moov_data = struct.pack(">I", 24) + b"moov" + b"x" * 16
        test_data = ftyp_data + moov_data

        # Mock readability to return True first time for stdout, then False to break the loop
        read_call_count = 0

        def mock_readable_side_effect(fp):
            nonlocal read_call_count
            if fp == mock_process.stdout:
                read_call_count += 1
                return read_call_count == 1  # Only return True on first call
            return False

        mock_readable.side_effect = mock_readable_side_effect

        # Mock os.read to return data first time, empty bytes second time
        read_data_call_count = 0

        def mock_read_side_effect(fd, size):
            nonlocal read_data_call_count
            read_data_call_count += 1
            if read_data_call_count == 1:
                return test_data
            else:
                return b""  # Empty read to break the while loop

        mock_read.side_effect = mock_read_side_effect

        self.processor._ffmpeg_process = mock_process
        self.processor._fmp4_state = state = {
            "got_first_frame": False,
            "buf": bytearray(),
            "init_segment": None,
            "last_init_sent": None,
        }

        self.processor._drain_fmp4()

        # Verify init segment was created and sent
        self.assertIsNotNone(state["init_segment"])
        self.assertEqual(len(state["init_segment"]), 44)  # 20 + 24 bytes
        mock_send.assert_called_with("stream.init", state["init_segment"])
