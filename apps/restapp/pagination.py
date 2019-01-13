from rest_framework import pagination


class CafesPagination(pagination.PageNumberPagination):
    page_size = 15


class CafeReviewsPagination(pagination.PageNumberPagination):
    page_size = 5
