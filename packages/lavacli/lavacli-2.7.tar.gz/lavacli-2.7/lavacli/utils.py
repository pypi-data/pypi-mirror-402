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

import re
import xmlrpc.client
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

from ruamel.yaml import YAML

VERSION_LATEST = (3000, 1)

# yaml objects

flow_yaml = YAML(typ="safe")
flow_yaml.default_flow_style = False
log_yaml = YAML(typ="safe")
log_yaml.default_flow_style = True
log_yaml.default_style = '"'
log_yaml.width = 10**6
# 'safe' -> SafeLoader/SafeDumper
safe_yaml = YAML(typ="safe")
# 'rt'/None -> RoundTripLoader/RoundTripDumper (default)
rt_yaml = YAML(typ="rt")


def parse_version(version):
    pattern = re.compile(r"(?P<major>20\d{2})\.(?P<minor>\d{1,2})")
    if not isinstance(version, str):
        version = str(version)
    m = pattern.match(version)
    if m is None:
        return VERSION_LATEST
    res = m.groupdict()
    return (int(res["major"]), int(res["minor"]))


def exc2str(exc, url):
    if isinstance(exc, xmlrpc.client.ProtocolError):
        msg = exc.errmsg
        if url is None:
            return msg
        p = urlparse(url)
        if "@" in p.netloc:
            uri = f"{p.scheme}://<USERNAME>:<TOKEN>@{p.netloc.split('@')[-1]}{p.path}"
        else:
            uri = f"{p.scheme}://{p.netloc}{p.path}"
        return msg.replace(url, uri)
    return str(exc)


def fetch_jobs(proxy, state, health, limit, since, start=0):
    job_numbers = []
    batch_size = 100

    while len(job_numbers) < limit:
        remaining = limit - len(job_numbers)
        fetch_count = min(batch_size, remaining)

        try:
            jobs = proxy.scheduler.jobs.list(
                state,
                health,
                start,
                fetch_count,
                since,
                False,
            )
        except xmlrpc.client.Error as exc:
            print(f"Error fetching jobs: {exc}")
            break

        if not jobs:
            break

        job_ids = [str(job["id"]) for job in jobs]
        job_numbers.extend(job_ids)
        start += batch_size

    return job_numbers


def extract_device_name(job_output):
    device_regex = re.compile(r"(?i)^\s*device\s*:\s*(.*)")
    for line in job_output.splitlines():
        match = device_regex.match(line)
        if match:
            return match.group(1).strip()
    return None


def print_error_summary(error_summary, summary=True):
    if summary:
        print("\n=== Short log with error count type of error and devices ===")
    else:
        print("\n=== Unique Errors Found with job-url ===")

    for error, device_jobs in sorted(
        error_summary.items(),
        key=lambda x: sum(len(jobs) for jobs in x[1].values()),
        reverse=True,
    ):
        total_count = sum(len(jobs) for jobs in device_jobs.values())
        if summary:
            devices_str = ", ".join(sorted(device_jobs))
            print(f"[{total_count}] {error} (Devices: {devices_str})")
        else:
            print(f"\n[{total_count}] {error}")
            for device in sorted(device_jobs):
                print(f"  - {device}:")
                for url in sorted(device_jobs[device]):
                    print(f"    * {url}")


def fetch_jobs_concurrent(
    proxy, job_ids, fetch_func, max_workers=None, progress_callback=None
):
    """
    Fetch multiple jobs concurrently using ThreadPoolExecutor.

    Args:
        proxy: XML-RPC proxy object
        job_ids: List of job IDs to fetch
        fetch_func: Function that takes (proxy, job_id) and returns job data
        max_workers: Maximum number of concurrent workers (default: min(20, len(job_ids)))
        progress_callback: Optional callback function called with (processed, total)

    Returns:
        List of (job_id, job_data) tuples. job_data is None if fetch failed.
    """
    if not job_ids:
        return []

    if max_workers is None:
        max_workers = min(20, len(job_ids))

    results = []
    processed = 0

    def fetch_single(job_id):
        try:
            return job_id, fetch_func(proxy, job_id)
        except Exception as exc:
            # Return the exception for caller to handle
            return job_id, exc

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_job = {
            executor.submit(fetch_single, job_id): job_id for job_id in job_ids
        }

        for future in as_completed(future_to_job):
            job_id, result = future.result()
            results.append((job_id, result))
            processed += 1

            if progress_callback:
                progress_callback(processed, len(job_ids))

    return results
