import requests_async as requests
import datetime

base_api_url = "https://api.school.mosreg.ru"
v = "v2.0"
base_api_url = f"{base_api_url}/{v}/"


def ts_to_iso(ts: int) -> str:
    ts = datetime.datetime.fromtimestamp(ts)
    return ts.isoformat()


def iso_to_ts(iso: str) -> int:
    ts = datetime.datetime.fromisoformat(iso)
    return int(ts.timestamp())


def anything_to_iso(anything):
    if isinstance(anything, str):
        return anything
    return ts_to_iso(anything)


class MosregException(Exception):
    def __init__(self, json_b, body, status_code):
        self.json: [dict, None] = json_b
        self.body: str = body
        self.status_code: int = status_code


class MosregNotFoundException(Exception):
    def __init__(self, json_b):
        self.type = json_b['parameterInvalid']
        self.parameterInvalid = json_b['parameterInvalid']


def exception_from_response(response: requests.Response) -> MosregException:
    n_json = None
    try:
        n_json = response.json()
    except ValueError:
        pass
    return MosregException(n_json, response.text, response.status_code)


class Subject:
    # noinspection PyShadowingBuiltins
    def __init__(self, id, id_str, name, knowledge_area):
        self.id: int = id
        self.id_str: str = id_str
        self.name: str = name
        self.knowledge_area: str = knowledge_area


class EduGroup:
    # noinspection PyShadowingBuiltins
    def __init__(self, id, id_str, parent_ids, parent_ids_str, type, name, full_name, parallel, timetable,
                 timetable_str, status, studyyear, education_type, subjects, journaltype):
        self.id: int = id
        self.id_str: str = id_str
        self.parent_ids: list = parent_ids
        self.parent_ids_str: list = parent_ids_str
        self.type: str = type
        self.name: str = name
        self.full_name: str = full_name
        self.parallel: int = parallel
        self.timetable: int = timetable
        self.timetable_str: str = timetable_str
        self.status: str = status
        self.studyyear: int = studyyear
        self.education_type: str = education_type
        self.subjects: list = [Subject(*list(x.values())) for x in subjects]
        self.journaltype: str = journaltype


class FinalMark:
    # noinspection PyShadowingBuiltins
    def __init__(self, id, id_str, type, value, text_value, person, person_str, work, work_str, lesson, lesson_str,
                 number, date, work_type, mood, use_avg_calc):
        self.id: int = id
        self.id_str: str = id_str
        self.type: str = type
        self.value: str = value
        self.text_value: str = text_value
        self.person: int = person
        self.person_str: str = person_str
        self.work: int = work
        self.work_str: str = work_str
        self.lesson: int = lesson
        self.lesson_str: str = lesson_str
        self.number: int = number
        self.date: str = date
        self.work_type: int = work_type
        self.mood: str = mood
        self.use_avg_calc: bool = use_avg_calc
        self.quarter: int = 0


class ReportingPeriod:
    # noinspection PyShadowingBuiltins
    def __init__(self, id, id_str, start, finish, number, type, name, year):
        self.id: int = id
        self.id_str: str = id_str
        self.start: str = start
        self.start_ts: int = iso_to_ts(self.start)
        self.finish: str = finish
        self.finish_ts: int = iso_to_ts(self.finish)
        self.number: int = number
        self.type: str = type
        self.name: str = name
        self.year: int = year


class MarkEntry:
    # noinspection PyShadowingBuiltins
    def __init__(self, subject, subject_str, final_mark):
        self.subject: int = subject
        self.subject_str: str = subject_str
        self.FinalMark: FinalMark = FinalMark(*list(final_mark.values()))


class EduGroupSmall:
    # noinspection PyShadowingBuiltins
    def __init__(self, e_id, id_str, parent_ids, parent_ids_str, e_type, name, full_name, parallel, timetable,
                 timetable_str, status, study_year, subjects, journal_type):
        self.id: int = e_id
        self.id_str: str = id_str
        self.parent_ids: list = parent_ids
        self.parent_ids_str: list = parent_ids_str
        self.type: str = e_type
        self.name: str = name
        self.full_name: str = full_name
        self.parallel: int = parallel
        self.timetable: int = timetable
        self.timetable_str: str = timetable_str
        self.status: str = status
        self.study_year: int = study_year
        self.subjects: [list, None] = subjects
        self.journal_type: str = journal_type


