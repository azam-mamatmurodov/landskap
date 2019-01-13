import ast
import requests

from django.utils import timezone
from django.db.models import Avg, Q, Sum, Count
from django.shortcuts import get_object_or_404, Http404
from django.conf import settings

import stripe
import stripe.error
import braintree
from authy.api import AuthyApiClient
from django_filters.rest_framework import DjangoFilterBackend
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from rest_framework import (
    viewsets,
    permissions,
    response,
    status,
    generics,
    views,
    filters
)
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token

from project.tasks import send_free_item_expire_notifications
from project import modules as project_modules
from apps.users import models as user_models
from apps.products import models as product_models
from apps.orders import models as order_models
from apps.payment import models as payment_models
from apps.restapp import serializers as rest_serializers
from apps.restapp import pagination
from apps.restapp import permissions as rest_permissions
from apps.restapp import filters as rest_filters


class CafesView(generics.ListAPIView):
    serializer_class = rest_serializers.CafesSerializer
    queryset = user_models.Cafe.objects.filter(status=user_models.Cafe.ACTIVE)
    filter_fields = ['category', ]
    search_fields = ['cafe_name', 'address', 'description', ]
    pagination_class = pagination.CafesPagination

    def get_queryset(self):
        if self.request.GET.get('rate'):
            rate = self.request.GET.get('rate', 0)
            self.queryset = self.queryset.annotate(total_rate=Avg('review__rate')).filter(
                Q(total_rate__lte=rate) | Q(total_rate=None))
        if self.request.GET.get('states'):
            now = timezone.now().time()
            states = self.request.GET.get('states').split(',')
            open_cafes = closed_cafes = unknown_cafes = list()

            current_day_available_cafes_queryset = \
                user_models.WeekTime.objects.filter(day=rest_serializers.current_week_day)

            if states.__contains__('open'):
                query = Q(opening_time__lte=now, closing_time__gte=now)
                open_cafes = current_day_available_cafes_queryset.filter(query).values_list('cafe', flat=True)
            if states.__contains__('closed'):
                query = Q(opening_time__lte=now, closing_time__gte=now)
                open_cafes_queryset = current_day_available_cafes_queryset.filter(query).values_list('cafe', flat=True)
                closed_cafes_queryset = current_day_available_cafes_queryset.values_list('cafe', flat=True)
                closed_cafes = list(set(closed_cafes_queryset) - set(open_cafes_queryset))

            if states.__contains__('unknown'):
                current_day_available_cafes = \
                    current_day_available_cafes_queryset.distinct('cafe').values_list('cafe', flat=True)
                unknown_cafes = self.queryset.exclude(pk__in=current_day_available_cafes).values_list('id', flat=True)
            all_cafes = list(open_cafes) + list(closed_cafes) + list(unknown_cafes)
            self.queryset = self.queryset.filter(pk__in=all_cafes)
        return self.queryset


class CafesNearByView(generics.ListAPIView):
    serializer_class = rest_serializers.CafesNearBySerializer
    queryset = user_models.Cafe.objects.filter(status=user_models.Cafe.ACTIVE)
    filter_fields = ['category', ]
    search_fields = ['cafe_name', 'address', 'description', ]

    def get_queryset(self):
        queryset = super().get_queryset()
        distance = self.request.GET.get('distance')
        latitude = self.request.GET.get('latitude')
        longitude = self.request.GET.get('longitude')

        if distance and latitude and longitude:
            kwargs = dict()
            if self.request.GET.get('rate'):
                rate = self.request.GET.get('rate', 0)
                kwargs.update({'rate': rate})

            if self.request.GET.get('states'):
                kwargs.update({'states': self.request.GET.get('states')})

            queryset = queryset.get_nearby_locations(distance=float(distance), location_lat_long=(float(latitude),
                                                                                                  float(longitude)),
                                                     **kwargs)
        else:
            queryset = queryset.none()
        return queryset


class CafesNearByForUserView(generics.ListAPIView):
    serializer_class = rest_serializers.CafesForUserSerializer
    queryset = user_models.Cafe.objects.filter(status=user_models.Cafe.ACTIVE)
    filter_fields = ['category', ]
    search_fields = ['cafe_name', 'address', 'description', ]

    def get_queryset(self):

        distance = self.request.GET.get('distance')
        latitude = self.request.GET.get('latitude')
        longitude = self.request.GET.get('longitude')

        if distance and latitude and longitude:
            kwargs = dict()
            if self.request.GET.get('rate'):
                rate = self.request.GET.get('rate', 0)
                kwargs.update({'rate': rate})

            if self.request.GET.get('states'):
                kwargs.update({'states': self.request.GET.get('states')})

            queryset = user_models.Cafe.objects.get_nearby_locations(distance=float(distance),
                                                                     location_lat_long=(
                                                                         float(latitude), float(longitude)),
                                                                     **kwargs)
        else:
            queryset = user_models.Cafe.objects.none()
        return queryset


class CafeDetailView(generics.RetrieveAPIView):
    serializer_class = rest_serializers.CafesSerializer

    def get_object(self):
        pk = self.kwargs.get('cafe_id')
        return get_object_or_404(user_models.Cafe, pk=pk)


