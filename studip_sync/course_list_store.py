import os
from datetime import datetime, timezone

from studip_sync.course_paths import get_course_save_as
from studip_sync.helpers import atomic_write_json


def save_course_list(courses, output_dir):
    output_dir = output_dir or "."
    path = os.path.join(output_dir, "course_list.json")
    os.makedirs(output_dir, exist_ok=True)

    serialized_courses = []
    for course in courses:
        serialized_courses.append({
            "course_id": course.get("course_id"),
            "name": course.get("save_as"),
            "semester": course.get("semester"),
            "target_path": get_course_save_as(course)
        })

    data = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "count": len(serialized_courses),
        "courses": serialized_courses
    }

    atomic_write_json(path, data)

    return path
