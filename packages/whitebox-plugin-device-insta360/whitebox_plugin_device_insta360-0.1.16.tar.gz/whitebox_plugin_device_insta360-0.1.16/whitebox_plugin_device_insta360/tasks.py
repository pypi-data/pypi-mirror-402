import logging
import re
import time
from datetime import timedelta
from pathlib import Path
from threading import Event, Thread
from queue import Queue

import django_rq
from django.conf import settings
from django.utils import timezone
from insta360.rtmp import Client

from whitebox import import_whitebox_model, get_plugin_logger
from .utils import (
    VideoQueueProcessor,
    prepare_stream_handler,
    ffprobe_get_video_duration,
)


logger = get_plugin_logger(__name__)


DeviceConnection = import_whitebox_model("device.DeviceConnection")
FlightSession = import_whitebox_model("flight.FlightSession")
FlightSessionRecording = import_whitebox_model("flight.FlightSessionRecording")


def _get_client_for_device_connection(device_connection):
    # TODO: When we add support for multiple Insta360's at once, resolve proper
    #       target by `device_connection` for the `Client` to connect to

    client = Client(
        # host=host,
        # port=port,
    )

    logger.info("Checking if camera is connected...")
    client.ensure_camera_connected()

    return client


def _get_base_flight_recording_path(flight_session, device_connection):
    return (
        settings.MEDIA_ROOT
        / "flight_recordings"
        / f"{flight_session.id}_{device_connection.id}"
    )


# region recording during flight


def _kickoff_video_queue_processor(
    processing_queue,
    flight_session_ended_event,
    output_filename,
    flight_session_recording=None,
):
    video_queue_processor_kwargs = {}

    if flight_session_recording:

        def on_start():
            flight_session_recording.status = FlightSessionRecording.STATUSES.RECORDING
            flight_session_recording.started_at = timezone.now()
            flight_session_recording.save(
                update_fields=[
                    "status",
                    "started_at",
                ]
            )

        def on_end():
            flight_session_recording.status = FlightSessionRecording.STATUSES.READY
            flight_session_recording.save(update_fields=["status"])

        video_queue_processor_kwargs["on_video_start"] = on_start
        video_queue_processor_kwargs["on_video_end"] = on_end

    video_queue_processor = VideoQueueProcessor(
        process_queue=processing_queue,
        stop_event=flight_session_ended_event,
        stream_to_websocket=True,
        save_to_file=output_filename,
        **video_queue_processor_kwargs,
    )
    processing_thread = Thread(target=video_queue_processor.run)
    processing_thread.start()

    return processing_thread


def _handle_camera_connection_for_flight_session(
    flight_session,
    device_connection,
    client,
    output_filename,
):
    processing_queue = Queue()
    flight_session_ended_event = Event()

    handler = prepare_stream_handler(
        processing_queue,
    )

    register_event_decor = client.on_video_stream(
        # wait=True,
        uid="insta360-on-flight-start-video-stream-handler",
    )
    register_event_decor(handler)

    # Create a FlightSessionRecording to keep track of existing files in case
    # there's some failure within the thread, so that we can track used space
    recording = FlightSessionRecording(
        flight_session=flight_session,
    )
    recording.file.name = Path(output_filename).as_posix()
    recording.provided_by = device_connection
    recording.save()

    # Kick off the processing of the stream in a separate thread
    logger.info("Starting the stream processing thread...")
    processing_thread = _kickoff_video_queue_processor(
        processing_queue=processing_queue,
        flight_session_ended_event=flight_session_ended_event,
        output_filename=output_filename,
        flight_session_recording=recording,
    )

    # Sync time to camera to ensure the file timestamps are accurate
    client.sync_local_time_to_camera()

    # Now, start the recording on the camera. As the video feed comes in, it
    # will be handled by the event handler running in its own thread. Here, we
    # will wait for the flight session to end, and then stop the recording
    logger.info("Starting the preview stream...")
    client.start_capture()
    client.start_preview_stream()

    logger.info("Recording started, waiting for flight session to end...")
    while True:
        flight_session.refresh_from_db()
        if not flight_session.is_active:
            flight_session_ended_event.set()
            break

        time.sleep(1)

    logger.info("Finished sleeping, stopping stream...")

    client.stop_capture()
    client.stop_preview_stream()
    client.close()

    logger.info("Waiting for the processing thread to finish...")
    processing_thread.join()

    logger.info("Recording stopped, file should be saved now.")
    recording.status = FlightSessionRecording.STATUSES.READY
    recording.save()


def handle_recording_for_flight_session(
    flight_session_id,
    device_connection_id,
):
    flight_session = FlightSession.objects.get(id=flight_session_id)
    device_connection = DeviceConnection.objects.get(id=device_connection_id)

    timestamp = timezone.now().isoformat().replace(":", "-").replace("T", "_")

    base_path = _get_base_flight_recording_path(
        flight_session,
        device_connection,
    )
    base_filename = "insta360_f{}_d{}_{}".format(
        flight_session.id,
        device_connection.id,
        timestamp,
    )
    filename_mp4 = base_path / f"{base_filename}.mp4"

    if Path(filename_mp4).exists():
        raise ValueError("Target file already exists")

    # First, connect to the camera
    client = _get_client_for_device_connection(device_connection)
    client.open()

    _handle_camera_connection_for_flight_session(
        flight_session=flight_session,
        device_connection=device_connection,
        client=client,
        output_filename=filename_mp4,
    )

    client.close()

    logger.info("Recording handler finished, enqueuing post-flight operations...")
    # TODO: Create a small API for this (e.g. `whitebox.tasks.run_task`)
    #       which would allow us to transition to other task queues in the
    #       future without requiring individual plugin changes
    django_rq.enqueue(
        post_flight_operations,
        flight_session_id=flight_session_id,
        device_connection_id=device_connection_id,
        # RQ queue settings
        job_timeout="24h",
    )


