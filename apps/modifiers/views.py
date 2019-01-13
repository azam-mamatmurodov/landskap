from django.views import generic
from django.shortcuts import redirect, reverse, get_object_or_404, Http404
from django.db import transaction

from apps.modifiers import models as modifier_models
from apps.modifiers import forms as modifier_forms
from apps.users import models as user_models


class ModifierListView(generic.ListView):
    template_name = 'pages/modifiers/modifier_list.html'
    model = modifier_models.Modifier
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = modifier_models.ModifierCategory.objects.all()
        return context

    def get_queryset(self):
        return self.model.objects.filter(owner=self.request.user)


class ModifierCatListView(generic.ListView):
    template_name = 'pages/modifiers/modifier_list.html'
    model = modifier_models.Modifier
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = modifier_models.ModifierCategory.objects.all()
        if self.kwargs.get('cat_id'):
            context['cat_id'] = self.kwargs.get('cat_id')
        return context

    def get_queryset(self):
        if self.kwargs.get('cat_id'):
            return self.model.objects.filter(owner=self.request.user, category_id=self.kwargs.get('cat_id'))
        else:
            return self.model.objects.filter(owner=self.request.user)


class ModifierCatDetailView(generic.DetailView):
    template_name = 'pages/modifiers/modifier_cat_detail.html'
    model = modifier_models.Modifier


class ModifierCatCreateView(generic.CreateView):
    template_name = 'pages/modifiers/modifier_cat_create.html'
    model = modifier_models.ModifierCategory
    fields = ['title', 'is_top', 'available', 'is_single', 'required', ]

    # def get_context_data(self, **kwargs):
    #     context = super(ModifierCatCreateView, self).get_context_data(**kwargs)
    #
    #     return context

    def form_valid(self, form):
        context = self.get_context_data()
        with transaction.atomic():
            instance = form.save(commit=False)
            instance.owner = self.request.user
            instance.save()
            self.object = instance

        return super(ModifierCatCreateView, self).form_valid(form)


class ModifierCatDeleteView(generic.DeleteView):
    template_name = 'pages/modifiers/modifier_cat_delete.html'
    model = modifier_models.Modifier

    def get_success_url(self):
        return reverse('modifiers:modifier_cat_list')


class ModifierCatEditView(generic.UpdateView):
    template_name = 'pages/modifiers/modifier_edit.html'
    model = modifier_models.Modifier
    fields = ['title', 'price', 'available', 'category', ]

    def get_context_data(self, **kwargs):
        context = super(ModifierCatEditView, self).get_context_data(**kwargs)
        context['cafes'] = user_models.Cafe.objects.filter(user=self.request.user)

        cafe_meals = modifier_models.CafeModifiers.objects.filter(modifier_id=self.object.id)
        if cafe_meals.exists():
            context['selected_cafes'] = cafe_meals.prefetch_related('cafe').values_list('cafe', flat=True)
        return context

    def form_valid(self, form):
        print(form.data.get('description'))
        form.save()
        context = self.get_context_data()
        cafes = self.request.POST.getlist('cafe')
        instance = self.get_object()
        if cafes:
            cafe_meals = modifier_models.CafeModifiers.objects.filter(modifier_id=instance.id)
            if cafe_meals.exists():
                cafe_meals.delete()
            for cafe in cafes:
                cafe_meal = modifier_models.CafeModifiers(cafe_id=cafe, modifier_id=instance.id)
                cafe_meal.save()
        return super().form_valid(form)


class ModifierListView(generic.ListView):
    template_name = 'pages/modifiers/modifier_cat_list.html'
    model = modifier_models.Modifier
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = modifier_models.ModifierCategory.objects.all()
        return context

    def get_queryset(self):
        return self.model.objects.filter(owner=self.request.user, category_id=self.kwargs.get('cat_id'))


class ModifierDetailView(generic.DetailView):
    template_name = 'pages/modifiers/modifier_detail.html'
    model = modifier_models.Modifier


class ModifierCreateView(generic.CreateView):
    template_name = 'pages/modifiers/modifier_create.html'
    model = modifier_models.Modifier
    fields = ['title', 'price', 'available', 'category', ]

    # def get_context_data(self, **kwargs):
    #     context = super(ModifierCreateView, self).get_context_data(**kwargs)
    #
    #     return context

    def form_valid(self, form):
        # context = self.get_context_data()
        # cafes = self.request.POST.getlist('cafe')
        with transaction.atomic():
            instance = form.save(commit=False)
            instance.owner = self.request.user
            instance.save()
            self.object = instance

            # if cafes:
            #     cafe_meals = modifier_models.CafeModifiers.objects.filter(modifier_id=instance.id)
            #     if cafe_meals.exists():
            #         cafe_meals.delete()
            #     for cafe in cafes:
            #         cafe_meal = modifier_models.CafeModifiers(cafe_id=cafe, modifier_id=instance.id)
            #         cafe_meal.save()
        return super(ModifierCreateView, self).form_valid(form)


class ModifierDeleteView(generic.DeleteView):
    template_name = 'pages/modifiers/modifier_cat_delete.html'
    model = modifier_models.Modifier

    def get_success_url(self):
        return reverse('modifiers:modifier_list')


class ModifierEditView(generic.UpdateView):
    template_name = 'pages/modifiers/modifier_cat_edit.html'
    model = modifier_models.Modifier
    fields = ['title', 'price', 'available', 'category', ]

    def get_context_data(self, **kwargs):
        context = super(ModifierEditView, self).get_context_data(**kwargs)
        return context

    def form_valid(self, form):
        print(form.data.get('description'))
        form.save()
        context = self.get_context_data()
        instance = self.get_object()
        return super().form_valid(form)
