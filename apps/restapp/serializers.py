from django.utils import timezone
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db.models import Sum

from rest_framework import serializers
from rest_framework_recursive.fields import RecursiveField
from geosimple.fields import convert_to_point
from geosimple.utils import Point as GeoPoint
from pyfcm import FCMNotification

from apps.users import models as user_models
from apps.products import models as product_models
from apps.modifiers import models as modifier_models
from apps.orders import models as order_models
from project import modules as project_modules

User = get_user_model()
push_service = FCMNotification(api_key=settings.FCM_API_KEY)

current_day = timezone.datetime.today().weekday()
current_week_day = user_models.get_week_day(current_day)


class RecursiveSerializer(serializers.Serializer):
    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data


class UsersSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'phone', 'first_name', 'last_name', 'is_active',
                  'password', 'gender', 'date_of_birthday',)
        write_only_fields = ('password',)
        read_only_fields = ('is_staff', 'is_active', 'date_joined',)

    def create(self, validated_data):
        user_instance = super(UsersSerializer, self).create(validated_data)
        user_instance.set_password(validated_data['password'])
        user_instance.save()
        return user_instance

    def update(self, instance, validated_data):
        validated_data.pop('password', None)

        instance_update = super().update(instance, validated_data)
        instance_update.save()
        return instance_update


class CafesSerializer(serializers.ModelSerializer):
    logo = serializers.FileField(source='user.settings.logo')
    cafe_id = serializers.IntegerField(source='id')
    root_cafe_id = serializers.IntegerField(source='user.settings.id')
    category = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    likes = serializers.SerializerMethodField()
    dislikes = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    opening_time = serializers.SerializerMethodField()
    closing_time = serializers.SerializerMethodField()
    cafe_reviews = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    time_graphic = serializers.SerializerMethodField()

    class Meta:
        model = user_models.Cafe
        extra_fields = ['avatar', 'time_graphic']
        exclude = ['user', 'id', ]

    @staticmethod
    def get_cafe_reviews(obj):
        return obj.reviews.all().count()

    @staticmethod
    def get_category(obj):
        return [{
            'name': obj.category.name,
            'id': obj.category.id
        }]

    @staticmethod
    def get_description(obj):
        return obj.description

    def get_avatar(self, obj):
        try:
            file = obj.user.get_avatar(self.context['request'])
        except (ValueError, AttributeError):
            return None

        return file

    @staticmethod
    def get_likes(obj):
        return obj.get_likes

    @staticmethod
    def get_dislikes(obj):
        return obj.get_dislikes

    @staticmethod
    def get_email(obj):
        return obj.user.email or ''

    @staticmethod
    def get_location(obj):
        try:
            location_hash_convert = convert_to_point(obj.location)
        except:
            return None
        return str(location_hash_convert.latitude) + "," + str(location_hash_convert.longitude)

    @staticmethod
    def get_opening_time(obj):
        if current_week_day:
            week_time_for_cafe = user_models.WeekTime.objects.filter(cafe=obj)
            week_time_instance = week_time_for_cafe.filter(day=current_week_day).values('opening_time')
            if week_time_instance.exists():
                return week_time_instance.first().get('opening_time')
            else:
                return None
        return None

    @staticmethod
    def get_closing_time(obj):
        if current_week_day:
            week_time_for_cafe = user_models.WeekTime.objects.filter(cafe=obj)
            week_time_instance = week_time_for_cafe.filter(day=current_week_day).values('closing_time')
            if week_time_instance.exists():
                return week_time_instance.first().get('closing_time')
            else:
                return None
        return None

    @staticmethod
    def get_time_graphic(obj):
        return obj.get_time_graphic()
        # return {
        #     'monday': {
        #         'opening_time': '10:00',
        #         'closing_time': '18:00'
        #     },
        #     'tuesday': {
        #         'opening_time': '10:00',
        #         'closing_time': '18:00'
        #     },
        #     'wednesday': {
        #         'opening_time': '10:00',
        #         'closing_time': '18:00'
        #     },
        #     'thursday': {
        #         'opening_time': '10:00',
        #         'closing_time': '18:00'
        #     }
        # }


