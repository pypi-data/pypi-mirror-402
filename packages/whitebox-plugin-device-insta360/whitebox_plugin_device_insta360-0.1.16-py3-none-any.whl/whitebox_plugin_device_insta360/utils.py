import os
import time
import subprocess
import queue
import select
import struct
from contextlib import ExitStack
from pathlib import Path

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from whitebox import get_plugin_logger
from utils.functional import wrapped_partial


logger = get_plugin_logger(__name__)


channel_layer = get_channel_layer()


# region ffmpeg


def _prepare_ffmpeg_command(
    input_file=None,
    input_stdin=False,
    output_file=None,
    output_stdout=False,
    width=1440,
    height=720,
):
    if not input_file and not input_stdin:
        raise ValueError("Either input_file or input_stdin must be provided")

    if input_file and input_stdin:
        raise ValueError("Provide only one of input_file or input_stdin")

    if not output_file and not output_stdout:
        raise ValueError("Either output_file or output_stdout must be provided")

    ffmpeg_input = input_file if input_file else "pipe:0"

    command = [
        "ffmpeg",
        #
        # Hide FFmpeg's banner by default. Uncomment this if you'd like the
        # banner to go into the logs (includes version and build configuration)
        # "-hide_banner",
        #
        "-loglevel",
        "warning",
        "-threads",
        "1",
        "-filter_complex_threads",
        "8",
        # Input side
        "-fflags",
        "+nobuffer",  # lower latency
        "-f",
        "h264",  # raw Annex-B H.264 input
        "-i",
        ffmpeg_input,
        # Processing
        # "-vf",
        "-filter_complex",
        f"[0:v]scale={width}:{height},v360=dfisheye:e:ih_fov=193:iv_fov=193[out]",
        # Output side: fragmented MP4 for MSE (init segment + moof/mdat fragments)
        "-map",
        "[out]",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-tune",
        "zerolatency",
        "-pix_fmt",
        "yuv420p",
        "-profile:v",
        "baseline",
        "-level",
        "3.1",
        "-x264-params",
        "bframes=0:keyint=60:min-keyint=60:scenecut=0",
        "-movflags",
        "+frag_keyframe+empty_moov+default_base_moof+separate_moof",
        "-frag_duration",
        "500000",  # ~0.5s
        "-an",
        "-f",
        "mp4",
        "pipe:1",
    ]

    return command


def start_ffmpeg_process(
    input_file=None,
    input_stdin=False,
    output_file=None,
    output_stdout=False,
    width=1440,
    height=720,
):
    command = _prepare_ffmpeg_command(
        input_file=input_file,
        input_stdin=input_stdin,
        output_file=output_file,
        output_stdout=output_stdout,
        width=width,
        height=height,
    )

    logger.info(f"Running ffmpeg command:\n{' '.join(command)}")
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE if input_stdin else None,
        stdout=subprocess.PIPE if output_stdout else None,
        stderr=subprocess.PIPE,
    )
    return process


def ffprobe_get_video_duration(file_path):
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        file_path,
    ]

    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)

    except subprocess.CalledProcessError as e:
        logger.error(
            f'Failed to get video duration for file "{file_path}"\n{e.output}',
        )
        return None

    except Exception as e:
        logger.exception(f'Failed to get video duration for file "{file_path}"')
        return None

    return float(output)


# endregion ffmpeg


# region streaming


