from datetime import datetime


def year(request):
    """Добавляет переменную с текущим годом."""
    time: int = datetime.now().timetuple()
    return {
        'year': int(time[0])
    }
