"""
Build a CloudEvents-compatible timeseries payload from scraped EPEX rows
and POST it to a webhook URL read from the SIGNALS_WEBHOOK_URL environment
variable.

Presumed Python 3.12.8
"""

import json
import logging
import os
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple


def build_timeseries_payload(
    event_id: str,
    delivery_date: str,
    mtu: str,
    zone: str,
    time_values: List[Tuple[str, Optional[float]]],
) -> dict:
    """
    Build a CloudEvents-compatible timeseries payload.

    *delivery_date* — YYYY-MM-DD string used for ``$.period`` and timestamp base.
    *mtu*           — one of ``'hh'`` (30 min), ``'qh'`` (15 min), ``'1h'``, ``'2h'``.
    *zone*          — lower-cased market zone string (e.g. ``'gb'``, ``'no2'``).
    *time_values*   — list of ``("HH:MM", price)`` pairs; one entry per row.
    """
    mtu_minutes: dict = {"hh": 30, "qh": 15, "1h": 60, "2h": 120}
    interval = timedelta(minutes=mtu_minutes[mtu])
    base_dt = datetime.strptime(delivery_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    period = delivery_date.replace("-", "")

    values = []
    for time_str, value in time_values:
        h, m = int(time_str[:2]), int(time_str[3:5])
        from_dt = base_dt + timedelta(hours=h, minutes=m)
        to_dt = from_dt + interval
        values.append({
            "from": from_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "to": to_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "value": value,
        })

    return {
        "specversion": "1.0",
        "id": event_id,
        "source": "https://github.com/tommed/epex-spot-scraper",
        "type": "timeseries",
        "subject": "epex",
        "mtu": mtu,
        "period": period,
        "zone": zone,
        "datacontenttype": "application/json",
        "time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "data": {"values": values},
    }


def post_webhook_payload(payload: dict) -> None:
    """
    POST *payload* as JSON to the URL stored in the ``SIGNALS_WEBHOOK_URL``
    environment variable.  Logs a warning and returns silently if the variable
    is not set.  HTTP errors are logged but do not raise.
    """
    url = os.environ.get("SIGNALS_WEBHOOK_URL")
    if not url:
        logging.warning("SIGNALS_WEBHOOK_URL not set; skipping webhook POST.")
        return
    data = json.dumps(payload).encode("utf-8")
    print(f"Posting webhook payload to {url}:\n{json.dumps(payload, indent=2)}")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            logging.info("Webhook POST → HTTP %d", resp.status)
    except urllib.error.HTTPError as e:
        logging.error("Webhook POST failed: HTTP %d %s", e.code, e.reason)
    except urllib.error.URLError as e:
        logging.error("Webhook POST failed: %s", e.reason)