class VideoQueueProcessor:
    INIT_SEGMENT_RESEND_INTERVAL = 2.0

    def __init__(
        self,
        stop_event: "threading.Event",
        process_queue: "queue.Queue[bytes]",
        stream_to_websocket: bool = False,
        save_to_file: str | Path = False,
        save_to_file_raw: bool = False,
        on_video_start: callable = None,
        on_video_end: callable = None,
    ):
        if not any((stream_to_websocket, save_to_file)):
            raise ValueError(
                "Either stream_to_websocket or save_to_file must be provided",
            )

        self.stop_event = stop_event
        self.process_queue = process_queue

        self.stream_to_websocket = stream_to_websocket
        self.save_to_file = save_to_file
        self.save_to_file_raw = save_to_file_raw

        self._ffmpeg_process = None
        self._running = False

        self._fmp4_state = None
        self._fmp4_output_file = None
        self._raw_output_file = None

        self.on_video_start = on_video_start
        self.on_video_end = on_video_end
        self._handled_video_start = False

    def _start_ffmpeg(self):
        self._ffmpeg_process = start_ffmpeg_process(
            input_stdin=True,
            output_stdout=True,
            width=1440,
            height=720,
        )
        os.set_blocking(self._ffmpeg_process.stdout.fileno(), False)
        os.set_blocking(self._ffmpeg_process.stderr.fileno(), False)

    def _maybe_resend_init_segment(self):
        if not self.stream_to_websocket:
            return

        if not self._fmp4_state:
            return

        init_segment = self._fmp4_state["init_segment"]

        if not init_segment:
            return

        now = time.time()
        last_init_sent = self._fmp4_state["last_init_sent"] or 0

        if (now - last_init_sent) >= self.INIT_SEGMENT_RESEND_INTERVAL:
            _send_to_frontend(
                "stream.init",
                self._fmp4_state["init_segment"],
            )
            self._fmp4_state["last_init_sent"] = now

    def _process_segment(self, segment, init=False):
        if self.stream_to_websocket:
            if init:
                message_type = "stream.init"
            else:
                message_type = "stream.data"
                # Every time we get the normal segment, check if init segment is
                # due to be resent
                self._maybe_resend_init_segment()

            _send_to_frontend(message_type, segment)

        if self.save_to_file:
            self._fmp4_output_file.write(segment)

            if not self._handled_video_start:
                self._handled_video_start = True
                if self.on_video_start:
                    self.on_video_start()

    def _drain_fmp4(self):
        got_first_frame = self._fmp4_state["got_first_frame"]

        if _readable(self._ffmpeg_process.stdout):
            fd = self._ffmpeg_process.stdout.fileno()
            while True:
                try:
                    chunk = os.read(fd, 64 * 1024)
                    if not chunk:
                        break
                    self._fmp4_state["buf"].extend(chunk)

                    if not got_first_frame:
                        got_first_frame = True
                        self._fmp4_state["got_first_frame"] = True
                        logger.info("Received first encoded frame from ffmpeg")
                except BlockingIOError:
                    break

        # Always drain stderr to avoid blocking
        if _readable(self._ffmpeg_process.stderr):
            try:
                stderr_output = self._ffmpeg_process.stderr.read()
                logger.info(
                    f"ffmpeg stderr: {stderr_output.decode('utf-8', 'ignore')}",
                )
            except Exception:
                logger.exception("Error reading ffmpeg stderr")
                pass

        mv = memoryview(self._fmp4_state["buf"])  # zero-copy slicing for parsing
        off = 0

        if not self._fmp4_state["init_segment"]:
            # Expect ftyp + moov at the start
            parts = []
            cur = off
            for expected in ("ftyp", "moov"):
                box = _parse_box_len(mv, cur)
                if not box:
                    return  # need more bytes
                size, typ = box
                if typ != expected:
                    # Unexpected; drop until a plausible ftyp
                    off = 0
                    # try to resync by discarding one byte
                    self._fmp4_state["buf"] = bytearray(mv[1:].tobytes())
                    return
                parts.append(mv[cur : cur + size].tobytes())
                cur += size

            off = cur

            # We have both boxes fully
            init_segment = b"".join(parts)
            self._fmp4_state["init_segment"] = init_segment

            self._process_segment(init_segment, init=True)
        else:
            # Emit moof+mdat pairs
            while True:
                box = _parse_box_len(mv, off)
                if not box:
                    break
                size, typ = box
                if typ != "moof":
                    # Skip unexpected box types until moof
                    off += size
                    continue
                moof_off = off
                moof_end = off + size
                off = moof_end
                box2 = _parse_box_len(mv, off)
                if not box2:
                    # need more for the following box
                    off = moof_off
                    break
                size2, typ2 = box2
                if typ2 != "mdat":
                    # Not a fragment; skip moof
                    off = moof_end
                    continue
                mdat_end = off + size2
                if mdat_end > len(mv):
                    # partial mdat; wait for more
                    off = moof_off
                    break

                # Emit moof+mdat together
                content = mv[moof_off:mdat_end].tobytes()
                off = mdat_end

                self._process_segment(content)

        if off > 0:
            # Discard consumed bytes
            self._fmp4_state["buf"] = bytearray(mv[off:].tobytes())

    def _process_queue_until_stop_event(self):
        got_first_camera_data = False

        while not self.stop_event.is_set():
            poll = self._ffmpeg_process.poll()
            if poll is not None:
                logger.error(f"FFMPEG DIED WITH EXIT CODE {poll}")
                raise SystemExit

            try:
                content = self.process_queue.get(timeout=0.05)

                if not got_first_camera_data:
                    got_first_camera_data = True
                    logger.info("Received first video data from camera")
            except queue.Empty:
                # Periodically drain encoder output even if no new input
                self._drain_fmp4()
                continue

            if self._raw_output_file:
                self._raw_output_file.write(content)

            try:
                self._ffmpeg_process.stdin.write(content)
            except (BrokenPipeError, ValueError):
                pass

            self._drain_fmp4()

    def run(self):
        if self._running:
            raise RuntimeError("Already running")

        self._running = True
        self._fmp4_state = {
            "got_first_frame": False,
            "buf": bytearray(),
            "init_segment": None,
            "last_init_sent": None,
        }

        self._start_ffmpeg()

        exit_stack = ExitStack()

        if self.save_to_file:
            output_file_path = Path(self.save_to_file)
            output_file_path.parent.mkdir(parents=True, exist_ok=True)
            self._fmp4_output_file = open(output_file_path, "wb")
            exit_stack.enter_context(self._fmp4_output_file)

            if self.save_to_file_raw:
                raw_output_file_path = output_file_path.with_suffix(".raw")
                self._raw_output_file = open(raw_output_file_path, "wb")
                exit_stack.enter_context(self._raw_output_file)

        with exit_stack:
            self._process_queue_until_stop_event()

            # Final drain on shutdown
            try:
                self._ffmpeg_process.stdin.close()
            except Exception:
                pass

            # Drain any remaining output
            self._drain_fmp4()

            logger.info("Closing ffmpeg stdout/stderr")
            self._ffmpeg_process.stdout.close()
            self._ffmpeg_process.stderr.close()

            logger.info("Asking ffmpeg to terminate")
            self._ffmpeg_process.terminate()

            logger.info("Waiting for ffmpeg to exit (2s)")
            self._ffmpeg_process.wait(timeout=2)

        logger.info("Stream ended gracefully")
        if self.on_video_end:
            self.on_video_end()


