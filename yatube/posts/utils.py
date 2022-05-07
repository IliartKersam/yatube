from typing import Type

from django.conf import settings
from django.core.paginator import Paginator, Page
from django.db.models.query import QuerySet
from django.http import HttpRequest


def pag_posts(request: Type[HttpRequest],
              post_list: Type[QuerySet]) -> Type[Page]:
    """Функция принимает запрос и список постов, выводит разделение постов
    по страницам, максимальное количество постов на странице берется
    из параметра MP_IN_LIST."""
    paginator = Paginator(post_list, settings.MP_IN_LIST)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
