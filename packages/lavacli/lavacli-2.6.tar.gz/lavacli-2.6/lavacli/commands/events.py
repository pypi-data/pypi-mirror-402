# vim: set ts=4

# Copyright 2017 Rémi Duraffort
# This file is part of lavacli.
#
# lavacli is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# lavacli is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with lavacli.  If not, see <http://www.gnu.org/licenses/>

import asyncio
import json
import sys
from urllib.parse import urlparse

import aiohttp

from lavacli.__about__ import __version__


def configure_parser(parser, version):
    sub = parser.add_subparsers(dest="sub_sub_command", help="Sub commands")
    sub.required = True

    # "listen"
    listen_parser = sub.add_parser("listen", help="listen to events")
    listen_parser.add_argument(
        "--filter",
        action="append",
        default=None,
        choices=["device", "event", "testjob", "worker"],
        help="filter by topic type",
    )

    # "wait"
    wait_parser = sub.add_parser("wait", help="wait for a specific event")
    obj_parser = wait_parser.add_subparsers(dest="object", help="object to wait")
    obj_parser.required = True

    # "wait device"
    device_parser = obj_parser.add_parser("device")
    device_parser.add_argument("name", type=str, help="name of the device")
    device_parser.add_argument(
        "--state",
        default=None,
        choices=["IDLE", "RESERVED", "RUNNING"],
        help="device state",
    )
    device_parser.add_argument(
        "--health",
        default=None,
        choices=["GOOD", "UNKNOWN", "LOOPING", "BAD", "MAINTENANCE", "RETIRED"],
        help="device health",
    )

    # "wait job"
    testjob_parser = obj_parser.add_parser("job")
    testjob_parser.add_argument("job_id", help="job id")
    testjob_parser.add_argument(
        "--state",
        default=None,
        choices=[
            "SUBMITTED",
            "SCHEDULING",
            "SCHEDULED",
            "RUNNING",
            "CANCELING",
            "FINISHED",
        ],
        help="job state",
    )
    testjob_parser.add_argument(
        "--health",
        default=None,
        choices=["UNKNOWN", "COMPLETE", "INCOMPLETE", "CANCELED"],
        help="job health",
    )

    # "wait worker"
    worker_parser = obj_parser.add_parser("worker")
    worker_parser.add_argument("name", type=str, help="worker name")
    worker_parser.add_argument(
        "--state", default=None, choices=["ONLINE", "OFFLINE"], help="worker state"
    )
    worker_parser.add_argument(
        "--health",
        default=None,
        choices=["ACTIVE", "MAINTENANCE", "RETIRED"],
        help="worker health",
    )


def help_string():
    return "listen to events"


def _get_zmq_url(proxy, options, config):
    if config is None or config.get("events", {}).get("uri") is None:
        url = proxy.scheduler.get_publisher_event_socket()
        if "*" in url:
            domain = urlparse(options.uri).netloc
            if "@" in domain:
                domain = domain.split("@")[1]
            domain = domain.split(":")[0]
            url = url.replace("*", domain)
    else:
        url = config["events"]["uri"]

    return url


def print_event(options, config, topic, dt, username, data):
    # If unknown, print the full data
    msg = data
    data = json.loads(data)
    # Print according to the topic
    topic_end = topic.split(".")[-1]

    # filter by topic_end
    if options.filter and topic_end not in options.filter:
        return

    if topic_end == "device":
        msg = f"[{data['device']}] <{data['device_type']}> state={data['state']} health={data['health']}"
        if "job" in data:
            msg += " for %s" % data["job"]
    elif topic_end == "testjob":
        msg = f"[{data['job']}] <{data.get('device', '??')}> state={data['state']} health={data['health']} ({data['description']})"
    elif topic_end == "worker":
        msg = f"[{data['hostname']}] state={data['state']} health={data['health']}"
    elif topic_end == "event":
        msg = f"[{data['job']}] message={data['message']}"

    if sys.stdout.isatty():
        print(
            f"\033[1;30m{dt}\033[0m \033[1;37m{topic}\033[0m \033[32m{username}\033[0m - {msg}"
        )
    else:
        print(f"{dt} {topic} {username} - {msg}")