class CafesNearBySerializer(CafesSerializer):
    distance = serializers.SerializerMethodField()
    email = serializers.EmailField(source='user.email')

    class Meta:
        model = CafesSerializer.Meta.model
        extra_fields = CafesSerializer.Meta.extra_fields + ['distance', ]
        exclude = ['user', 'id', ]

    def get_distance(self, obj):
        latitude = self.context['view'].request.GET.get('latitude')
        longitude = self.context['view'].request.GET.get('longitude')

        point = GeoPoint(latitude=latitude, longitude=longitude)
        obj_location = GeoPoint(obj.location.latitude, obj.location.longitude)
        distance_in_km = point.distance_from(obj_location)
        return distance_in_km.km


class NotificationsSerializer(serializers.ModelSerializer):
    cafe = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = user_models.Notifications
        fields = ['title', 'text', 'cafe', 'image', 'id', 'is_read', ]
        read_only_fields = ['title', 'text', ]

    @staticmethod
    def get_cafe(obj):
        cafe = user_models.Cafe.objects.filter(user=obj.notification_sender, status=user_models.Cafe.ACTIVE)
        if cafe.exists():
            return cafe.first().id
        return None

    @staticmethod
    def get_image(obj):
        if obj.image:
            return obj.image.url
        return None


class CafesForUserSerializer(CafesSerializer):
    is_bookmarked = serializers.SerializerMethodField()

    class Meta:
        model = user_models.Cafe
        extra_fields = ['avatar', 'is_bookmarked', ]
        exclude = ['user', 'id', ]

    def get_is_bookmarked(self, obj):
        phone = self.context['view'].kwargs.get('phone')
        cafe_in_bookmark = user_models.Bookmarks.objects.filter(user__phone=phone, cafe_id=obj.id)
        if cafe_in_bookmark.exists():
            return True
        return False


class ReviewSerializer(serializers.ModelSerializer):
    review_id = serializers.IntegerField(source='id')
    author_id = serializers.IntegerField(source='author.id')
    parent_review_id = serializers.SerializerMethodField('get_parent')
    cafe_id = serializers.IntegerField(source='cafe.id')
    children = serializers.ListField(read_only=True, source='get_children', child=RecursiveField())
    created_at = serializers.SerializerMethodField()
    likes = serializers.SerializerMethodField()
    dislikes = serializers.SerializerMethodField()
    author_avatar = serializers.SerializerMethodField()
    author_fullname = serializers.SerializerMethodField()

    class Meta:
        model = user_models.Review
        fields = ['review_id', 'created_at', 'rate', 'comment', 'parent_review_id',
                  'author_id', 'album', 'cafe_id', 'children', 'likes', 'dislikes',
                  'author_fullname',
                  'author_avatar',
                  ]

    @staticmethod
    def get_parent(obj):
        if obj.parent is not None:
            return obj.parent.id
        else:
            return None

    @staticmethod
    def get_created_at(obj):
        return obj.created_at.timestamp()

    @staticmethod
    def get_likes(obj):
        return user_models.ReviewLikeDislike.objects.filter(review=obj, rate=1).count()

    @staticmethod
    def get_dislikes(obj):
        return user_models.ReviewLikeDislike.objects.filter(review=obj, rate=-1).count()

    def get_author_avatar(self, obj):
        return obj.author.get_avatar(self.context['request'])

    @staticmethod
    def get_author_fullname(obj):
        return obj.author.get_full_name()


class ReviewSerializerForUser(ReviewSerializer):
    rated_status = serializers.SerializerMethodField()

    class Meta:
        model = user_models.Review
        fields = ReviewSerializer.Meta.fields + ['rated_status']

    def get_rated_status(self, obj):
        phone = self.context['view'].kwargs.get('phone')

        review_rated = user_models.ReviewLikeDislike.objects.filter(like_dislike_user__phone=phone, review=obj)
        if review_rated.exists():
            return review_rated.first().rate
        return 0