class School:
    # noinspection PyShadowingBuiltins
    def __init__(self, full_name, avatar_small, city, municipality, regionid, mark_type, time_zone, uses_avg,
                 uses_weighted_avg, id, id_str, name, education_type):
        self.full_name: str = full_name
        self.avatar_small: str = avatar_small
        self.city: str = city
        self.municipality: str = municipality
        self.regionid: int = regionid
        self.mark_type: str = mark_type
        self.time_zone: int = time_zone
        self.uses_avg: bool = uses_avg
        self.uses_weighted_avg: bool = uses_weighted_avg
        self.id: int = id
        self.id_str: str = id_str
        self.name: str = name
        self.education_type: str = education_type


class SchoolSmall:
    # noinspection PyShadowingBuiltins
    def __init__(self, id, name, type, group_ids):
        self.id: int = id
        self.name: str = name
        self.type: str = type
        self.group_ids: list = group_ids


class Context:
    def __init__(self, user_id, roles, children, schools, edu_groups, split_id, person_id, short_name, school_ids,
                 group_ids):
        self.user_id: int = user_id
        self.roles: list = roles
        self.children: list = children
        # self.B = [dic*x for x in schools]
        self.schools: list = [SchoolSmall(*list(x.values())) for x in schools]
        self.edu_groups: list = [EduGroupSmall(*list(x.values())) for x in edu_groups]
        self.split_id: str = split_id
        self.person_id: int = person_id
        self.short_name: str = short_name
        self.school_ids: list = school_ids
        self.group_ids: list = group_ids


class FullHomeworkTask:
    # noinspection PyShadowingBuiltins
    def __init__(self, id, id_str, person, person_str, work, work_str, status, target_date):
        self.id: int = id
        self.id_str: str = id_str
        self.person: int = person
        self.person_str: str = person_str
        self.work: int = work
        self.work_str: str = work_str
        self.status: str = status
        self.target_date: str = target_date


class FullHomeworkUser:
    # noinspection PyShadowingBuiltins
    def __init__(self, id, id_str, person_id, person_id_str, short_name, locale, timezone, sex, birthday, roles):
        self.id: int = id
        self.id_str: str = id_str
        self.person_id: int = person_id
        self.person_id_str: str = person_id_str
        self.short_name: str = short_name
        self.locale: str = locale
        self.timezone: str = timezone
        self.sex: str = sex
        self.birthday: str = birthday
        self.roles: list = roles


class FullHomeworkWork:
    # noinspection PyShadowingBuiltins
    def __init__(self, id, id_str, type, work_type, mark_type, mark_count, lesson, lesson_str, display_in_journal,
                 status, edu_group, edu_group_str, text, period_number, period_type, subject_id, is_important,
                 target_date, sent_date, created_by, files, one_drive_links):
        self.id: int = id
        self.id_str: str = id_str
        self.type: str = type
        self.work_type: int = work_type
        self.mark_type: str = mark_type
        self.mark_count: int = mark_count
        self.lesson: int = lesson
        self.lesson_str: str = lesson_str
        self.display_in_journal: bool = display_in_journal
        self.status: str = status
        self.edu_group: int = edu_group
        self.edu_group_str: str = edu_group_str
        self.text: str = text
        self.period_number: int = period_number
        self.period_type: str = period_type
        self.subject_id: int = subject_id
        self.is_important: bool = is_important
        self.target_date: str = target_date
        self.sent_date: str = sent_date
        self.created_by: int = created_by
        self.files: list = files
        self.one_drive_links: list = one_drive_links


class FullHomeworkSubject:
    # noinspection PyShadowingBuiltins
    def __init__(self, id, name, knowledge_area_id):
        self.id: int = id
        self.name: str = name
        self.knowledge_area_id: int = knowledge_area_id


