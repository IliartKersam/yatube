from typing import Type

from django.http import HttpRequest
from django.utils import timezone


def year(request: Type[HttpRequest]) -> int:
    """Получаем текущий год."""
    return {
        'year': timezone.now().year
    }
