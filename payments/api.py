from django.utils.translation import ugettext_lazy as _
from rest_framework import mixins, permissions, serializers, viewsets

from payments.models import Order, OrderLine, Product
from resources.api import resource
from resources.api.base import register_view
from resources.api.resource import ResourceSerializer


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ('id', 'type', 'name', 'pretax_price', 'tax_percentage')


class OrderLineCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderLine
        fields = ('product',)


class OrderLineReadSerializer(serializers.ModelSerializer):
    product = ProductSerializer()
    price = serializers.SerializerMethodField()

    class Meta:
        model = OrderLine
        fields = ('product', 'price')

    def get_price(self, obj):
        return str(obj.product.get_price_for_reservation(obj.order.reservation))


class OrderCreateSerializer(serializers.ModelSerializer):
    order_lines = OrderLineCreateSerializer(many=True)
    payment_url = serializers.SerializerMethodField()
    redirect_url = serializers.CharField(write_only=True)

    class Meta:
        model = Order
        fields = '__all__'

    def create(self, validated_data):
        order_lines_data = validated_data.pop('order_lines', [])
        validated_data.pop('redirect_url', '')
        order = super().create(validated_data)

        for order_line_data in order_lines_data:
            OrderLine.objects.create(order=order, **order_line_data)

        return order

    def validate_order_lines(self, value):
        if not value:
            raise serializers.ValidationError(_('At least one order line required.'))
        return value

    def get_payment_url(self, obj):
        return '{}?next={}'.format('www.example.com/payment-provider/pay', self.initial_data['redirect_url'])


class OrderReadSerializer(serializers.ModelSerializer):
    order_lines = OrderLineReadSerializer(many=True)

    class Meta:
        model = Order
        fields = '__all__'


class OrderViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Order.objects.all()

    #permission_classes = (permissions.IsAuthenticatedOrReadOnly,)  # TODO
    permission_classes = (permissions.AllowAny,)

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        else:
            return OrderReadSerializer


class ResourceProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ('id', 'name', 'type', 'pretax_price', 'price_type', 'tax_percentage')


class PaymentResourceSerializer(ResourceSerializer):
    products = ResourceProductSerializer(many=True)


# TODO temporal solution for replacing ResourceSerializer, figure out some better way
resource.ResourceListViewSet.serializer_class = PaymentResourceSerializer


register_view(OrderViewSet, 'order')