class FullHomeworkLesson:
    # noinspection PyShadowingBuiltins
    def __init__(self, id, title, date, number, subject_id, status, result_place_id, building, place, floor, hours,
                 works, teachers):
        self.id: int = id
        self.title: str = title
        self.date: str = date
        self.number: int = number
        self.subject_id: int = subject_id
        self.status: str = status
        self.result_place_id: int = result_place_id
        self.building: str = building
        self.place: str = place
        self.floor: str = floor
        self.hours: str = hours
        self.works: list = works
        self.teachers: list = teachers


class FullHomeworkFile:
    # noinspection PyShadowingBuiltins
    def __init__(self, id, id_str, name, type_group, type, page_url, download_url, user, size, vote, uploaded_date,
                 storage_type):
        self.id: int = id
        self.id_str: str = id_str
        self.name: str = name
        self.type_group: str = type_group
        self.type: str = type
        self.page_url: str = page_url
        self.download_url: str = download_url
        self.user: FullHomeworkUser = FullHomeworkUser(*list(user.values()))
        self.size: int = size
        self.vote: int = vote
        self.uploaded_date: str = uploaded_date
        self.storage_type: str = storage_type


class FullHomeworkTeacher:
    # noinspection PyShadowingBuiltins
    def __init__(self, id, id_str, user_id, user_id_str, short_name, sex):
        self.id: int = id
        self.id_str: str = id_str
        self.user_id: int = user_id
        self.user_id_str: str = user_id_str
        self.short_name: str = short_name
        self.sex: str = sex


class FullHomework:
    # noinspection PyShadowingBuiltins
    def __init__(self, works, subjects, lessons, files, teachers):
        # self.tasks: list = [FullHomeworkTask(*list(x.values())) for x in tasks]
        # self.user: FullHomeworkUser = FullHomeworkUser(*list(user.values()))
        self.works: list = [FullHomeworkWork(*list(x.values())) for x in works]
        self.subjects: list = [FullHomeworkSubject(*list(x.values())) for x in subjects]
        self.lessons: list = [FullHomeworkLesson(*list(x.values())) for x in lessons]
        self.files: list = [FullHomeworkFile(*list(x.values())) for x in files]
        self.teachers: list = [FullHomeworkTeacher(*list(x.values())) for x in teachers]


class Mark:
    # noinspection PyShadowingBuiltins
    def __init__(self, id, id_str, type, value, text_value, person, person_str, work, work_str, lesson, lesson_str,
                 number, date, work_type, mood, use_avg_calc):
        self.id: int = id
        self.id_str: str = id_str
        self.type: str = type
        self.value: str = value
        self.text_value: str = text_value
        self.person: int = person
        self.person_str: str = person_str
        self.work: int = work
        self.work_str: str = work_str
        self.lesson: int = lesson
        self.lesson_str: str = lesson_str
        self.number: int = number
        self.date: str = date
        self.work_type: int = work_type
        self.mood: str = mood
        self.use_avg_calc: bool = use_avg_calc


class LessonSubject:
    # noinspection PyShadowingBuiltins
    def __init__(self, id, id_str, name, knowledge_area, fgos_subject_id):
        self.id: int = id
        self.id_str: str = id_str
        self.name: str = name
        self.knowledge_area: str = knowledge_area
        self.fgos_subject_id: int = fgos_subject_id


class LessonTask:
    # noinspection PyShadowingBuiltins
    def __init__(self, id, id_str, person, person_str, work, work_str, status, target_date):
        self.id: int = id
        self.id_str: str = id_str
        self.person: int = person
        self.person_str: str = person_str
        self.work: int = work
        self.work_str: str = work_str
        self.status: str = status
        self.target_date: str = target_date


