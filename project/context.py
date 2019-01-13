from django.template.loader import render_to_string
from django.shortcuts import reverse
from django.utils.translation import ugettext as _
from django.utils.timezone import now
from django.conf import settings
from django.contrib.staticfiles.templatetags.staticfiles import static


from apps.users.models import News
from apps.main.models import Menu

site_logo = static('images/logo.png')


def get_page_data(request, *args, **kwargs):

    view_name = request.resolver_match.view_name
    kwargs = request.resolver_match.kwargs
    page_title = _('Home page')
    paths = list()
    paths.append({
        'title': page_title,
        'path': reverse('users:cafe_list')
    })
    if view_name == 'users:profile':
        page_title = _('Account Settings')
        paths.append({
            'title': _('Account Settings'),
            'path': reverse(view_name)
        })
    elif view_name == 'main:news_list':
        page_title = _('News')
        paths.append({
            'title': page_title,
            'path': reverse(view_name,),
        })
    elif view_name == 'users:cafe_list':
        page_title = _('Cafe list')
        paths.append({
            'title': page_title,
            'path': reverse(view_name,),
        })
    elif view_name == 'users:settings':
        page_title = _('Settings')
        paths.append({
            'title': page_title,
            'path': reverse(view_name,),
        })
    elif view_name == 'users:cafe_detail':
        paths.append({
            'title': _('Cafe list'),
            'path': reverse('users:cafe_list',),
        })
        page_title = _('Cafe detail')
        paths.append({
            'title': page_title,
            'path': reverse(view_name,),
        })
    elif view_name == 'users:cafe_edit':
        args = [kwargs.get('cafe_id')]
        paths.append({
            'title': _('Cafe list'),
            'path': reverse('users:cafe_list',),
        })
        page_title = _('Cafe detail')
        paths.append({
            'title': page_title,
            'path': reverse('users:cafe_detail', args=args),
        })
        page_title = _('Cafe edit')
        paths.append({
            'title': page_title,
            'path': reverse(view_name, args=args),
        })
    elif view_name == 'users:cafe_add':
        paths.append({
            'title': _('Cafe list'),
            'path': reverse('users:cafe_list',),
        })
        page_title = _('Cafe add')
        paths.append({
            'title': page_title,
            'path': reverse('users:cafe_add',),
        })

    elif view_name == 'users:cafe_week_time_page':
        args = [kwargs.get('cafe_id')]
        paths.append({
            'title': _('Cafe list'),
            'path': reverse('users:cafe_list',),
        })
        page_title = _('Cafe detail')
        paths.append({
            'title': page_title,
            'path': reverse('users:cafe_detail', args=args),
        })
        page_title = _('Cafe edit')
        paths.append({
            'title': page_title,
            'path': reverse('users:cafe_edit', args=args),
        })
        page_title = _('Time graphic')
        paths.append({
            'title': page_title,
            'path': reverse(view_name, args=args),
        })

    elif view_name == 'users:cafe_location_page':
        args = [kwargs.get('cafe_id')]
        paths.append({
            'title': _('Cafe list'),
            'path': reverse('users:cafe_list',),
        })
        page_title = _('Cafe detail')
        paths.append({
            'title': page_title,
            'path': reverse('users:cafe_detail', args=args),
        })
        page_title = _('Cafe edit')
        paths.append({
            'title': page_title,
            'path': reverse('users:cafe_edit', args=args),
        })
        page_title = _('Location settings')
        paths.append({
            'title': page_title,
            'path': reverse(view_name, args=args),
        })

    elif view_name == 'users:cafe_gallery':
        args = [kwargs.get('cafe_id')]
        paths.append({
            'title': _('Cafe list'),
            'path': reverse('users:cafe_list',),
        })
        page_title = _('Cafe detail')
        paths.append({
            'title': page_title,
            'path': reverse('users:cafe_detail', args=args),
        })
        page_title = _('Cafe edit')
        paths.append({
            'title': page_title,
            'path': reverse('users:cafe_edit', args=args),
        })
        page_title = _('Gallery list')
        paths.append({
            'title': page_title,
            'path': reverse(view_name, args=args),
        })

    elif view_name == 'users:cafe_gallery_add':
        args = [kwargs.get('cafe_id')]
        paths.append({
            'title': _('Cafe list'),
            'path': reverse('users:cafe_list',),
        })
        page_title = _('Cafe detail')
        paths.append({
            'title': page_title,
            'path': reverse('users:cafe_detail', args=args),
        })
        page_title = _('Cafe edit')
        paths.append({
            'title': page_title,
            'path': reverse('users:cafe_edit', args=args),
        })
        page_title = _('Gallery list')
        paths.append({
            'title': page_title,
            'path': reverse('users:cafe_gallery', args=args),
        })
        page_title = _('Gallery add')
        paths.append({
            'title': page_title,
            'path': reverse(view_name, args=args),
        })

    elif view_name == 'users:cafe_gallery_delete':
        args = [kwargs.get('cafe_id')]
        paths.append({
            'title': _('Cafe list'),
            'path': reverse('users:cafe_list',),
        })
        page_title = _('Cafe detail')
        paths.append({
            'title': page_title,
            'path': reverse('users:cafe_detail', args=args),
        })
        page_title = _('Cafe edit')
        paths.append({
            'title': page_title,
            'path': reverse('users:cafe_edit', args=args),
        })
        page_title = _('Gallery list')
        paths.append({
            'title': page_title,
            'path': reverse('users:cafe_gallery', args=args),
        })
        page_title = _('Gallery delete')
        args.append(kwargs.get('file_id'))
        paths.append({
            'title': page_title,
            'path': reverse(view_name, args=args),
        })

    elif view_name == 'main:news_detail':

        news_list_title = _('News')
        paths.append({
            'title': news_list_title,
            'path': reverse('main:news_list'),
        })

        arg = kwargs.get('slug')
        news_content = News.objects.get(translations__slug=arg)
        page_title = news_content.name
        paths.append({
            'title': page_title,
            'path': reverse(view_name, args=[arg]),
        })

    elif view_name == 'products:product_list':
        page_title = _('Product list')
        paths.append({
            'title': page_title,
            'path': reverse(view_name,),
        })
    elif view_name == 'products:product_create':
        page_title = _('Product list')
        paths.append({
            'title': page_title,
            'path': reverse('products:product_list',),
        })
        page_title = _('Product create')
        paths.append({
            'title': page_title,
            'path': reverse(view_name,),
        })
    elif view_name == 'products:product_detail':
        args = [kwargs.get('pk')]
        page_title = _('Product list')
        paths.append({
            'title': page_title,
            'path': reverse('products:product_list',),
        })
        page_title = _('Product detail info')
        paths.append({
            'title': page_title,
            'path': reverse(view_name, args=args),
        })
    elif view_name == 'products:product_edit':
        args = [kwargs.get('pk')]
        page_title = _('Product list')
        paths.append({
            'title': page_title,
            'path': reverse('products:product_list',),
        })
        page_title = _('Product detail info')
        paths.append({
            'title': page_title,
            'path': reverse('products:product_detail', args=args),
        })
        page_title = _('Product edit')
        paths.append({
            'title': page_title,
            'path': reverse('products:product_edit', args=args),
        })
    elif view_name == 'products:product_delete':
        args = [kwargs.get('pk')]
        page_title = _('Product list')
        paths.append({
            'title': page_title,
            'path': reverse('products:product_list',),
        })
        page_title = _('Product detail info')
        paths.append({
            'title': page_title,
            'path': reverse('products:product_detail', args=args),
        })
        page_title = _('Product edit')
        paths.append({
            'title': page_title,
            'path': reverse('products:product_edit', args=args),
        })
        page_title = _('Product delete')
        paths.append({
            'title': page_title,
            'path': reverse(view_name, args=args),
        })
    elif view_name == 'users:employee_list':
        page_title = _('Employee list')
        paths.append({
            'title': page_title,
            'path': reverse(view_name, ),
        })
    elif view_name == 'users:employee_edit':
        args = [kwargs.get('employee_id')]
        page_title = _('Employee list')
        paths.append({
            'title': page_title,
            'path': reverse('users:employee_list', ),
        })
        page_title = _('Employee edit')
        paths.append({
            'title': page_title,
            'path': reverse(view_name, args=args),
        })
    elif view_name == 'users:employee_add':
        page_title = _('Employee list')
        paths.append({
            'title': page_title,
            'path': reverse('users:employee_list', ),
        })
        page_title = _('New Employee')
        paths.append({
            'title': page_title,
            'path': reverse(view_name, ),
        })
    elif view_name == 'users:employee_delete':
        args = [kwargs.get('employee_id')]
        page_title = _('Employee list')
        paths.append({
            'title': page_title,
            'path': reverse('users:employee_list', ),
        })
        page_title = _('Delete Employee')
        paths.append({
            'title': page_title,
            'path': reverse(view_name, args=args),
        })
    elif view_name == 'users:employee_add_existing':
        page_title = _('Employee list')
        paths.append({
            'title': page_title,
            'path': reverse('users:employee_list', ),
        })
        page_title = _('Add existing employee')
        paths.append({
            'title': page_title,
            'path': reverse(view_name),
        })
    return {'paths': paths, 'page_title': page_title}


def get_breadcrumbs(request, *args, **kwargs):
    page_data = get_page_data(request, *args, **kwargs)
    return render_to_string('parts/breadcrumbs.html', page_data)


def get_header(request):
    context = dict()
    context['request'] = request
    context['menu_items'] = Menu.objects.order_by('order')
    context['site_name'] = settings.SITE_NAME
    context['site_logo'] = site_logo
    return render_to_string('parts/main_header.html', context=context)


def get_footer(request):
    context = dict()
    context['request'] = request
    context['now'] = now()
    context['site_logo'] = site_logo
    return render_to_string('parts/footer.html', context=context)


def defaults(request, *args, **kwargs):
    breadcrumbs = get_breadcrumbs(request, *args, **kwargs)
    header = get_header(request)
    footer = get_footer(request)
    site_name = settings.SITE_NAME
    page_title = get_page_data(request, *args, **kwargs).get('page_title')
    return locals()