# endregion recording during flight


# region handling media post flight


re_camera_file_date_time = re.compile(
    r"_"
    r"(?P<year>\d{4})"
    r"(?P<month>\d{2})"
    r"(?P<day>\d{2})"
    r"_"
    r"(?P<hour>\d{2})"
    r"(?P<minute>\d{2})"
    r"(?P<second>\d{2})"
    r"_",
)


def _filter_files_eligible_for_flight_session(flight_session, file_list):
    from_ts = timezone.make_naive(flight_session.started_at)
    to_ts = timezone.make_naive(flight_session.ended_at)

    eligible = []

    for file_path in file_list:
        parsed = Path(file_path)

        # Only download high resolution videos, we don't need any others
        if parsed.suffix.lower() != ".insv":
            continue

        filename = parsed.name
        regex_match = re_camera_file_date_time.search(filename)

        if not regex_match:
            continue

        # TODO: HOW TO ASCERTAIN TIMEZONE?
        # Now that we got the file's creation timestamp, we can figure out
        # whether it's eligible to be downloaded & associated with the actual
        # flight session or not. The filestamp indicates the moment when the
        # file was created, e.g. VID_20250903_165835_00_001.insv

        file_timestamp = timezone.datetime(
            year=int(regex_match.group("year")),
            month=int(regex_match.group("month")),
            day=int(regex_match.group("day")),
            hour=int(regex_match.group("hour")),
            minute=int(regex_match.group("minute")),
            second=int(regex_match.group("second")),
            # We do not have microseconds available
        )

        if from_ts <= file_timestamp <= to_ts:
            eligible.append(file_path)

    return eligible


def _download_and_associate_file_with_flight_session(
    flight_session,
    device_connection,
    client,
    file_path,
):
    # As this function is run in a thread, when making changes, make sure that
    # it is still thread-safe. At the time of writing, `client.download_file`
    # is an isolated operation from the client's state, thus thread-safe.
    # The `downlaod_file` relies on the OSC API, which uses the usual HTTP

    recording = FlightSessionRecording(
        flight_session=flight_session,
    )

    target_filename = Path(file_path).name
    base_path = _get_base_flight_recording_path(
        flight_session,
        device_connection,
    )

    target_path = base_path / target_filename
    download_ok = client.download_file(file_path, target_path)

    # Ensure that we don't have dead files in case of any failure
    if not download_ok:
        try:
            target_path.unlink()
        except FileNotFoundError:
            pass

        return None

    recording.file.name = target_path.as_posix()
    recording.status = FlightSessionRecording.STATUSES.READY
    recording.provided_by = device_connection
    recording.save()

    return recording


def _update_recording_durations(flight_session):
    logger.debug(
        f"Updating recording durations for flight session {flight_session.id}...",
    )
    recordings = flight_session.recordings.filter(ended_at=None)

    for recording in recordings:
        if not recording.file:
            logger.warning(
                f"Recording is missing file, skipping... (ID: {recording.pk})",
            )
            continue

        if not recording.started_at:
            logger.warning(
                f"Recording is missing start time, skipping... (ID: {recording.pk})",
            )
            continue

        file_path = recording.file.path
        try:
            seconds_duration = ffprobe_get_video_duration(file_path)
        except Exception as e:
            logger.exception(
                f"Failed to get video duration for recording {recording.id}",
            )
            continue

        delta = timedelta(seconds=seconds_duration)
        ended_at = recording.started_at + delta
        recording.ended_at = ended_at
        recording.save(update_fields=["ended_at"])

        logger.debug(
            f"Updated recording {recording.id} duration to {delta}",
        )


def post_flight_operations(
    flight_session_id,
    device_connection_id,
):
    # Download all clips that have material within the (started_at, stopped at)
    # range, inclusively

    # Build a single video file, based on the timestamps, that will, in case of
    # missing frames by timestamps, fill them up with a black screen (this would
    # include the first e.g. 0.5s of the flight, since it's `started` in the DB,
    # until the recording actually started on the camera). Time-tagging every
    # single piece of data like this, that is fetched externally, will enable us
    # to confidently be able to sync any kind of thing anywhere, with minimal
    # context except for the `started_at` timestamp along with the content
    # itself. However, this will require that we can sync our time with Insta360
    # camera upon connection to it (rtmp.Client.sync_local_time_to_camera), but
    # also on all other devices as well. Those that don't have it, we'll need to
    # figure out a way to make up for it, which I think would anyway be much
    # easier than any other alternative for streamlining development.

    # Create a `FlightRecording` entry that is going to have the highest
    # priority for viewing.
    logger.info(
        f"Post-flight tasks - F {flight_session_id} - D {device_connection_id}",
    )

    flight_session = FlightSession.objects.get(id=flight_session_id)
    device_connection = DeviceConnection.objects.get(id=device_connection_id)

    # First, update the live streamed flight session recording with its actual
    # video duration
    _update_recording_durations(flight_session)

    client = _get_client_for_device_connection(device_connection)
    client.open()

    file_list = client.get_camera_files_list_bundle()

    eligible_files = _filter_files_eligible_for_flight_session(
        flight_session,
        file_list,
    )

    logger.info(
        f"Found {len(eligible_files)} files for "
        f"flight session {flight_session_id}, downloading...",
    )

    for eligible_file in eligible_files:
        recording = _download_and_associate_file_with_flight_session(
            flight_session=flight_session,
            device_connection=device_connection,
            client=client,
            file_path=eligible_file,
        )
        logger.info(f". Recording saved to {recording.file.name}")

    client.close()
    logger.info("Post-flight tasks finished.")


# region handling media post flight
