from datetime import datetime, timedelta

from django.views import generic
from django.views.generic.edit import FormMixin, FormView, CreateView
from django.utils.translation import ugettext as _
from django.shortcuts import redirect

from apps.users.forms import ReviewForm
from apps.users.models import Review


one_week_ago = datetime.today() - timedelta(days=7)


class ReviewsView(generic.ListView, FormView):
    template_name = 'pages/reviews.html'
    model = Review
    paginate_by = 10
    title = _('Latest reviews')
    queryset = Review.objects.filter(parent=None)
    form_class = ReviewForm

    def get_queryset(self):
        self.queryset = self.queryset.filter(cafe__user=self.request.user)
        review_type = self.kwargs.get('review_type')
        if review_type == 'responded':
            self.title = _('Responded reviews')
            queryset = self.queryset.filter(review_parent__isnull=False).distinct()
        elif review_type == 'not-responded':
            self.title = _('Not responded reviews')
            queryset = self.queryset.filter(review_parent__isnull=True).distinct()
        else:
            self.title = _('Latest reviews')
            queryset = self.queryset
        return queryset.order_by('-pk')

    def get_context_data(self, **kwargs):
        queryset = self.queryset.filter(cafe__user=self.request.user)

        context = super().get_context_data(**kwargs)
        context['object_list'] = self.object_list
        context['title'] = self.title
        context['new_reviews_within_week'] = queryset.filter(created_at__gte=one_week_ago).count()
        context['responded_reviews_within_week'] = queryset.filter(created_at__gte=one_week_ago,
                                                                   review_parent__isnull=False).count()
        context['un_responded_reviews_within_week'] = queryset.filter(created_at__gte=one_week_ago,
                                                                      review_parent__isnull=True).count()
        context['total_reviews_within_week'] = queryset.filter(created_at__gte=one_week_ago).count()

        return context

    def form_valid(self, form):
        parent_id = form.data.get('parent')
        comment = form.data.get('comment')

        new_review = Review()
        new_review.author = self.request.user
        new_review.parent_id = parent_id
        new_review.company_id = self.request.user.company.id
        new_review.comment = comment
        new_review.save()

        full_path = self.request.get_full_path()
        return redirect(to=full_path)