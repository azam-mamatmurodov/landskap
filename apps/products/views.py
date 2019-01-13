from django.views import generic
from django.shortcuts import redirect, reverse, get_object_or_404, Http404
from django.db import transaction

from apps.products import models as product_models
from apps.modifiers import models as modifier_models
from apps.products import forms as product_forms
from apps.users import models as user_models


class ProductListView(generic.ListView):
    template_name = 'pages/products/product_list.html'
    model = product_models.Product
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = product_models.ProductCategory.objects.all()
        return context

    def get_queryset(self):
        return self.model.objects.filter(owner=self.request.user)


class ProductCatListView(generic.ListView):
    template_name = 'pages/products/product_list.html'
    model = product_models.Product
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = product_models.ProductCategory.objects.all()
        return context

    def get_queryset(self):
        return self.model.objects.filter(owner=self.request.user, category_id=self.kwargs.get('cat_id'))


class ProductDetailView(generic.DetailView):
    template_name = 'pages/products/product_detail.html'
    model = product_models.Product


class ProductCreateView(generic.CreateView):
    template_name = 'pages/products/product_create.html'
    model = product_models.Product
    fields = ['image', 'title', 'description', 'price', 'available', 'category', ]

    def get_context_data(self, **kwargs):
        context = super(ProductCreateView, self).get_context_data(**kwargs)
        context['cafes'] = product_models.Cafe.objects.filter(user=self.request.user)
        context['modifiers'] = modifier_models.ModifierCategory.objects.all()

        cafes = self.request.POST.getlist('cafe')
        if cafes:
            context['selected_cafes'] = cafes
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        cafes = self.request.POST.getlist('cafe')
        modifiers = self.request.POST.getlist('modifier')
        with transaction.atomic():
            instance = form.save(commit=False)
            instance.owner = self.request.user
            instance.save()
            self.object = instance

            if modifiers:
                product_modifiers = product_models.ProductModifier.objects.filter(product_id=instance.id)
                if product_modifiers.exists():
                    product_modifiers.delete()
                for modifier in modifiers:
                    product_modifier = product_models.ProductModifier(product_id=instance.id, modifier_id=modifier)
                    product_modifier.save()

            if cafes:
                cafe_meals = product_models.CafeMeals.objects.filter(product_id=instance.id)
                if cafe_meals.exists():
                    cafe_meals.delete()
                for cafe in cafes:
                    cafe_meal = product_models.CafeMeals(cafe_id=cafe, product_id=instance.id)
                    cafe_meal.save()


class ProductDeleteView(generic.DeleteView):
    template_name = 'pages/products/product_delete.html'
    model = product_models.Product

    def get_success_url(self):
        return reverse('products:product_list')


class ProductEditView(generic.UpdateView):
    template_name = 'pages/products/product_edit.html'
    model = product_models.Product
    fields = ['image', 'title', 'description', 'price', 'available', 'category', ]

    def get_context_data(self, **kwargs):
        context = super(ProductEditView, self).get_context_data(**kwargs)
        context['cafes'] = user_models.Cafe.objects.filter(user=self.request.user)
        context['modifiers'] = modifier_models.ModifierCategory.objects.all()

        product_modifiers = product_models.ProductModifier.objects.filter(product_id=self.object.id)
        if product_modifiers.exists():
            context['selected_modifiers'] = product_modifiers.prefetch_related('modifier').values_list('modifier',
                                                                                                       flat=True)

        cafe_meals = product_models.CafeMeals.objects.filter(product_id=self.object.id)
        if cafe_meals.exists():
            context['selected_cafes'] = cafe_meals.prefetch_related('cafe').values_list('cafe', flat=True)
        return context

    def form_valid(self, form):
        print(form.data.get('description'))
        form.save()
        context = self.get_context_data()
        cafes = self.request.POST.getlist('cafe')
        modifiers = self.request.POST.getlist('modifier')
        instance = self.get_object()
        if modifiers:
            product_modifiers = product_models.ProductModifier.objects.filter(product_id=instance.id)
            if product_modifiers.exists():
                product_modifiers.delete()
            for modifier in modifiers:
                product_modifier = product_models.ProductModifier(product_id=instance.id, modifier_id=modifier)
                product_modifier.save()

        if cafes:
            cafe_meals = product_models.CafeMeals.objects.filter(product_id=instance.id)
            if cafe_meals.exists():
                cafe_meals.delete()
            for cafe in cafes:
                cafe_meal = product_models.CafeMeals(cafe_id=cafe, product_id=instance.id)
                cafe_meal.save()
            return super().form_valid(form)

        return super(ProductCreateView, self).form_valid(form)