class LessonWork:
    # noinspection PyShadowingBuiltins
    def __init__(self, id, id_str, type, work_type, mark_type, mark_count, lesson, lesson_str, display_in_journal,
                 status, edu_group, edu_group_str, tasks, text, period_number, period_type, subject_id, is_important,
                 target_date, sent_date, created_by, files, one_drive_links):
        self.id: int = id
        self.id_str: str = id_str
        self.type: str = type
        self.work_type: int = work_type
        self.mark_type: str = mark_type
        self.mark_count: int = mark_count
        self.lesson: int = lesson
        self.lesson_str: str = lesson_str
        self.display_in_journal: bool = display_in_journal
        self.status: str = status
        self.edu_group: int = edu_group
        self.edu_group_str: str = edu_group_str
        self.tasks: list = [LessonTask(*list(x.values())) for x in tasks]
        self.text: str = text
        self.period_number: int = period_number
        self.period_type: str = period_type
        self.subject_id: int = subject_id
        self.is_important: bool = is_important
        self.target_date: str = target_date
        self.sent_date: str = sent_date
        self.created_by: int = created_by
        self.files: list = files
        self.one_drive_links: list = one_drive_links


class Lesson:
    # noinspection PyShadowingBuiltins
    def __init__(self, id, id_str, title, date, number, subject, group, status, result_place_id, works, teachers,
                 teachers_str):
        self.id: int = id
        self.id_str: str = id_str
        self.title: str = title
        self.date: str = date
        self.number: int = number
        self.subject: LessonSubject = LessonSubject(*list(subject.values()))
        self.group: int = group
        self.status: str = status
        self.result_place_id: int = result_place_id
        self.works: list = [LessonWork(*list(x.values())) for x in works]
        self.teachers: list = teachers
        self.teachers_str: list = teachers_str


class ScheduleLesson:
    # noinspection PyShadowingBuiltins
    def __init__(self, id, title, date, number, subject_id, status, result_place_id, building, place, floor, hours,
                 works, teachers):
        self.id: int = id
        self.title: str = title
        self.date: str = date
        self.number: int = number
        self.subject_id: int = subject_id
        self.status: str = status
        self.result_place_id: int = result_place_id
        self.building: str = building
        self.place: str = place
        self.floor: str = floor
        self.hours: str = hours
        self.works: list = works
        self.teachers: list = teachers


class ScheduleMark:
    # noinspection PyShadowingBuiltins
    def __init__(self, id, id_str, type, value, text_value, person, person_str, work, work_str, lesson, lesson_str,
                 number, date, work_type, mood, use_avg_calc):
        self.id: int = id
        self.id_str: str = id_str
        self.type: str = type
        self.value: str = value
        self.text_value: str = text_value
        self.person: int = person
        self.person_str: str = person_str
        self.work: int = work
        self.work_str: str = work_str
        self.lesson: int = lesson
        self.lesson_str: str = lesson_str
        self.number: int = number
        self.date: str = date
        self.work_type: int = work_type
        self.mood: str = mood
        self.use_avg_calc: bool = use_avg_calc


class ScheduleWork:
    # noinspection PyShadowingBuiltins
    def __init__(self, id, id_str, type, work_type, mark_type, mark_count, lesson, lesson_str, display_in_journal,
                 status, edu_group, edu_group_str, text, period_number, period_type, subject_id, is_important,
                 target_date, sent_date, created_by, files, one_drive_links):
        self.id: int = id
        self.id_str: str = id_str
        self.type: str = type
        self.work_type: int = work_type
        self.mark_type: str = mark_type
        self.mark_count: int = mark_count
        self.lesson: int = lesson
        self.lesson_str: str = lesson_str
        self.display_in_journal: bool = display_in_journal
        self.status: str = status
        self.edu_group: int = edu_group
        self.edu_group_str: str = edu_group_str
        self.text: str = text
        self.period_number: int = period_number
        self.period_type: str = period_type
        self.subject_id: int = subject_id
        self.is_important: bool = is_important
        self.target_date: str = target_date
        self.sent_date: str = sent_date
        self.created_by: int = created_by
        self.files: list = files
        self.one_drive_links: list = one_drive_links


