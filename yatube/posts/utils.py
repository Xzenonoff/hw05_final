from django.core.paginator import Paginator


def paginate(request, items, NUMBER_OF_POSTS):
    paginator = Paginator(items, NUMBER_OF_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
