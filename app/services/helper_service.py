import datetime


class DateTimeHelper:

    @staticmethod
    def get_duration_in_s(started_at, completed_at) -> str:
        duration = None
        if started_at and completed_at:
            duration = int((datetime.datetime.fromisoformat(completed_at.rstrip('Z'))
                     - datetime.datetime.fromisoformat(
                         started_at.rstrip('Z'))).total_seconds())
        return duration