class ScheduleTask:
    # noinspection PyShadowingBuiltins
    def __init__(self, id, id_str, person, person_str, work, work_str, status, target_date):
        self.id: int = id
        self.id_str: str = id_str
        self.person: int = person
        self.person_str: str = person_str
        self.work: int = work
        self.work_str: str = work_str
        self.status: str = status
        self.target_date: str = target_date


class ScheduleSubject:
    # noinspection PyShadowingBuiltins
    def __init__(self, id, name, knowledge_area_id):
        self.id: int = id
        self.name: str = name
        self.knowledge_area_id: int = knowledge_area_id


class ScheduleWorkType:
    # noinspection PyShadowingBuiltins
    def __init__(self, id, school_id, abbreviation, name, is_final, is_important, kind_id, kind):
        self.id: int = id
        self.school_id: int = school_id
        self.abbreviation: str = abbreviation
        self.name: str = name
        self.is_final: bool = is_final
        self.is_important: bool = is_important
        self.kind_id: int = kind_id
        self.kind: str = kind


class ScheduleLessonLogEntrie:
    # noinspection PyShadowingBuiltins
    def __init__(self, person, lesson, person_str, lesson_str, comment, status, created_date):
        self.person: int = person
        self.lesson: int = lesson
        self.person_str: str = person_str
        self.lesson_str: str = lesson_str
        self.comment: str = comment
        self.status: str = status
        self.created_date: str = created_date


class ScheduleTeacher:
    # noinspection PyShadowingBuiltins
    def __init__(self, person, role):
        self.person: FullHomeworkTeacher = FullHomeworkTeacher(*list(person.values()))
        self.role: str = role


class ScheduleDay:
    # noinspection PyShadowingBuiltins
    def __init__(self, date, lessons, marks, works, homeworks, subjects, work_types, lesson_log_entries, teachers,
                 next_date):
        self.date: str = date
        self.lessons: list = [ScheduleLesson(*list(x.values())) for x in lessons]
        self.marks: list = [ScheduleMark(*list(x.values())) for x in marks]
        self.works: list = [ScheduleWork(*list(x.values())) for x in works]
        self.homeworks: list = [FullHomeworkWork(*list(x.values())) for x in homeworks]
        self.subjects: list = [ScheduleSubject(*list(x.values())) for x in subjects]
        self.work_types: list = [ScheduleWorkType(*list(x.values())) for x in work_types]
        self.lesson_log_entries: list = [ScheduleLessonLogEntrie(*list(x.values())) for x in lesson_log_entries]
        self.teachers: list = [ScheduleTeacher(*list(x.values())) for x in teachers]
        self.next_date: str = next_date


class Schedule:
    # noinspection PyShadowingBuiltins
    def __init__(self, days):
        self.days: list = [ScheduleDay(*list(x.values())) for x in days]


class MosregClient:
    def __init__(self, access_token):
        self.access_token: str = access_token
        self.headers = {
            'Accept': 'application/json',
            'Access-Token': self.access_token,
        }

        self.me: Context = None

    async def get_me(self) -> [Context, MosregException]:
        if not self.me:
            r = await requests.get(base_api_url + "users/me/context", headers=self.headers)
            if r.status_code == 200:
                self.me = Context(*(r.json().values()))
                return self.me

            else:
                raise exception_from_response(r)
        else:
            return self.me

    async def get_context(self, user_id):
        return await get_context(self.access_token, user_id)

    async def get_reporting_periods(self):
        if self.me:
            return await get_reporting_periods(self.access_token, self.me.group_ids[0])
        else:
            await self.get_me()
            return await get_reporting_periods(self.access_token, self.me.group_ids[0])

    async def get_homework_period(self, start_date, end_date):
        if self.me:
            return await get_homework_period(self.access_token, self.me.person_id, self.me.school_ids[0], start_date,
                                             end_date)
        else:
            await self.get_me()
            return await get_homework_period(self.access_token, self.me.person_id, self.me.school_ids[0], start_date,
                                             end_date)

    async def get_marks_period(self, start_date, end_date):
        if self.me:
            return await get_marks_period(self.access_token, self.me.person_id, self.me.group_ids[0], start_date,
                                          end_date)
        else:
            await self.get_me()
            return await get_marks_period(self.access_token, self.me.person_id, self.me.group_ids[0], start_date,
                                          end_date)

    async def get_lessons_period(self, start_date, end_date):
        if self.me:
            return await get_lessons_period(self.access_token, self.me.group_ids[0], start_date, end_date)
        else:
            await self.get_me()
            return await get_lessons_period(self.access_token, self.me.group_ids[0], start_date, end_date)

    async def get_schedule(self, start_date, end_date):
        if self.me:
            return await get_schedule(self.access_token, self.me.person_id, self.me.group_ids[0], start_date, end_date)
        else:
            await self.get_me()
            return await get_schedule(self.access_token, self.me.person_id, self.me.group_ids[0], start_date, end_date)


