from datetime import datetime, timezone

from studip_sync.helpers import atomic_write_json


def build_sync_report(mode, status_code, sync_fully, sync_recent, dry_run, use_api, stats,
                      aborted=False):
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "status_code": status_code,
        "aborted": bool(aborted),
        "sync_options": {
            "full": bool(sync_fully),
            "recent": bool(sync_recent),
            "dry_run": bool(dry_run),
            "use_api": bool(use_api)
        },
        "stats": dict(stats)
    }


def write_sync_report(path, report):
    atomic_write_json(path, report)
