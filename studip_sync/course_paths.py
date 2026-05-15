import os
import re


def sanitize_path_component(value):
    component = (value or "").strip()
    component = re.sub(r"\s\s+", " ", component)
    component = component.replace("/", "--")

    if component:
        return component

    return "Unknown"


def get_course_save_as(course):
    semester = sanitize_path_component(course.get("semester"))
    course_name = sanitize_path_component(course.get("save_as"))
    course_id = sanitize_path_component(str(course.get("course_id", "unknown")))
    course_folder = "{} [{}]".format(course_name, course_id)

    return os.path.join(semester, course_folder)
