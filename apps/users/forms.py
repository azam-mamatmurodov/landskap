from django import forms
from django.contrib.auth import get_user_model
from django.forms.models import inlineformset_factory

from apps.users import models as user_models

User = get_user_model()


class LoginForm(forms.Form):
    username = forms.CharField(max_length=60)
    passwd = forms.CharField(widget=forms.PasswordInput(), max_length=60)

    def clean(self):
        clean_data = super().clean()
        return clean_data


class RegisterForm(forms.ModelForm):

    class Meta:
        model = User
        fields = '__all__'


class FileUploadForm(forms.ModelForm):

    class Meta:
        model = user_models.File
        fields = ['file']


class AlbumForm(forms.ModelForm):
    class Meta:
        model = user_models.Album
        fields = '__all__'


FileUploadFormSet = inlineformset_factory(user_models.Album, user_models.File, form=FileUploadForm, extra=4)


class ReviewForm(forms.ModelForm):
    comment = forms.CharField(widget=forms.Textarea(attrs={'class': 'chats-area'}), label='')

    class Meta:
        model = user_models.Review
        fields = ['comment', 'parent', ]


class CategoryForm(forms.ModelForm):
    class Meta:
        model = user_models.Category
        exclude = []


class NotificationsAdminForm(forms.Form):
    text = forms.CharField(widget=forms.Textarea())
    count = forms.IntegerField(max_value=100)
    user_type = forms.ChoiceField(choices=User.USER_TYPE_CHOICES)


class NewsForm(forms.ModelForm):
    class Meta:
        model = user_models.News
        exclude = ('owner', )


class CafeAddForm(forms.ModelForm):
    class Meta:
        model = user_models.Cafe
        exclude = ('user', 'status', )


class EmployeeForm(forms.ModelForm):
    cafe = forms.ModelChoiceField(queryset=user_models.Cafe.objects.all())

    class Meta:
        model = User
        fields = ('avatar', 'phone', 'email', 'first_name', 'last_name', 'date_of_birthday', 'gender', 'is_can_reject')


class EmployeeAddForm(EmployeeForm):
    password = forms.CharField(widget=forms.PasswordInput())


class EmployeeAddExistingForm(forms.Form):
    phone = forms.CharField()
    cafe = forms.ModelChoiceField(queryset=user_models.Cafe.objects.all())

    def clean(self):
        cleaned_data = super().clean()
        phone = cleaned_data.get('phone')
        user = User.objects.filter(phone=phone)
        if not user.exists():
            self.add_error('phone', 'User not exists')

        cashier = user_models.Cashier.objects.filter(cashier__phone=phone)
        if cashier.exists():
            self.add_error('phone', 'User already has cafe')
        return cleaned_data


class CafeAddNewForm(forms.ModelForm):
    address = forms.CharField()
    second_address = forms.CharField()
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}))

    class Meta:
        model = user_models.Cafe
        exclude = ('user', 'location', 'status')


class UserForm(forms.ModelForm):
    date_of_birthday = forms.DateField(widget=forms.DateInput())

    class Meta:
        model = User
        fields = ('avatar', 'email', 'first_name', 'last_name', 'date_of_birthday', 'gender', )


class CafeGeneralSettingsForm(forms.ModelForm):
    # show_reviews = forms.ChoiceField(choices=((1, 'Show', ), (0, 'Hide', ), ), widget=forms.RadioSelect(),)

    class Meta:
        model = user_models.CafeGeneralSettings
        exclude = ('owner', )


class EmployeePasswordForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput())
    confirm_password = forms.CharField(widget=forms.PasswordInput())
