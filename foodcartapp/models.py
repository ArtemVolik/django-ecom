from django.contrib.auth.models import User
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Sum, F, ExpressionWrapper, DecimalField


class Restaurant(models.Model):
    name = models.CharField('название', max_length=50)
    address = models.CharField('адрес', max_length=100, blank=True)
    contact_phone = models.CharField('контактный телефон', max_length=50, blank=True)

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
    price = models.DecimalField('цена', max_digits=8, decimal_places=2)
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


class Order(models.Model):
    firstname = models.CharField('Имя', max_length=30)
    lastname = models.CharField('Фамилия', max_length=30)
    phonenumber = PhoneNumberField('Мобильный номер')
    address = models.CharField('Адрес доставки', max_length=100)

    def total(self):
        total = self.order_items.annotate(
            total=ExpressionWrapper(F('quantity') * F('price'),
            output_field=DecimalField())).aggregate(Sum('total'))
        return total['total__sum']

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
    order = models.ForeignKey(Order, related_name='order_items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.CASCADE)
    quantity = models.IntegerField('Количество', default=1)
    price = models.DecimalField('цена', max_digits=8, decimal_places=2, default=None, null=True)
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
