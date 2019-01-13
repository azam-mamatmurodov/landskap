from django_filters import filterset, filters
from apps.users import models as user_models


class CategoryFilter(filterset.Filter):
    is_top = filters.BooleanFilter(name="is_top")

    class Meta:
        model = user_models.Category
        fields = ['is_top']