class CafeDetailForUserView(generics.RetrieveAPIView):
    serializer_class = rest_serializers.CafesForUserSerializer

    def get_object(self):
        pk = self.kwargs.get('cafe_id')
        return get_object_or_404(user_models.Cafe, pk=pk)


class CafeFilesView(generics.ListAPIView):
    serializer_class = rest_serializers.CafeFilesSerializer

    def get_queryset(self):
        cafe = user_models.Cafe.objects.get(pk=self.kwargs.get('cafe_id'))
        files = user_models.File.objects.filter(album__cafe=cafe, album__owner=cafe.user).order_by('-pk')
        return files


class CafeReviewView(generics.ListAPIView):
    serializer_class = rest_serializers.ReviewSerializer
    queryset = user_models.Review.objects.filter(parent=None)
    pagination_class = pagination.CafeReviewsPagination

    def get_queryset(self):
        cafe = user_models.Cafe.objects.get(pk=self.kwargs.get('cafe_id'))
        root_cafe = cafe.user.settings
        reviews = self.queryset.none()
        if root_cafe.show_reviews:
            reviews = self.queryset.filter(cafe=self.kwargs.get('cafe_id')).order_by('-pk')
        return reviews


class CafeReviewForUserView(generics.ListAPIView):
    serializer_class = rest_serializers.ReviewSerializerForUser
    queryset = user_models.Review.objects.filter(parent=None)

    def get_queryset(self):
        cafe = user_models.Cafe.objects.get(pk=self.kwargs.get('cafe_id'))
        root_cafe = cafe.user.settings
        reviews = self.queryset.none()
        if root_cafe.show_reviews:
            reviews = self.queryset.filter(cafe=self.kwargs.get('cafe_id')).order_by('-pk')
        return reviews


class CafeReviewCreateView(generics.CreateAPIView, ):
    serializer_class = rest_serializers.ReviewCreateSerializer


