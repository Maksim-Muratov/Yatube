from django.utils import timezone


def year(request):
    """Добавляет переменную с текущим годом."""
    time = timezone.now()
    return {
        'year': int(time.strftime('%Y'))
    }
