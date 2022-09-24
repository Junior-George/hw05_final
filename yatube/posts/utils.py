from django.core.paginator import Paginator

AMOUNT = 10


def Paginate(request, post_list):
    paginator = Paginator(post_list, AMOUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