class ReviewCreateSerializer(serializers.ModelSerializer):
    author_phone = serializers.CharField(source='author.phone')
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = user_models.Review
        exclude = ['cafe', 'lft', 'rght', 'tree_id', 'level', 'author', ]

    def create(self, validated_data):
        cafe_id = self.context.get('view').kwargs.get('cafe_id')
        author_phone = validated_data.get('author').get('phone')
        cafe = user_models.Cafe.objects.get(pk=cafe_id)
        author = User.objects.get(phone=author_phone)
        album = user_models.Album.objects.create(**{
            'owner': author,
            'cafe': cafe
        })
        validated_data['author'] = author
        validated_data['cafe'] = cafe
        validated_data['album'] = album

        instance = super().create(validated_data)

        if instance.parent:
            parent_author = instance.parent.author

            phone = parent_author.phone
            message = "To your review has been replied"
            kwargs = dict()
            kwargs['title'] = "Replied to review"
            kwargs['notification_sender'] = author.id
            result = project_modules.send_push_for_topic(phone, message, **kwargs)
            if result:
                print('Successfully sent')
        else:
            user_models.Notifications.objects.create(**{
                'title': 'Added new review',
                'user': cafe.user,
                'notification_sender': author,
                'text': 'You have new review from {}'.format(author.get_full_name()),
            })
        return instance

    @staticmethod
    def get_created_at(obj):
        return obj.created_at.timestamp()