class CafeReviewRUD(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = rest_serializers.ReviewReadUpdateDestroySerializer
    lookup_url_kwarg = ['review_id']

    def get_object(self):
        review = user_models.Review.objects.get(pk=self.kwargs.get('review_id'))
        if not review.album:
            review.album = user_models.Album.objects.create(**{
                'owner': review.author,
                'cafe': review.cafe
            })
        return review


class ReviewsView(viewsets.ModelViewSet):
    serializer_class = rest_serializers.ReviewSerializer
    queryset = user_models.Review.objects.all()
    filter_backends = (DjangoFilterBackend,)


class ReviewAllFilesView(generics.ListAPIView):
    serializer_class = rest_serializers.ReviewFileUploadSerializer
    queryset = user_models.File.objects.all()

    def get_queryset(self):
        cafe = user_models.Cafe.objects.get(pk=self.kwargs.get('cafe_id'))
        return self.queryset.filter(album__cafe=cafe).exclude(album__owner=cafe.user).order_by('-pk')


class ReviewFilesView(generics.ListAPIView):
    serializer_class = rest_serializers.ReviewFileUploadSerializer
    queryset = user_models.File.objects.all()

    def get_queryset(self):
        review = user_models.Review.objects.get(pk=self.kwargs.get('review_id'))
        return self.queryset.filter(album=review.album).order_by('-pk')


class ReviewFilesUploadView(generics.CreateAPIView):
    serializer_class = rest_serializers.ReviewFileUploadSerializer


class CategoryView(generics.ListAPIView):
    serializer_class = rest_serializers.CategorySerializer
    queryset = user_models.Category.objects.filter(parent=None)


class CategoryTopView(generics.ListAPIView):
    serializer_class = rest_serializers.CategoryTopSerializer
    queryset = user_models.Category.objects.filter(is_top=1)


class BookmarkView(generics.ListAPIView):
    serializer_class = rest_serializers.BookmarkListSerializer

    def get_queryset(self):
        phone = self.kwargs.get('phone')
        return user_models.Bookmarks.objects.filter(user__phone=phone).order_by('-pk')


class BookmarkCreateView(views.APIView):
    serializer_class = rest_serializers.BookmarkSerializer

    def post(self, request, *args, **kwargs):
        phone = kwargs.get('phone')
        user = user_models.User.objects.get(phone=phone)
        ids = request.POST.get('cafe_ids', None)
        if ids:
            cafe_ids = ast.literal_eval(ids)
            if user_models.Cafe.objects.filter(pk__in=cafe_ids).exists():
                objs = [user_models.Bookmarks(user=user, cafe_id=cafe_id) for cafe_id in cafe_ids]
                user_models.Bookmarks.objects.bulk_create(objs=objs)
                msg = "Successful created"
            else:
                msg = "Some cafe are not exist, please check your data"
        else:
            msg = "Error while creating bookmarks, please check your data"
        return response.Response({"status": "success", "message": [msg]}, status=status.HTTP_200_OK)


class BookmarkDestroyView(views.APIView):
    authentication_classes = [TokenAuthentication, ]
    model = user_models.Bookmarks

    def post(self, request, *args, **kwargs):
        cafe_ids = request.POST.get('cafe_ids', None)
        if cafe_ids:
            ids = ast.literal_eval(cafe_ids)
            user_models.Bookmarks.objects.filter(cafe_id__in=ids, user__phone=self.kwargs.get('phone')).delete()
            msg = 'Successful removed'
        else:
            msg = 'Can not remove'
        return response.Response({"status": "success", "message": [msg]}, status=status.HTTP_200_OK)


class UserListView(generics.ListAPIView):
    serializer_class = rest_serializers.UserSerializer
    queryset = user_models.User.objects.all()


class UserReviewListView(generics.ListAPIView):
    serializer_class = rest_serializers.ReviewSerializer
    queryset = user_models.Review.objects.all()

    def get_queryset(self):
        return self.queryset.filter(author__phone=self.kwargs.get('phone')).order_by('-pk')


class UserRetrieveView(generics.RetrieveAPIView):
    serializer_class = rest_serializers.UserSerializer
    model = user_models.User

    def get_object(self):
        return get_object_or_404(user_models.User, phone=self.kwargs.get('phone'))


class UserNotificationsView(generics.ListAPIView):
    model = user_models.Notifications
    serializer_class = rest_serializers.NotificationsSerializer

    def get_queryset(self):
        phone = self.kwargs.get('phone')
        return self.model.objects.filter(user__phone=phone).order_by('-pk')


class UserNotificationsClearView(generics.DestroyAPIView):
    model = user_models.Notifications
    serializer_class = rest_serializers.NotificationsSerializer
    lookup_url_kwarg = ['phone']

    def get_queryset(self):
        phone = self.kwargs.get('phone')
        return self.model.objects.filter(user__phone=phone).order_by('-pk')

    def destroy(self, request, *args, **kwargs):
        query_set = self.get_queryset()
        query_set.delete()
        return response.Response(status.HTTP_204_NO_CONTENT)


class UserNotificationsUpdateView(generics.UpdateAPIView):
    model = user_models.Notifications
    serializer_class = rest_serializers.NotificationsSerializer
    lookup_url_kwarg = ['notification_id']

    def get_object(self):
        return get_object_or_404(self.model, pk=self.kwargs.get('notification_id'))

    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        return response.Response({"status": "success", "message": ["Successful updated"]})


class UserRecentlyViewedListView(generics.ListAPIView):
    serializer_class = rest_serializers.CafesSerializer
    model = user_models.RecentlyViewed

    def get_queryset(self):
        viewed_cafes = self.model.objects.filter(user__phone=self.kwargs.get('phone')).values_list('cafe')
        return user_models.Cafe.objects.filter(pk__in=viewed_cafes)


class UserRecentlyViewedCreateView(generics.CreateAPIView):
    serializer_class = rest_serializers.RecentlyViewedSerializer
    model = user_models.RecentlyViewed

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid(raise_exception=False):
            errors = []
            for error in serializer.errors:
                errors.append(serializer.errors.get(error)[0])
            return response.Response({"status": "fail", "message": errors},
                                     status=status.HTTP_400_BAD_REQUEST)
        phone = kwargs.get('phone')
        cafe_id = request.data.get('cafe')

        viewed_cafe = self.model.objects.filter(user__phone=phone, cafe__id=cafe_id)
        if not viewed_cafe.exists():
            self.model.objects.create(**{
                'user': user_models.User.objects.get(phone=phone),
                'cafe': user_models.Cafe.objects.get(id=cafe_id)
            })
        headers = self.get_success_headers(serializer.data)
        return response.Response({"status": "success", "message": ["Successful added"]},
                                 status=status.HTTP_201_CREATED, headers=headers)


class UserRecentlyViewedDeleteView(generics.DestroyAPIView):
    serializer_class = rest_serializers.RecentlyViewedSerializer
    authentication_classes = [TokenAuthentication]
    model = user_models.RecentlyViewed

    def get_object(self):
        return self.model.objects.get(cafe_id=self.kwargs.get('cafe_id'), user__phone=self.kwargs.get('phone'))


class UserRecentlyViewedClearAllView(generics.DestroyAPIView):
    serializer_class = rest_serializers.RecentlyViewedSerializer
    authentication_classes = [TokenAuthentication]
    model = user_models.RecentlyViewed
    lookup_url_kwarg = ['phone']

    def get_queryset(self):
        phone = self.kwargs.get('phone')
        return self.model.objects.filter(user__phone=phone)

    def destroy(self, request, *args, **kwargs):
        query_set = self.get_queryset()
        query_set.delete()
        return response.Response(status.HTTP_204_NO_CONTENT)


class UserCreateView(generics.CreateAPIView):
    serializer_class = rest_serializers.UserCreateSerializer

    def create(self, request, *args, **kwargs):
        serialized = self.serializer_class(data=request.data)
        if serialized.is_valid():
            serialized.save()
            return response.Response(serialized.data, status=status.HTTP_201_CREATED)
        else:
            errors = []
            for key in serialized.errors.keys():
                if isinstance(serialized.errors[key], list):
                    error_text = serialized.errors[key][0]
                else:
                    error_text = serialized.errors[key]
                errors.append({'message': error_text})
            print(errors)
            return response.Response(errors, status=status.HTTP_400_BAD_REQUEST)


class UserUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = rest_serializers.UserUpdateSerializer

    def get_object(self):
        return user_models.User.objects.get(phone=self.kwargs.get('phone'))

    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        return response.Response({"status": "success", "message": ["Successful updated"]})


class UserPasswordChangeView(views.APIView):

    def post(self, request, *args, **kwargs):
        phone = kwargs.get('phone')
        country_code = settings.TWILLIO_COUNTRY_CODE
        authy_api = AuthyApiClient(api_key=settings.TWILLIO_API_KEY)

        if request.data.get('code') and request.data.get('password'):
            password = request.data.get('password')
            check = authy_api.phones.verification_check(phone_number=phone, country_code=country_code,
                                                        verification_code=request.data.get('code'))
            if check.ok():
                user = user_models.User.objects.get(phone=phone)
                user.set_password(raw_password=password)
                user.save()
                token = Token.objects.filter(user_id=user.id)
                if token.exists():
                    token.delete()
                token = Token.objects.create(user_id=user.id)
                msg_text = 'Password successful changed'
                data = {
                    'status': 'success',
                    'token': token.key,
                    'message': msg_text
                }
                return response.Response(data=data)
            else:
                msg_status = 'fail'
                msg_text = 'Incorrect verification code'
        else:
            sent_sms = authy_api.phones.verification_start(phone_number=phone, country_code=country_code, via='sms')
            print(sent_sms.response.text)
            if sent_sms.ok():
                msg_status = 'success'
                msg_text = 'Successful sent verification code'
            else:
                msg_status = 'fail'
                msg_text = 'Could not send sms'
        message = {
            'status': msg_status,
            'message': msg_text
        }
        return response.Response(data=message)


class ReviewLikeDislikeView(generics.CreateAPIView):
    serializer_class = rest_serializers.ReviewLikeDislikeSerializer


class CafeLikeDislikeView(generics.CreateAPIView):
    serializer_class = rest_serializers.CafeLikeDislikeSerializer


class ReviewLikeDislikeAllView(generics.ListAPIView):
    serializer_class = rest_serializers.ReviewLikeDislikeSerializer
    queryset = user_models.ReviewLikeDislike.objects.all()

    def get_queryset(self):
        review = user_models.Review.objects.get(pk=self.kwargs.get('review_id'))
        return self.queryset.filter(review=review).order_by('-pk')


class NewsView(generics.ListAPIView):
    serializer_class = rest_serializers.NewsSerializer
    queryset = user_models.News.objects.order_by('-created_at')
    permission_classes = (permissions.AllowAny,)


class NewsDetailView(generics.RetrieveAPIView):
    serializer_class = rest_serializers.NewsSerializer
    permission_classes = (permissions.AllowAny,)
    queryset = user_models.News.objects.all()
    lookup_url_kwarg = 'news_id'


class ProductsView(generics.ListAPIView):
    serializer_class = rest_serializers.ProductSerializer
    queryset = product_models.Product.objects.all()
    permission_classes = (permissions.AllowAny,)
    search_fields = ['title', 'category__name', 'description', ]


class ProductsDetailView(generics.RetrieveAPIView):
    serializer_class = rest_serializers.ProductSerializer
    queryset = product_models.Product.objects.all()
    permission_classes = (permissions.AllowAny,)
    lookup_url_kwarg = 'product_id'


class UserOrdersView(generics.ListAPIView):
    serializer_class = rest_serializers.OrderSerializer

    def get_queryset(self):
        return order_models.Order.objects.filter(customer__phone=self.kwargs.get('phone')).order_by('-id')
        # return order_models.Order.objects.filter(customer__phone=self.kwargs.get('phone'),
        #                                          transaction__isnull=False)


class UserOrdersCreateView(generics.CreateAPIView):
    serializer_class = rest_serializers.OrderCreateSerializer
    queryset = order_models.Order.objects.all()


class CafeProductsView(generics.ListAPIView):
    serializer_class = rest_serializers.ProductSerializer
    filter_fields = ['category', ]
    search_fields = ['title', 'category__name', 'description', ]

    def get_queryset(self):
        queryset = product_models.Product.objects.filter(cafes__cafe_id=self.kwargs.get('cafe_id')).distinct('id')
        return queryset


class UserPointsView(generics.ListAPIView):
    serializer_class = rest_serializers.PointSerializer

    def get_queryset(self):
        return user_models.Point.objects.filter(owner__phone=self.kwargs.get('phone'))


class CafePointsView(generics.ListAPIView):
    serializer_class = rest_serializers.UsersPointSerializer
    filter_fields = ['phone']
    search_fields = ['first_name', 'last_name', 'username', 'phone', ]

    def get_queryset(self):
        cafe = user_models.Cafe.objects.get(pk=self.kwargs.get('cafe_id'))

        return user_models.User.objects.filter(product_exchanger__root_cafe__owner_id=cafe.user_id,
                                               points__isnull=False).distinct()


class UserPointCreateView(views.APIView):
    serializer_class = rest_serializers.UserPointSerializer

    def post(self, request, *args, **kwargs):
        cafe_id = request.data.get('cafe')
        point_count = int(request.data.get('point_count'))
        phone = kwargs.get('phone')

        cafe = user_models.Cafe.objects.get(pk=cafe_id)

        point_owner = user_models.User.objects.get(phone=phone)

        point = project_modules.point_free_item_calculation(cafe=cafe, client=point_owner, count=point_count)

        return response.Response(data={'message': 'Success', 'data': {
            'point_count': point.point_count
        }})


class UserPointSubtractionView(views.APIView):

    def post(self, request, *args, **kwargs):
        owner = kwargs.get('phone')
        point_count = request.POST.get('point_count', 0)
        total_point_count = user_models.Point.objects.filter(owner__phone=owner).aggregate(Sum('point_count'))
        if total_point_count >= point_count:
            pass
        return response.Response(data={'message': total_point_count})


class CashierOrdersListView(generics.ListAPIView):
    serializer_class = rest_serializers.OrderSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('state',)

    def get_queryset(self):
        return order_models.Order.objects.filter(
            cafe__cafe_cashiers__cashier__phone=self.kwargs.get('phone'), ).order_by('-id')


class CashierOrderUpdateView(generics.UpdateAPIView):
    serializer_class = rest_serializers.OrderUpdateSerializer

    # permission_classes = [permissions.IsAuthenticated, ]

    def get_object(self):
        try:
            order = order_models.Order.objects.get(pk=self.kwargs.get('order_id'))
        except order_models.Order.DoesNotExist:
            raise Http404()
        cashier = order.cafe.cafe_cashiers.filter(cashier__phone=self.kwargs.get('phone'))
        if not cashier.exists():
            raise Http404()
        return order


class CashierOrderedUsersListView(generics.ListAPIView):
    serializer_class = rest_serializers.OrderedUsersSerializer

    def get_queryset(self):
        phone = self.kwargs.get('phone')
        ordered_users = order_models.Order.objects.filter(cafe__cafe_cashiers__cashier__phone=phone,
                                                          transaction__isnull=False).values_list('customer', flat=True)
        users = user_models.User.objects.filter(pk__in=ordered_users)
        return users


class CashierOrderedUsersTransactionsListView(generics.ListAPIView):
    serializer_class = rest_serializers.OrderedUsersTransactionSerializer

    def get_queryset(self):
        phone = self.kwargs.get('phone')
        orders = order_models.Order.objects.filter(cafe__cafe_cashiers__cashier__phone=phone,
                                                   transaction__isnull=False).values_list('pk', flat=True)
        return order_models.Transaction.objects.filter(order_id__in=orders)


class ProductsCategoryView(generics.ListAPIView):
    serializer_class = rest_serializers.ProductCategorySerializer
    queryset = product_models.ProductCategory.objects.all()
    permission_classes = (permissions.AllowAny,)


class CafePointsExchangedProductsView(generics.ListAPIView):
    serializer_class = rest_serializers.CafePointsExchangedProductsSerializer

    def get_queryset(self):
        cafe = user_models.Cafe.objects.get(pk=self.kwargs.get('cafe_id'))
        return user_models.FreeItem.objects.filter(owner__phone=self.kwargs.get('phone'),
                                                   root_cafe__owner_id=cafe.user_id)


class CustomerFreeItemsView(generics.ListAPIView):
    serializer_class = rest_serializers.UserExchangedProductsSerializer

    def get_queryset(self):
        status = self.request.GET.get('status', user_models.FreeItem.VALID)

        owners = user_models.User.objects.get(phone=self.kwargs.get('phone')).product_exchanger.filter(
            status=status).values_list('root_cafe__owner', flat=True).distinct('root_cafe__owner')
        t = user_models.User.objects.filter(pk__in=owners)
        return t


class UserFreeItemsForCashierView(generics.ListAPIView):
    serializer_class = rest_serializers.UsersFreeItemsForCashierSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ['status', ]

    def get_queryset(self):
        cafe = user_models.Cafe.objects.get(pk=self.kwargs.get('cafe_id'))
        products = user_models.FreeItem.objects.filter(owner__phone=self.kwargs.get('phone'),
                                                       root_cafe_id=cafe.user.settings.id)
        return products


class UserPaymentStripeView(views.APIView):

    def get(self, request, *args, **kwargs):
        return response.Response('Hello world')

    def post(self, request, *args, **kwargs):
        print(request)
        stripe.api_key = settings.STRIPE_API_KEY
        order = order_models.Order.objects.get(id=kwargs.get('order_id'))
        payer = user_models.User.objects.get(phone=kwargs.get('phone'))

        data = request.data
        token_id = data.get('m_id')
        token = stripe.Token.retrieve(id=token_id)
        amount = int(order.total_price * 100)
        payment_type = data.get('m_card').get('brand', '-empty-')

        transaction = payment_models.StripeTransaction()
        transaction.token = token_id
        transaction.order_id = order.id
        transaction.amount = amount
        transaction.payer_id = payer.id
        transaction.payment_type = payment_type
        transaction.description = data.get('description', '-empty-')
        transaction.save()

        simple_transaction = order_models.Transaction()
        simple_transaction.amount = amount
        simple_transaction.order = order
        simple_transaction.payment_type = payment_type
        simple_transaction.payer = order.customer
        simple_transaction.save()

        customer = stripe.Customer.create(
            source=token_id,
        )
        print(customer)
        try:
            charge = stripe.Charge.create(
                amount=amount,
                currency='usd',
                customer=customer.id,
            )
            message = "Successfully transaction was created"
            status_code = 200

            transaction.payment_id = charge.__getitem__('id')
            transaction.status = 'paid'
            transaction.order.state = transaction.order.READY
            transaction.order.save()
            transaction.save()

        except stripe.error.CardError as e:
            # Since it's a decline, stripe.error.CardError will be caught
            body = e.json_body
            err = body.get('error', {})

            message = err.get('message')
            status_code = e.http_status
        except stripe.error.RateLimitError as e:
            # Too many requests made to the API too quickly
            body = e.json_body
            err = body.get('error', {})
            message = err.get('message')
            status_code = e.http_status
        except stripe.error.InvalidRequestError as e:
            # Invalid parameters were supplied to Stripe's API
            body = e.json_body
            err = body.get('error', {})
            message = err.get('message')
            status_code = e.http_status
        except stripe.error.AuthenticationError as e:
            # Authentication with Stripe's API failed
            # (maybe you changed API keys recently)

            body = e.json_body
            err = body.get('error', {})
            message = err.get('message')
            status_code = e.http_status
        except stripe.error.APIConnectionError as e:
            # Network communication with Stripe failed

            body = e.json_body
            err = body.get('error', {})
            message = err.get('message')
            status_code = e.http_status
        except stripe.error.StripeError as e:
            # Display a very generic error to the user, and maybe send
            # yourself an email

            body = e.json_body
            err = body.get('error', {})
            message = err.get('message')
            status_code = e.http_status
        except Exception as e:
            # Something else happened, completely unrelated to Stripe
            body = e.json_body
            err = body.get('error', {})
            message = err.get('message')
            status_code = e.http_status
        return response.Response(data={
            'message': message,
            'customer_id': customer.id
        }, status=status_code)


class StripeRetrieveView(views.APIView):

    def post(self, request, *args, **kwargs):
        if request.data.get('token_id'):
            stripe.api_key = settings.STRIPE_API_KEY
            token_id = request.data.get('token_id')
            # token = stripe.Token.retrieve(id=token_id)
            customer = stripe.Customer.create(source=token_id)
            # customer.sources.create(source=token_id)
            print(customer.id)
            return response.Response(data={'customer': customer.id})
        return response.Response(data={'customer': '12'})


class PaypalRetrieveView(views.APIView):

    def post(self, request, *args, **kwargs):
        cse_key = request.data.get('token_id')
        print(cse_key)
        print(request)
        gateway = braintree.BraintreeGateway(
            braintree.Configuration(
                braintree.Environment.Sandbox,
                merchant_id=settings.PAYPAL_MERCHANT_ID,
                public_key=settings.PAYPAL_PUBLIC_KEY,
                private_key=settings.PAYPAL_PRIVATE_KEY
            )
        )
        client_token = gateway.client_token.generate()
        return response.Response(data={
            'token': client_token
        })


class StripeRejectView(views.APIView):

    def post(self, request, *args, **kwargs):
        user = user_models.User.objects.get(phone=self.kwargs.get('phone'))
        status = 'succeeded'

        try:
            print(self.kwargs.get('phone'))
            # user = user_models.User.objects.get(phone=self.kwargs.get('phone'))
            if user.is_can_reject:
                stripe.api_key = settings.STRIPE_API_KEY
                # token_id = request.data.get('token_id')
                order = order_models.Order.objects.get(id=self.kwargs.get('order_id'))
                # payer = user_models.User.objects.get(post_data.get('phone'))
                if order:
                    payments = payment_models.StripeTransaction.objects.filter(order_id=order.id)
                    for payment in payments:
                        refund = stripe.Refund.create(charge=payment.payment_id)
                        reject = stripe.Refund.retrieve(refund.id)
                        if reject.status == 'succeeded':
                            payment.status = 'reject'

                            payment.save()
                    order.state = 'reject'
                    order.save()
                return response.Response(data={'status': status})
        except stripe.error.StripeError as e:
            body = e.json_body
            err = body.get('error', {})
            message = err.get('message')
            status_code = e.http_status
            return response.Response(data={'message': message, 'order': order.id}, status=status_code)
        except Exception as e:
            # Something else happened, completely unrelated to Stripe
            body = e.json_body
            err = body.get('error', {})
            message = err.get('message')
            status_code = e.http_status
            return response.Response(data={'message': message, 'customer_id': user.id}, status=status_code)

        return response.Response(data={'customer': user.id})


class CafesRelatedView(generics.ListAPIView):
    serializer_class = rest_serializers.CafesSerializer

    def get_queryset(self):
        cafe = user_models.Cafe.objects.get(pk=self.kwargs.get('cafe_id'))
        return user_models.Cafe.objects.filter(category_id=cafe.category.id).exclude(pk=cafe.id)


class ProductFileUploadView(views.APIView):
    pass


class CustomerFreeItemsForCafeView(views.APIView):

    def get(self, request, *args, **kwargs):
        free_items = user_models.FreeItem.objects.filter(owner__phone=kwargs.get('phone')).values('root_cafe').annotate(
            count=Count('root_cafe'))
        return response.Response(data=free_items)


class UserPaymentStripeExistingCardView(views.APIView):

    def post(self, request, *args, **kwargs):

        stripe.api_key = settings.STRIPE_API_KEY
        order = order_models.Order.objects.get(id=kwargs.get('order_id'))
        payer = user_models.User.objects.get(phone=kwargs.get('phone'))

        data = request.data

        customer_id = data.get('customer_id')
        customer = stripe.Customer.retrieve(id=customer_id)
        card_id = data.get('card_id')
        token_id = data.get('token_id')
        token = stripe.Token.retrieve(id=token_id)

        amount = int(order.total_price * 100)
        payment_type = token.card.get('brand', '--empty--')

        transaction = payment_models.StripeTransaction()
        transaction.order_id = order.id
        transaction.amount = amount
        transaction.payer_id = payer.id
        transaction.customer_id = customer_id
        transaction.card_id = card_id
        transaction.payment_type = payment_type
        transaction.description = token.card.get('description', '-empty-')
        transaction.save()

        simple_transaction = order_models.Transaction()
        simple_transaction.amount = amount
        simple_transaction.order = order
        simple_transaction.payment_type = payment_type
        simple_transaction.payer = order.customer
        simple_transaction.save()

        try:
            charge = stripe.Charge.create(
                amount=amount,
                currency='usd',
                customer=customer,
                source=card_id
            )
            message = "Successfully transaction was created"
            status_code = 200

            transaction.payment_id = charge.__getitem__('id')
            transaction.status = 'paid'
            transaction.save()

        except stripe.error.CardError as e:
            # Since it's a decline, stripe.error.CardError will be caught
            body = e.json_body
            err = body.get('error', {})

            message = err.get('message')
            status_code = e.http_status
        except stripe.error.RateLimitError as e:
            # Too many requests made to the API too quickly
            body = e.json_body
            err = body.get('error', {})
            message = err.get('message')
            status_code = e.http_status
        except stripe.error.InvalidRequestError as e:
            # Invalid parameters were supplied to Stripe's API
            body = e.json_body
            err = body.get('error', {})
            message = err.get('message')
            status_code = e.http_status
        except stripe.error.AuthenticationError as e:
            # Authentication with Stripe's API failed
            # (maybe you changed API keys recently)
            body = e.json_body
            err = body.get('error', {})
            message = err.get('message')
            status_code = e.http_status
        except stripe.error.APIConnectionError as e:
            # Network communication with Stripe failed

            body = e.json_body
            err = body.get('error', {})
            message = err.get('message')
            status_code = e.http_status
        except stripe.error.StripeError as e:
            # Display a very generic error to the user, and maybe send
            # yourself an email

            body = e.json_body
            err = body.get('error', {})
            message = err.get('message')
            status_code = e.http_status
        except Exception as e:
            # Something else happened, completely unrelated to Stripe
            body = e.json_body
            err = body.get('error', {})
            message = err.get('message')
            status_code = e.http_status
        return response.Response(data={
            'message': message,
            'customer_id': customer.id
        }, status=status_code)


class SendNotificationsView(views.APIView):

    def get(self, request, *args, **kwargs):
        if request.GET.get('key') and request.GET.get('key') == '123':
            print('before runing tasks from tasks file')
            send_free_item_expire_notifications.delay()
        return response.Response('sent notifications')


class SocialLoginView(views.APIView):

    def post(self, request, *args, **kwargs):
        data = {'message': 'Social login'}
        print(data)
        token = request.data.get('token_id')
        if kwargs.get('provider') == 'google':
            try:
                idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), settings.GOOGLE_API_CLIENT_ID)

                if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                    raise ValueError('Wrong issuer.')

                google_user_id = idinfo['sub']
                google_email = idinfo['email']
                google_full_name = idinfo['name']
                google_picture = idinfo['picture']
                google_given_name = idinfo['given_name']
                google_family_name = idinfo['family_name']

                profiles = user_models.SocialProfile.objects.filter(social_user_id=google_user_id)
                if profiles.exists():
                    profile = profiles.first()
                    user = profile.user
                    token = Token.objects.filter(user_id=user.id)
                    if token.exists():
                        token.delete()
                    token = Token.objects.create(user_id=user.id)
                    data = {
                        'token': token.key,
                        'phone': user.phone
                    }
                    return response.Response(data=data)
                else:
                    data = {
                        'first_name': google_given_name,
                        'last_name': google_family_name,
                        'avatar': google_picture,
                        'full_name': google_full_name,
                        'email': google_email,
                        'user_id': google_user_id,
                    }
                    return response.Response(data=data)
            except ValueError as e:
                print(e)
                print('Error')
                data = {
                    'error': e.args[0]
                }
        elif kwargs.get('provider') == 'facebook':
            # access_token = "EAAJSytEXoGsBACXeg5oJUej8tH0VQvV0tYOzXEEeo7Kn2fXovJo9yCfyahdV0FaKlBxZCokQB60WbZAIPpgEb40eHwjOqQk76btGH13tvLycbZCfocsxZCNKvMNS75SVxuugGn6f7pOfCJpeh3yRNVZBqlEoFKr29ZCpOhJLZBagbJ1MIo0Haspjqg0PTJrHKEyF2pzlzN82AZDZD"
            access_token = token
            response_data = requests.post(url=settings.AWS_LAMBDA_API_URL, json={'access_token': access_token})
            response_data = response_data.json()
            profiles = user_models.SocialProfile.objects.filter(social_user_id=response_data['id'])
            if profiles.exists():
                profile = profiles.first()
                profile = profiles.first()
                user = profile.user
                token = Token.objects.filter(user_id=user.id)
                if token.exists():
                    token.delete()
                token = Token.objects.create(user_id=user.id)
                data = {
                    'token': token.key,
                    'phone': user.phone
                }
                return response.Response(data=data)
            else:
                data = {
                    'first_name': response_data.get('first_name'),
                    'last_name': response_data.get('last_name'),
                    'avatar': "https://graph.facebook.com/{}/picture?type=large".format(response_data.get('id')),
                    'full_name': response_data.get('name'),
                    'user_id': response_data.get('id'),
                }
                return response.Response(data=data)

        return response.Response(data=data)


