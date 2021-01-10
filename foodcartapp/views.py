from django.http import JsonResponse
from django.templatetags.static import static
import json
from .models import Order, Product, OrderProduct
from rest_framework.decorators import api_view
from rest_framework.response import Response

def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })



def product_list_api(request):
    products = Product.objects.select_related('category').available()
    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            },
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })

# {'products': [{'product': 2, 'quantity': 1}], 'firstname': 'Артем', 'lastname': '12335', 'phonenumber': '0981990993', 'address': 'Московский проспект 9'}


@api_view(['POST'])
def register_order(request):
    data = request.data
    order = Order.objects.create(
        name=data['firstname'],
        lastname=data['lastname'],
        phone=data['phonenumber'],
        delivery_address=data['address']
    )
    order_products = data['products']
    for order_product in order_products:
        product = OrderProduct.objects.create(
            order=order,
            product=Product.objects.get(id=order_product['product']),
            quantity=order_product['quantity'])
        product.save()
    order.save()
    return Response(data)
