from django.contrib.auth.models import User
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from collections import defaultdict
import requests
from StarBurger import settings
from django.core.cache import cache
from hashlib import sha1
from django.core.validators import MinValueValidator

def fetch_coordinates(apikey, place):
    cache_key = sha1(place.encode()).hexdigest()
    if cache.get(cache_key):
        return cache.get(cache_key)
    base_url = "https://geocode-maps.yandex.ru/1.x"
    params = {"geocode": place, "apikey": apikey, "format": "json"}
    response = requests.get(base_url, params=params)
    response.raise_for_status()
    places_found = response.json()['response']['GeoObjectCollection']['featureMember']
    most_relevant = places_found[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    cache.set(cache_key, (lon, lat))
    return lon, lat


class Restaurant(models.Model):
    name = models.CharField('название', max_length=50)
    address = models.CharField('адрес', max_length=100, blank=True)
    contact_phone = models.CharField('контактный телефон', max_length=50, blank=True)
    lon = models.FloatField('Долгота', null=True, blank=True)
    lat = models.FloatField('Широта', null=True, blank=True)

    def save(self, *args, **kwargs):
        try:
            lon, lat = fetch_coordinates(settings.YANDEX_KEY, self.address)
            self.lon = lon
            self.lat = lat
        except (ConnectionError, TypeError):
            super(Restaurant, self).save(*args, **kwargs)
        super(Restaurant, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'


class ProductQuerySet(models.QuerySet):
    def available(self):
        return self.distinct().filter(menu_items__availability=True)


class ProductCategory(models.Model):
    name = models.CharField('название', max_length=50)

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField('название', max_length=50)
    category = models.ForeignKey(ProductCategory, null=True, blank=True, on_delete=models.SET_NULL,
                                 verbose_name='категория', related_name='products')
    price = models.DecimalField(
        'цена', max_digits=8, decimal_places=2,
        validators=[MinValueValidator(0, message="Предлагаешь доплатить?")])
    image = models.ImageField('картинка')
    special_status = models.BooleanField('спец.предложение', default=False, db_index=True)
    description = models.TextField('описание', max_length=200, blank=True)

    objects = ProductQuerySet.as_manager()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='menu_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='menu_items')
    availability = models.BooleanField('в продаже', default=True, db_index=True)

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]


class OrderQuerySet(models.QuerySet):

    def fetch_orders_with_total_and_restaurants(self):

        orders_products = OrderProduct.objects.values_list('order', 'product')
        orders_with_products = defaultdict(list)
        for set in orders_products:
            orders_with_products[set[0]].append(set[1])

        orders = self.all()
        orders_total_price = OrderProduct.objects.values('order').\
            annotate(order_total=ExpressionWrapper(Sum(F('quantity') * F('price')),
                     output_field=DecimalField()))
        orders_total_price = orders_total_price.values_list('order_id', 'order_total')
        orders_total_price = dict(orders_total_price)

        restaurant_menu_items = RestaurantMenuItem.objects.all()
        restaurant_menu_items = restaurant_menu_items \
                .filter(availability=True).values_list('restaurant__name',
                                                       'product',
                                                       'restaurant__lon',
                                                       'restaurant__lat')
        restaurants_with_products = defaultdict(list)
        for set in restaurant_menu_items:
            restaurants_with_products[(set[0], set[3], set[2])].append(set[1])

        for order in orders:
            restaurants = []
            products_set = orders_with_products[order.id]
            for restaurant, products in restaurants_with_products.items():
                if {*products_set}.issubset({*products}):
                    restaurants.append({restaurant[0]: (restaurant[1], restaurant[2])})
            order.restaurants = restaurants

            order.total_price = orders_total_price[order.id]
        return orders


class Order(models.Model):
    firstname = models.CharField('Имя', max_length=30)
    lastname = models.CharField('Фамилия', max_length=30)
    phonenumber = PhoneNumberField('Мобильный номер')
    address = models.CharField('Адрес доставки', max_length=100)

    class Status(models.TextChoices):
        new = 'new', _('Новый')
        in_progress = 'in_progress', _('Выполняется')
        completed = 'completed', _('Выполнен')

    class Payment(models.TextChoices):
        online = 'online', _('Картой курьеру')
        cash = 'cash', _('Наличными курьеру')
        prepayment = 'prepayment', _('Оплачено')

    status = models.CharField(
        'Статус заказа', max_length=11,
        choices=Status.choices, default=Status.new, db_index=True)
    payment = models.CharField(
        'Способ оплаты', max_length=10,
        choices=Payment.choices, default=Payment.cash, db_index=True)
    registrated_at = models.DateTimeField(verbose_name='Оформлен', default=timezone.now)
    called_at = models.DateTimeField(verbose_name='Принят', blank=True, null=True)
    delivered_at = models.DateTimeField(verbose_name='Доставлен', blank=True, null=True)
    comment = models.TextField('Комментарий', default='')
    restaurant = models.ForeignKey(Restaurant, blank=True, null=True, on_delete=models.SET_NULL)
    lon = models.FloatField('Долгота', null=True, blank=True)
    lat = models.FloatField('Широта', null=True, blank=True)

    def save(self, *args, **kwargs):
        try:
            lon, lat = fetch_coordinates(settings.YANDEX_KEY, self.address)
            self.lon = lon
            self.lat = lat
        except (ConnectionError, TypeError):
            super(Order, self).save(*args, **kwargs)
        super(Order, self).save(*args, **kwargs)
    objects = OrderQuerySet.as_manager()

    @property
    def total(self):
        total = self.order_items.annotate(
            total=ExpressionWrapper(F('quantity') * F('price'),
                                    output_field=DecimalField())).aggregate(Sum('total'))
        return total['total__sum']

    total.fget.short_description = "Общая сумма заказа"

    @property
    def order_restaurants(self):
        products_set = self.order_items.values_list('product', flat=True)
        restaurants_and_products = RestaurantMenuItem.objects\
            .filter(availability=True).values_list('restaurant', 'product')
        restaurants_with_products = defaultdict(list)
        restaurants = []
        for set in restaurants_and_products:
            restaurants_with_products[set[0]].append(set[1])
        for restaurant, products in restaurants_with_products.items():
            if {*products_set}.issubset({*products}):
                restaurants.append(restaurant)
        return Restaurant.objects.filter(id__in=restaurants)

    def __str__(order):
        return f'{order.firstname} {order.lastname} {order.address}'

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'


class BulkCreateManager(models.Manager):
    def bulk_create(self, objs, **kwargs):
        super().bulk_create(objs, **kwargs)
        for item in objs:
            post_save.send(item.__class__, instance=item, created=True)


class OrderProduct(models.Model):
    order = models.ForeignKey(Order, related_name='order_items',
                              on_delete=models.CASCADE, verbose_name="Заказ")
    product = models.ForeignKey(Product, related_name='order_items',
                                on_delete=models.CASCADE, verbose_name="Товары заказа")
    quantity = models.IntegerField('Количество', default=1)
    price = models.DecimalField('цена', max_digits=8,
                                decimal_places=2, validators=[MinValueValidator(0)])
    objects = BulkCreateManager()

    class Meta:
        unique_together = ['order', 'product']
        verbose_name = 'Элементы заказа'
        verbose_name_plural = 'Элементы заказов'

    def __str__(self):
        return f"{self.product.name} - {self.order}"


@receiver(post_save, sender=OrderProduct)
def set_order_price(sender, instance, created, **kwargs):
    if created:
        price = instance.product.price
        order_product = OrderProduct.objects.get(order=instance.order.id, product=instance.product.id)
        order_product.price = price
        order_product.save()