async def get_context(access_token, user_id) -> [Context, MosregNotFoundException, MosregException]:
    headers = {
        'Accept': 'application/json',
        'Access-Token': access_token,
    }
    r = await requests.get(base_api_url + f"users/{user_id}/context", headers=headers)
    if r.status_code == 200:
        return Context(*(r.json().values()))
    elif r.status_code == 404:
        return MosregNotFoundException(r.json())
    else:
        raise exception_from_response(r)


async def get_reporting_periods(access_token, edu_grp) -> [[ReportingPeriod], MosregException]:
    headers = {
        'Accept': 'application/json',
        'Access-Token': access_token,
    }
    r = await requests.get(base_api_url + f"edu-groups/{edu_grp}/reporting-periods", headers=headers)
    if r.status_code == 200:
        periods = []
        for period in r.json():
            periods.append(ReportingPeriod(*(period.values())))
        return periods
    else:
        raise exception_from_response(r)


async def get_homework_period(access_token, person: int, school: int, start_date: [int, str], end_date: [int, str]) \
        -> [FullHomework, MosregException]:
    headers = {
        'Accept': 'application/json',
        'Access-Token': access_token,
    }
    r = await requests.get(base_api_url + f"persons/{person}/school/{school}/homeworks", headers=headers, params={
        'startDate': anything_to_iso(start_date),
        'endDate': anything_to_iso(end_date),
    })
    if r.status_code == 200:
        return FullHomework(*(r.json().values()))
    else:
        raise exception_from_response(r)


async def get_marks_period(access_token, person: int, group: int, start_date: [int, str], end_date: [int, str]) \
        -> [[Mark], MosregException]:
    headers = {
        'Accept': 'application/json',
        'Access-Token': access_token,
    }
    r = await requests.get(base_api_url + f"persons/{person}/edu-groups/{group}/marks/{start_date}/{end_date}",
                           headers=headers)
    if r.status_code == 200:
        marks = []
        for mark in r.json():
            marks.append(Mark(*(mark.values())))
        return marks
    else:
        raise exception_from_response(r)


async def get_lessons_period(access_token, group: int, start_date: [int, str], end_date: [int, str]) \
        -> [[Lesson], MosregException]:
    headers = {
        'Accept': 'application/json',
        'Access-Token': access_token,
    }
    r = await requests.get(base_api_url + f"edu-groups/{group}/lessons/{start_date}/{end_date}",
                           headers=headers)
    if r.status_code == 200:
        lessons = []
        for lesson in r.json():
            lessons.append(Lesson(*(lesson.values())))
        return lessons
    else:
        raise exception_from_response(r)


async def get_schedule(access_token, person: int, group: int, start_date: [int, str], end_date: [int, str]):
    headers = {
        'Accept': 'application/json',
        'Access-Token': access_token,
    }
    r = await requests.get(base_api_url + f"persons/{person}/groups/{group}/schedules", params={
        'startDate': anything_to_iso(start_date),
        'endDate': anything_to_iso(end_date),
    }, headers=headers)
    if r.status_code == 200:
        return Schedule(*(r.json().values()))
    else:
        raise exception_from_response(r)