async def _base_video_stream_handler(
    content: bytes,
    queue: "queue.Queue[bytes]",
    **kwargs,
):
    queue.put(content)


def prepare_stream_handler(queue):
    return wrapped_partial(
        _base_video_stream_handler,
        queue=queue,
    )


# endregion streaming


# region processing


def _send_to_frontend(type_, content: bytes):
    # Use the channel layer to send the content
    send_coro = channel_layer.group_send
    wrapped_send = async_to_sync(send_coro)
    # print('Sending content to frontend')
    wrapped_send(
        "video_stream",
        {
            "type": type_,
            "content": content,
        },
    )


def _readable(fp):
    try:
        r, _, _ = select.select([fp], [], [], 0)
        return bool(r)
    except Exception:
        return False


def _parse_box_len(b: memoryview, off: int):
    if off + 8 > len(b):
        return None
    size = struct.unpack_from(">I", b, off)[0]
    typ = bytes(b[off + 4 : off + 8]).decode("ascii", "ignore")
    if size == 1:
        if off + 16 > len(b):
            return None
        size = struct.unpack_from(">Q", b, off + 8)[0]
        hdr = 16
    else:
        hdr = 8
    if size < hdr:
        return None
    if off + size > len(b):
        return None
    return size, typ


# endregion processing
