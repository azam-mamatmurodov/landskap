from django import forms


from apps.products.models import Product, ProductImage


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        exclude = ('order', )


AlbumFormSet = forms.inlineformset_factory(Product, ProductImage,
                                           form=ProductImageForm,
                                           extra=5,
                                           can_order=False,
                                           max_num=5)