class ReviewReadUpdateDestroySerializer(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = user_models.Review
        fields = ['created_at', 'comment', 'author', 'parent', 'album', ]

    @staticmethod
    def get_created_at(obj):
        return obj.created_at.timestamp()


class ReviewLikeDislikeSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(source='like_dislike_user.phone')

    class Meta:
        model = user_models.ReviewLikeDislike
        exclude = ['like_dislike_user', 'review']

        def create(self, validated_data):
            phone = validated_data.get('like_dislike_user').get('phone')
            review_id = self.context['view'].kwargs.get('review_id')
            like_dislike_user = User.objects.get(phone=phone)
            review = user_models.Review.objects.get(pk=review_id)

            if self.Meta.model.objects.filter(like_dislike_user=like_dislike_user, review=review).exists():
                instance = self.Meta.model.objects.get(like_dislike_user=like_dislike_user, review=review)
                instance.rate = validated_data.get('rate')
                instance.save()
            else:
                validated_data['like_dislike_user'] = like_dislike_user
                validated_data['review'] = review
                instance = super().create(validated_data)

            if review.author:
                review_author = review.author
                if validated_data.get('rate') == 1:
                    rated_as = 'like'
                elif validated_data.get('rate') == -1:
                    rated_as = 'dislike'
                else:
                    rated_as = 'neutral'
                message = "Hi, Your review was rated as " + rated_as

                kwargs = dict()
                kwargs['title'] = "user_models.Review was rated"
                kwargs['notification_sender'] = like_dislike_user.id

                result = project_modules.send_push_for_topic(review_author.phone, message, **kwargs)
                if result:
                    print('Successfully sent')
            return instance


class CafeLikeDislikeSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(source='user.phone')

    class Meta:
        model = user_models.CafeLikeDislike
        exclude = ['user', 'cafe']

    def create(self, validated_data):
        phone = validated_data.get('user').get('phone')
        cafe_id = self.context['view'].kwargs.get('cafe_id')

        rate_instance, created = user_models.CafeLikeDislike.objects.get_or_create(cafe_id=cafe_id, user__phone=phone,
                                                                                   defaults={'rate': validated_data.get(
                                                                                       'rate')})
        if not created:
            rate_instance.rate = validated_data.get('rate')
            rate_instance.save()

        # Todo: Send notification to cafe owner
        return rate_instance


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.ListField(read_only=True, source='get_children', child=RecursiveField())

    class Meta:
        model = user_models.Category
        fields = ['id', 'name', 'is_top', 'icon', 'parent', 'children', 'svg_icon', ]


class CategoryTopSerializer(serializers.ModelSerializer):
    class Meta:
        model = user_models.Category
        fields = ['id', 'name', 'is_top', 'icon', 'parent', 'svg_icon', ]


class BookmarkListSerializer(serializers.ModelSerializer):
    bookmark_id = serializers.IntegerField(source='id')
    cafe = CafesSerializer(read_only=True)
    cafe_reviews = serializers.SerializerMethodField()

    class Meta:
        model = user_models.Bookmarks
        fields = ['bookmark_id', 'cafe', 'cafe_reviews', ]

    @staticmethod
    def get_cafe_reviews(obj):
        return obj.cafe.reviews.all().count()


class BookmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = user_models.Bookmarks
        fields = [
            'cafe',
        ]


class UserSerializer(serializers.ModelSerializer):
    date_of_birthday = serializers.DateField(required=False)
    phone = serializers.CharField(required=False)
    gender = serializers.CharField(required=False)
    avatar = serializers.ImageField(required=False, allow_null=True)
    password = serializers.CharField(write_only=True, required=False, )
    cafe_id = serializers.SerializerMethodField(read_only=True)
    inviter_code = serializers.CharField(write_only=True, allow_null=True)
    is_cashier = serializers.SerializerMethodField(read_only=True, allow_null=True)
    referral_code = serializers.CharField(read_only=True, allow_null=True)

    class Meta:
        model = User
        fields = [
            'phone',
            'first_name',
            'last_name',
            'date_of_birthday',
            'gender',
            'avatar',
            'password',
            'is_cashier',
            'cafe_id',
            'inviter_code',
            'referral_code',
        ]

    def get_avatar(self, obj):
        return obj.get_avatar(self.context['request'])

    @staticmethod
    def get_is_cashier(obj):
        return obj.is_cashier

    @staticmethod
    def get_cafe_id(obj):
        return obj.cashiers.first().cafe.id if obj.is_cashier else None


class UserUpdateSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        fields = [
            'first_name',
            'last_name',
            'date_of_birthday',
            'gender',
            'avatar'
        ]


class UserCreateSerializer(serializers.ModelSerializer):
    # user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    password = serializers.CharField(write_only=True)
    inviter_code = serializers.CharField(write_only=True, allow_null=True, required=False)

    class Meta:
        model = User
        fields = [
            'phone',
            'first_name',
            'last_name',
            'date_of_birthday',
            'gender',
            'avatar',
            'password',
            'inviter_code',
        ]

    #
    # def to_representation(self, instance):
    #     self.fields['user'] = serializers.SerializerMethodField()

    def create(self, validated_data):
        inviter_code = validated_data.pop('inviter_code', None)
        user = super(UserCreateSerializer, self).create(validated_data)
        user.set_password(validated_data['password'])
        user.set_referral_code()
        user.save()
        if inviter_code:
            try:
                inviter = user_models.User.objects.get(referral_code=inviter_code)
                user_models.InvitedUser(user_id=user.id, inviter_id=inviter.id).save()
            except user_models.User.DoesNotExist:
                pass
        return user


class UserPasswordSerializer(serializers.ModelSerializer):
    password = serializers.CharField(required=True, write_only=True)

    class Meta:
        model = User
        fields = (
            'password',
        )

    def update(self, instance, validated_data):
        user = instance
        user.set_password(validated_data.get('password'))
        user.save()
        return user


class ReviewFileUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = user_models.File
        fields = ['file']

    def create(self, validated_data):
        kwargs = self.context['view'].kwargs
        review_id = kwargs.get('review_id')
        review = user_models.Review.objects.get(id=review_id)
        if not review.album:
            album = user_models.Album.objects.create(**{
                'owner': review.author,
                'cafe': review.cafe
            })
            review.album = album
            review.save()
        file_instance = self.Meta.model.objects.create(**{
            'file': validated_data.get('file'),
            'album': review.album
        })
        return file_instance


class CafeFilesSerializer(serializers.ModelSerializer):
    class Meta:
        model = user_models.File
        fields = ['file']


class RecentlyViewedSerializer(serializers.ModelSerializer):
    class Meta:
        model = user_models.RecentlyViewed
        fields = ['cafe', ]


class RecentlyViewedListSerializer(serializers.ModelSerializer):
    cafe = CafesSerializer(read_only=True)

    class Meta:
        model = user_models.RecentlyViewed
        fields = ['cafe', ]


class NewsSerializer(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = user_models.News
        fields = ['id', 'title', 'content', 'created_at', 'image']

    @staticmethod
    def get_created_at(obj):
        return int(obj.created_at.timestamp())


class ProductSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    sizes = serializers.SerializerMethodField()
    modifiers = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    available_in_free_item = serializers.SerializerMethodField()

    class Meta:
        model = product_models.Product
        fields = ['id', 'title', 'description', 'price', 'sizes', 'modifiers', 'images', 'category',
                  'available_in_free_item', ]

    def get_images(self, obj):
        return [
            {
                'id': image.id,
                'src': self.context['request'].build_absolute_uri(image.file.url)
            }
            for image in obj.images.all()
        ]

    @staticmethod
    def get_category(obj):
        if obj.category:
            return [{
                'name': obj.category.name,
                'id': obj.category.id
            }]
        return None

    @staticmethod
    def get_sizes(obj):
        sizes = product_models.Size.objects.filter(product_id=obj.id, available=True)
        serializer = SizeSerializer(sizes, many=True)
        if serializer:
            return serializer.data
        return None

    @staticmethod
    def get_modifiers(obj):
        modifiers = product_models.ModifierCategory.objects.raw(
            "SELECT  id, title, is_top, is_single, required, available FROM modifiers_modifiercategory WHERE id IN (SELECT modifier_id FROM products_productmodifier WHERE product_id = %s)",
            [obj.id])
        serializer = ModifierCategorySerializer(modifiers, many=True)
        if serializer:
            return serializer.data
        return None

    @staticmethod
    def get_available_in_free_item(obj):
        category = obj.owner.settings.exchangeable_product
        is_free_item = False
        if category and obj.category:
            if category.pk == obj.category.pk:
                is_free_item = True
        return is_free_item


class CartModifierSerializer(serializers.ModelSerializer):
    modifier__title = serializers.CharField(source='modifier.title', required=False)
    modifier__category__title = serializers.CharField(source='modifier.category.title', required=False)
    modifier__id = serializers.IntegerField(source='modifier.id', required=False)
    modifier__category__id = serializers.IntegerField(source='modifier.category.id', required=False)
    modifier__price = serializers.FloatField(source='modifier.price', required=False, default=0)

    class Meta:
        model = order_models.CartModifier
        fields = ['id', 'count', 'cart', 'modifier__title', 'product',
                  'modifier__price', 'modifier__id', 'modifier__category__title','modifier__category__id']


class CartSerializer(serializers.ModelSerializer):
    product__title = serializers.CharField(source='product.title', required=False)
    product__price = serializers.FloatField(source='product.price', required=False)
    free_count = serializers.IntegerField(allow_null=True)
    modifiers = serializers.SerializerMethodField()

    class Meta:
        model = order_models.Cart
        fields = ['id', 'product__title', 'count', 'modifiers', 'product', 'free_count', 'product__price']
        extra_fields = ['free_count']

    @staticmethod
    def get_modifiers(obj):
        cart_modifier = order_models.CartModifier.objects.filter(cart_id=obj.id)
        if cart_modifier:
            serializer = CartModifierSerializer(cart_modifier, many=True)
            if serializer:
                # return cart_modifier.values_list('id')
                return serializer.data
                # return cart_modifier
        return None


class OrderSerializer(serializers.ModelSerializer):
    ordered_time = serializers.SerializerMethodField()
    pre_order_date = serializers.SerializerMethodField()
    # cart_items = serializers.ListField(source='get_items_list')
    customer = serializers.CharField(source='customer.get_full_name')
    customer_avatar = serializers.SerializerMethodField()
    cafe_logo = serializers.SerializerMethodField()
    cafe_name = serializers.CharField(source='cafe.cafe_name')
    cafe_id = serializers.IntegerField(source='cafe.id')
    cart_items = CartSerializer(many=True, required=False)

    class Meta:
        model = order_models.Order
        fields = [
            'id',
            'ordered_time',
            'total_price',
            'sub_total_price',
            'tax_total',
            'state',
            'cart_items',
            'customer',
            'customer_avatar',
            'pre_order',
            'pre_order_date',
            'cafe_id',
            'cafe_logo',
            'cafe_name'
        ]

    @staticmethod
    def get_ordered_time(obj):
        return obj.created.timestamp()

    @staticmethod
    def get_pre_order_date(obj):
        return obj.pre_order_date.timestamp() if obj.pre_order else None

    def get_customer_avatar(self, obj):
        return obj.customer.get_avatar(request=self.context['request'])

    def get_cafe_logo(self, obj):

        try:
            root_settings = user_models.CafeGeneralSettings.objects.get(owner_id=obj.cafe.user_id)
            request = self.context['request']
            file = request.build_absolute_uri(root_settings.logo.url)
        except (ValueError, AttributeError):
            return None
        return file


class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = product_models.Size
        fields = '__all__'


class ModifierCategorySerializer(serializers.ModelSerializer):
    modifier_items = serializers.SerializerMethodField()

    class Meta:
        model = modifier_models.ModifierCategory
        fields = ['id', 'title', 'is_top', 'is_single', 'modifier_items', 'required', 'available', ]

    @staticmethod
    def get_modifier_items(obj):
        modifiers = modifier_models.Modifier.objects.filter(category_id=obj.id)
        serializer = ModifierSerializer(modifiers, many=True)
        if serializer:
            return serializer.data
        return None


class ModifierSerializer(serializers.ModelSerializer):
    class Meta:
        model = modifier_models.Modifier
        fields = ['id', 'title', 'price', 'default', 'available', ]


class OrderCreateSerializer(serializers.ModelSerializer):
    cart_items = CartSerializer(many=True, required=False)
    pre_order = serializers.BooleanField(required=False, default=True)
    pre_order_date = serializers.DateTimeField(required=False)

    class Meta:
        model = order_models.Order
        fields = ['id', 'created', 'tax_total', 'total_price', 'sub_total_price', 'cart_items', 'cafe', 'pre_order',
                  'pre_order_date', ]

    def create(self, validated_data):
        cart_items = validated_data.pop('cart_items')
        phone = self.context['view'].kwargs['phone']
        data_cart_items = self.initial_data.get('cart_items')

        customer = User.objects.get(phone=phone)
        validated_data['customer'] = customer
        order = order_models.Order.objects.create(**validated_data)
        cafe = order.cafe
        total_count = 0

        for cart_item in data_cart_items:
            product = cart_item['product']
            cart_item['order'] = order
            cart_item_total_count = cart_item['count']
            free_items_count = cart_item.pop('free_count')
            paid_items_count = cart_item_total_count - free_items_count

            if paid_items_count:
                paid_cart_item = order_models.Cart()
                paid_cart_item.order = order
                paid_cart_item.count = paid_items_count
                paid_cart_item.is_free = False
                paid_cart_item.product_id = product
                # paid_cart_item.price = paid_items_count * product.price
                paid_cart_item.save()
                modifiers = cart_item['modifiers']
                for modifier_item in modifiers:
                    modifier = order_models.CartModifier()
                    modifier.product_id = product
                    # modifier.price = product
                    modifier.order = order
                    modifier.modifier_id = modifier_item
                    modifier.cart = paid_cart_item
                    modifier.count = paid_items_count
                    modifier.save()

                # sub_total_price += paid_cart_item.price
                total_count += paid_cart_item.count

            if free_items_count:
                free_cart_item = order_models.Cart()
                free_cart_item.order = order
                free_cart_item.count = free_items_count
                free_cart_item.is_free = True
                free_cart_item.product_id = product
                free_cart_item.price = 0
                free_cart_item.save()
                modifiers = cart_item['modifiers']
                for modifier_item in modifiers:
                    modifier = order_models.CartModifier()
                    modifier.product_id = product
                    # modifier.price = product
                    modifier.order = order
                    modifier.modifier_id = modifier_item
                    modifier.cart = free_cart_item
                    modifier.count = free_items_count
                    modifier.save()
                free_items = user_models.FreeItem.objects.filter(owner=customer,
                                                                 root_cafe=cafe.user.settings,
                                                                 status=user_models.FreeItem.VALID
                                                                 ).order_by('pk')[0:free_items_count]
                free_items_pk_list = free_items.values_list('pk', flat=True)
                free_items_list = user_models.FreeItem.objects.select_for_update().filter(
                    pk__in=free_items_pk_list).update(product=product, status=user_models.FreeItem.REDEEMED)

        # tax_total = total_price * tax_rate / 100
        # total_price = sub_total_price + tax_total
        # order.total_price = total_price
        # order.sub_total_price = sub_total_price
        # order.tax_total = tax_total
        order.save()
        inviter = getattr(customer, 'inviter', None)
        if inviter:
            if inviter.given_free_item is False:
                user_models.FreeItem(owner=inviter.inviter).save()
                customer.inviter.given_free_item = True
                customer.inviter.save()

        return order


class CafeMealSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = product_models.CafeMeals
        fields = ('id', 'product',)


class PointSerializer(serializers.ModelSerializer):
    customer = serializers.SerializerMethodField()
    customer_avatar = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = user_models.Point
        fields = ('id', 'created_at', 'point_count', 'owner_id', 'order', 'customer', 'customer_avatar',)

    @staticmethod
    def get_created_at(obj):
        return obj.created_at.timestamp()

    @staticmethod
    def get_customer(obj):
        return obj.owner.get_full_name()

    def get_customer_avatar(self, obj):
        return obj.owner.get_avatar(self.context['request'])


class UserPointSerializer(serializers.ModelSerializer):
    cafe = serializers.IntegerField()

    class Meta:
        model = user_models.Point
        fields = ('point_count', 'cafe')


class OrderUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = order_models.Order
        fields = ['state', ]

    def update(self, instance, validated_data):
        if validated_data['state'] == self.Meta.model.READY:
            project_modules.send_push_for_topic(phone=instance.customer.phone, message='Your order is ready',
                                                tag='order_ready')
        super().update(instance=instance, validated_data=validated_data)
        return instance


class OrderedUsersSerializer(UsersSerializer):
    total_points = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = UsersSerializer.Meta.model
        fields = UsersSerializer.Meta.fields + ('total_points', 'avatar',)

    @staticmethod
    def get_total_points(obj):
        return obj.points.aggregate(Sum('point_count'))['point_count__sum']

    def get_avatar(self, obj):
        try:
            file = obj.user.get_avatar(self.context['request'])
        except (ValueError, AttributeError):
            return None

        return file


class ProductCategorySerializer(serializers.ModelSerializer):
    icon = serializers.SerializerMethodField()

    class Meta:
        model = product_models.ProductCategory
        fields = ('id', 'name', 'icon',)

    def get_icon(self, obj):
        try:
            request = self.context['request']
            file = request.build_absolute_uri(obj.icon.url)
        except (ValueError, AttributeError):
            return None
        return file


class OrderedUsersTransactionSerializer(serializers.ModelSerializer):
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()

    class Meta:
        model = order_models.Transaction
        fields = ('id', 'first_name', 'last_name', 'order', 'created_time',)

    @staticmethod
    def get_first_name(obj):
        return obj.order.customer.first_name

    @staticmethod
    def get_last_name(obj):
        return obj.order.customer.last_name


class UsersPointSerializer(serializers.ModelSerializer):
    customer = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    total_point = serializers.SerializerMethodField()
    free_items = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('phone', 'customer', 'total_point', 'avatar', 'free_items',)

    @staticmethod
    def get_customer(obj):
        return obj.get_full_name()

    def get_avatar(self, obj):
        return obj.get_avatar(self.context['request'])

    def get_total_point(self, obj):
        cafe_id = self.context['view'].kwargs.get('cafe_id')
        cafe = user_models.Cafe.objects.get(pk=cafe_id)
        return obj.points.filter(root_cafe__owner_id=cafe.user_id).aggregate(Sum('point_count'))['point_count__sum']

    def get_free_items(self, obj):
        cafe_id = self.context['view'].kwargs.get('cafe_id')
        cafe = user_models.Cafe.objects.get(pk=cafe_id)
        products_count = user_models.FreeItem.objects.filter(owner_id=obj.id, root_cafe__owner_id=cafe.user_id).count()
        return products_count


class CafePointsExchangedProductsSerializer(serializers.ModelSerializer):
    product = serializers.CharField(source='product.title', allow_null=True)
    expire_time = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = user_models.FreeItem
        fields = ('id', 'owner', 'product', 'point_count', 'expire_time', 'status',)

    @staticmethod
    def get_expire_time(obj):
        return obj.expire_time.timestamp() if obj.expire_time else None

    @staticmethod
    def get_status(obj):
        return obj.get_status()


class UserExchangedProductsSerializer(serializers.ModelSerializer):
    products = serializers.SerializerMethodField()
    cafe_name = serializers.CharField(source='settings.cafe_name')
    points = serializers.SerializerMethodField()
    logo = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'cafe_name', 'logo', 'points', 'products',)

    def get_products(self, obj):
        phone = self.context['view'].kwargs.get('phone')
        status = self.context['request'].GET.get('status', user_models.FreeItem.VALID)
        free_items = user_models.FreeItem.objects.filter(owner__phone=phone, root_cafe__owner=obj, status=status)
        serializer = CafePointsExchangedProductsSerializer(many=True, instance=free_items)
        return serializer.data

    def get_points(self, obj):
        phone = self.context['view'].kwargs.get('phone')
        points = user_models.Point.objects.filter(owner__phone=phone, root_cafe__owner=obj)
        return points.aggregate(total=Sum('point_count')).get('total')

    def get_logo(self, obj):
        try:
            return self.context['request'].build_absolute_uri(obj.settings.logo.url)
        except user_models.CafeGeneralSettings.DoesNotExist:
            return None


class UsersFreeItemsForCashierSerializer(serializers.ModelSerializer):
    expire_time = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    owner = serializers.CharField(source='owner.get_full_name')
    product = serializers.CharField(source='product.title', allow_null=True)

    class Meta:
        model = user_models.FreeItem
        fields = ('owner', 'product', 'created_at', 'expire_time', 'status',)

    @staticmethod
    def get_expire_time(obj):
        return obj.expire_time.timestamp()

    @staticmethod
    def get_created_at(obj):
        return obj.created_at.timestamp()


class CustomerFreeItemsSerializer(serializers.ModelSerializer):
    cafe_name = serializers.CharField(source='root_cafe.cafe_name')
    points = serializers.SerializerMethodField()
    logo = serializers.FileField(source='root_cafe.logo')
    product = serializers.CharField(source='product.title')

    class Meta:
        model = user_models.FreeItem
        fields = ('id', 'cafe_name', 'logo', 'points', 'product',)

    def get_points(self, obj):
        phone = self.context['view'].kwargs.get('phone')
        points = user_models.Point.objects.filter(owner__phone=phone)
        return points.aggregate(total=Sum('point_count')).get('total')


class FreeItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = user_models.FreeItem
        fields = ['status', ]

    def update(self, instance, validated_data):
        if validated_data['status'] == self.Meta.model.REDEEMED:
            project_modules.send_push_for_topic(phone=instance.owner.phone, message='Your free item was redeemed',
                                                tag='free_item_redeemed')
        super().update(instance=instance, validated_data=validated_data)
        return instance
