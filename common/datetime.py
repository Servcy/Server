from datetime import datetime, timedelta


def future_date_in_iso_formate(days: int, with_microseconds: bool = False) -> str:
    """
    Function to get date in future in ISO format
    """
    future_date = datetime.now() + timedelta(days=days)
    date_format = "%Y-%m-%dT%H:%M:%SZ"
    if with_microseconds:
        date_format = "%Y-%m-%dT%H:%M:%S.%fZ"
    return datetime.strftime(future_date, date_format)