def loop_zmq_events(proxy, options, config, func):
    import zmq  # pylint: disable=import-outside-toplevel
    from zmq.utils.strtypes import b  # pylint: disable=import-outside-toplevel

    # Try to find the socket url
    url = _get_zmq_url(proxy, options, config)
    if url is None:
        print("Unable to find the socket url", file=sys.stderr)
        return 1

    context = zmq.Context()
    sock = context.socket(zmq.SUB)
    sock.setsockopt(zmq.SUBSCRIBE, b"")
    # Set the sock proxy (if needed)
    socks = config.get("events", {}).get("socks_proxy")
    if socks is not None:
        print(f"Listening to {url} (socks {socks})")
        sock.setsockopt(zmq.SOCKS_PROXY, b(socks))
    else:
        print("Listening to %s" % url)

    try:
        sock.connect(url)
    except zmq.error.ZMQError as exc:
        print("Unable to connect: %s" % exc, file=sys.stderr)
        return 1

    while True:
        msg = sock.recv_multipart()
        try:
            # Convert bytes to string using decode() instead of deprecated strtypes
            (topic, _, dt, username, data) = (
                m.decode("utf-8") if isinstance(m, bytes) else m for m in msg
            )
        except ValueError:
            print("Invalid message: %s" % msg, file=sys.stderr)
            continue
        if func(options, config, topic, dt, username, data):
            break


def loop_ws_events(proxy, options, config, func):
    async def handler():
        HEADERS = {"User-Agent": "lavacli v%s" % __version__}
        url = urlparse(options.uri)
        scheme = url.scheme
        path = url.path
        if path.endswith("/RPC2/"):
            path = path[:-5]
        elif path.endswith("/RPC2"):
            path = path[:-4]
        if not path.endswith("/"):
            path = path + "/"

        ws_url = ws_url_redacted = f"{scheme}://{url.netloc}{path}ws/"
        if "@" in url.netloc:
            ws_url_redacted = (
                f"{scheme}://<USERNAME>:<TOKEN>@{url.netloc.split('@')[-1]}{path}ws/"
            )

        try:
            while True:
                try:
                    async with aiohttp.ClientSession(headers=HEADERS) as session:
                        print("Connecting to %s" % ws_url_redacted)
                        async with session.ws_connect(ws_url, heartbeat=30) as ws:
                            async for msg in ws:
                                if msg.type == aiohttp.WSMsgType.TEXT:
                                    try:
                                        data = json.loads(msg.data)
                                        if "error" in data:
                                            raise aiohttp.ClientError(data["error"])
                                        (topic, _, dt, username, data) = data
                                    except ValueError:
                                        print(
                                            "Invalid message: %s" % msg,
                                            file=sys.stderr,
                                        )
                                        continue
                                    if func(options, config, topic, dt, username, data):
                                        return 0
                            print("Connection closed")
                            await asyncio.sleep(1)
                except aiohttp.ClientError as exc:
                    print("Connection issue: %s" % str(exc), file=sys.stderr)
                    await asyncio.sleep(1)
        except Exception as exc:
            print(exc, file=sys.stderr)

    asyncio.run(handler())


def handle_listen(proxy, options, config):
    if config["version"] < (2020, 9):
        loop_zmq_events(proxy, options, config, print_event)
    else:
        loop_ws_events(proxy, options, config, print_event)
    return 0


def handle_wait(proxy, options, config):
    def wait(options, config, topic, dt, username, data):
        # "job" is called "testjob" in the events
        object_topic = options.object
        if object_topic == "job":
            object_topic = "testjob"

        data = json.loads(data)

        # Filter by object
        obj = topic.split(".")[-1]
        if obj != object_topic:
            return False

        if object_topic == "device":
            if data.get("device") != options.name:
                return False
        elif object_topic == "testjob":
            if data.get("job") != options.job_id:
                return False
        else:
            if data.get("hostname") != options.name:
                return False

        # Filter by state
        if options.state is not None:
            if data.get("state") != options.state.capitalize():
                return False
        # Filter by health
        if options.health is not None:
            if data.get("health") != options.health.capitalize():
                return False

        return True

    if config["version"] < (2020, 9):
        loop_zmq_events(proxy, options, config, wait)
    else:
        loop_ws_events(proxy, options, config, wait)
    return 0


def handle(proxy, options, config):
    handlers = {"listen": handle_listen, "wait": handle_wait}
    return handlers[options.sub_sub_command](proxy, options, config)
