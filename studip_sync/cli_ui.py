from studip_sync.log import colorize

DEFAULT_COURSE_DISPLAY_MAX_CHARS = 60

STATE_COLORS = {
    "ok": "green",
    "warn": "yellow",
    "error": "red",
    "info": "cyan"
}


def truncate_text(value, max_chars=DEFAULT_COURSE_DISPLAY_MAX_CHARS):
    text = str(value or "")
    if max_chars <= 0:
        return ""
    if len(text) <= max_chars:
        return text
    if max_chars <= 3:
        return text[:max_chars]
    return text[:max_chars - 3] + "..."


def build_progress_bar(current, total, width=16):
    if total <= 0:
        return "[{}]".format("." * width)

    safe_current = max(0, min(current, total))
    filled = int(round((float(safe_current) / float(total)) * width))
    return "[{}{}]".format("=" * filled, "." * (width - filled))


def format_banner(mode, sync_fully, sync_recent, dry_run, use_api=None):
    mode_label = "rsync" if mode == "rsync" else "legacy"
    parts = [
        colorize("studip-sync", "bold"),
        "mode={}".format(mode_label),
        "full={}".format("yes" if sync_fully else "no"),
        "recent={}".format("yes" if sync_recent else "no"),
        "dry_run={}".format("yes" if dry_run else "no")
    ]
    if use_api is not None:
        parts.append("api={}".format("yes" if use_api else "no"))
    return " | ".join(parts)


def format_controls_hint(enabled):
    if not enabled:
        return "Controls: unavailable (non-interactive terminal)"
    return "Controls: [p] pause/resume  [q] abort  [h] help"


def format_course_header(index, total, course_name):
    progress = colorize(build_progress_bar(index, total), "cyan")
    counter = colorize("{}/{}".format(index, total), "blue")
    title = truncate_text(course_name)
    return "{} {} {}".format(progress, counter, title)


def format_status_line(section, message, state="info"):
    color = STATE_COLORS.get(state, "cyan")
    label = colorize(section + ":", color)
    return "  {} {}".format(label, message)


def format_summary_line(status_code, stats, aborted=False):
    if aborted or status_code == 130:
        status = colorize("ABORTED", "yellow")
    elif status_code == 0:
        status = colorize("OK", "green")
    else:
        status = colorize("FAILED", "red")

    return (
        "Result={} | courses={} | file_synced={} | file_would_sync={} | "
        "files_downloaded={} | media_downloaded={} | errors={}"
    ).format(
        status,
        stats.get("courses_total", 0),
        stats.get("courses_file_synced", 0),
        stats.get("courses_file_would_sync", 0),
        stats.get("files_downloaded", 0),
        stats.get("media_downloaded", 0),
        stats.get("errors", 0)
    )