class SocialRegisterView(views.APIView):

    def post(self, request, *args, **kwargs):
        provider = kwargs.get('provider')
        post_data = request.data
        phone = post_data.get('phone')
        if user_models.User.objects.filter(phone=phone).exists():
            data = {
                'message': 'User with this phone already exists'
            }
            status_code = status.HTTP_409_CONFLICT
        else:
            user = user_models.User()
            user.phone = post_data.get('phone')
            user.first_name = post_data.get('first_name')
            user.last_name = post_data.get('last_name')
            user.set_password(post_data.get('password'))
            user.is_active = True
            user.save()

            profile = user_models.SocialProfile()
            profile.user_id = user.id
            profile.provider = provider
            profile.token = post_data.get('token_id')
            profile.social_user_id = post_data.get('user_id')
            profile.save()
            token = Token(user_id=user.id)
            token.save()
            data = {
                'phone': user.phone,
                'token': token.key
            }
            status_code = status.HTTP_200_OK
        return response.Response(data=data, status=status_code)


class UserPaymentPaypalView(views.APIView):

    def post(self, request, *args, **kwargs):
        order = order_models.Order.objects.get(pk=kwargs.get('order_id'))
        nonce = request.data.get('nonce')

        gateway = braintree.BraintreeGateway(
            braintree.Configuration(
                braintree.Environment.Sandbox,
                merchant_id=settings.PAYPAL_MERCHANT_ID,
                public_key=settings.PAYPAL_PUBLIC_KEY,
                private_key=settings.PAYPAL_PRIVATE_KEY
            )
        )
        try:
            result = gateway.transaction.sale({
                "amount": order.total_price,
                "payment_method_nonce": nonce,
                "options": {
                    "submit_for_settlement": True
                }
            })
            if result.is_success:
                transaction_id = result.transaction.id
                paypal_payment = payment_models.PaypalTransaction()
                paypal_payment.transaction_id = transaction_id
                paypal_payment.order = order
                paypal_payment.amount = result.transaction.amount
                paypal_payment.payment_type = result.transaction.credit_card_details.card_type if result.transaction.credit_card_details else 'Paypal'
                paypal_payment.save()
                order.state = order_models.Order.READY
                order.save()
                simple_transaction = order_models.Transaction()
                simple_transaction.amount = result.transaction.amount
                simple_transaction.order = order
                simple_transaction.payment_type = result.transaction.credit_card_details.card_type if result.transaction.credit_card_details else 'Paypal'
                simple_transaction.payer = order.customer
                simple_transaction.save()

                data = {
                    'message': 'Successful paid',
                    'transaction_id': transaction_id,
                    'is_success': True
                }
            elif result.transaction:
                data = {
                    'status': result.transaction.processor_response_code,
                    'message': result.transaction.processor_response_text,
                    'is_success': False
                }
            else:
                print(result.errors)
                data = {
                    'message': result.errors.deep_errors[0].message,
                    'is_success': False
                }
        except Exception as e:
            print(e)
            return response.Response(data={
                'message': e
            })
        return response.Response(data=data)


class CashierFreeItemChangeView(generics.UpdateAPIView):
    serializer_class = rest_serializers.FreeItemSerializer
    permission_classes = (rest_permissions.IsCashier,)

    def get_object(self):
        return user_models.FreeItem.objects.get(pk=self.kwargs.get('pk'))
