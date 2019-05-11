import hmac
import hashlib
import logging
import requests
from requests.exceptions import RequestException
from urllib.parse import urlencode
from django.http import HttpResponseBadRequest, HttpResponse

from ..models import Order, OrderLine
from ..utils import price_as_sub_units
from .payments_base import PaymentsBase, PaymentError

logger = logging.getLogger()

# Keys the provider expects to find in the config
RESPA_PAYMENTS_BAMBORA_API_KEY = 'RESPA_PAYMENTS_BAMBORA_API_KEY'
RESPA_PAYMENTS_BAMBORA_API_SECRET = 'RESPA_PAYMENTS_BAMBORA_API_SECRET'
RESPA_PAYMENTS_BAMBORA_PAYMENT_METHODS = 'RESPA_PAYMENTS_BAMBORA_PAYMENT_METHODS'

# Param for respa redirect
UI_RETURN_URL_PARAM_NAME = 'RESPA_UI_RETURN_URL'


class BamboraPayformPayments(PaymentsBase):
    """Bambora Payform specific integration utilities and configuration
    testing docs: https://payform.bambora.com/docs/web_payments/?page=testing
    api reference: https://payform.bambora.com/docs/web_payments/?page=full-api-reference
    """

    def __init__(self, **kwargs):
        super(BamboraPayformPayments, self).__init__(**kwargs)
        self.url_payment_api = 'https://payform.bambora.com/pbwapi'
        self.url_payment_auth = '{}/auth_payment'.format(self.url_payment_api)
        self.url_payment_token = '{}/token/{{token}}'.format(self.url_payment_api)

    @staticmethod
    def get_config_template() -> dict:
        """Keys and value types what Bambora requires from environment"""
        return {
            RESPA_PAYMENTS_BAMBORA_API_KEY: str,
            RESPA_PAYMENTS_BAMBORA_API_SECRET: str,
            RESPA_PAYMENTS_BAMBORA_PAYMENT_METHODS: list
        }

    def order_create(self, request, ui_return_url, order) -> str:
        """Initiate payment by constructing the payload with necessary items"""

        respa_return_url = self.get_success_url(request)
        query_params = urlencode({UI_RETURN_URL_PARAM_NAME: ui_return_url})
        full_return_url = '{}?{}'.format(respa_return_url, query_params)

        payload = {
            'version': 'w3.1',
            'api_key': self.config.get(RESPA_PAYMENTS_BAMBORA_API_KEY),
            'payment_method': {
                'type': 'e-payment',
                'return_url': full_return_url,
                'notify_url': self.get_notify_url(request),
                'selected': self.config.get(RESPA_PAYMENTS_BAMBORA_PAYMENT_METHODS)
            },
            'currency': 'EUR',
            'order_number': str(order.order_number)
        }

        self.payload_add_products(payload, order)
        self.payload_add_customer(payload, order.reservation)
        self.payload_add_auth_code(payload)

        try:
            r = requests.post(self.url_payment_auth, json=payload)
            r.raise_for_status()
            return self.handle_order_create(r.json())
        except RequestException as e:
            raise ServiceUnavailableError("Payment service is unreachable") from e

    def handle_order_create(self, response) -> str:
        """Handling the Bambora payment auth response"""
        result = response['result']
        if result == 0:
            # Create the URL where user is redirected to complete the payment
            # Append "?minified" to get a stripped version of the payment page
            return self.url_payment_token.format(token=response['token'])
        elif result == 1:
            raise PayloadValidationError("Payment payload data validation failed: {}"
                                         .format(" ".join(response['errors'])))
        elif result == 2:
            raise DuplicateOrderError("Order with the same ID already exists")
        elif result == 10:
            raise ServiceUnavailableError("Payment service is down for maintentance")
        else:
            raise UnknownReturnCodeError("Return code was not recognized: {}".format(result))

    def payload_add_products(self, payload, order):
        """Attach info of bought products to payload

        Order lines that contain bought products are retrieved through order"""
        reservation = order.reservation
        order_lines = OrderLine.objects.filter(order=order.id)
        items = []
        for order_line in order_lines:
            product = order_line.product
            int_tax = int(product.tax_percentage)
            assert int_tax == product.tax_percentage  # make sure the tax is a whole number
            items.append({
                'id': product.sku,
                'title': product.name,
                'price': price_as_sub_units(product.get_price_for_reservation(reservation)),
                'pretax_price': price_as_sub_units(product.get_pretax_price_for_reservation(reservation)),
                'tax': int_tax,
                'count': order_line.quantity,
                'type': 1
            })
        payload['amount'] = price_as_sub_units(order.get_price())
        payload['products'] = items

    def payload_add_customer(self, payload, reservation):
        """Attach customer data to payload

        TODO Somehow split reserver first and last name into separate fields"""
        payload.update({
            'email': reservation.reserver_email_address,
            'customer': {
                'firstname': reservation.reserver_name,
                'lastname': reservation.reserver_name,
                'email': reservation.reserver_email_address,
                'address_street': reservation.billing_address_street,
                'address_zip': reservation.billing_address_zip,
                'address_city': reservation.billing_address_city,
            }
        })

    def payload_add_auth_code(self, payload):
        """Construct auth code string and hash it into payload"""
        data = '{}|{}'.format(payload['api_key'], payload['order_number'])
        payload.update(authcode=self.calculate_auth_code(data))

    def calculate_auth_code(self, data) -> str:
        """Calculate a hmac sha256 out of some data string"""
        return hmac.new(bytes(self.config.get(RESPA_PAYMENTS_BAMBORA_API_SECRET), 'latin-1'),
                        msg=bytes(data, 'latin-1'),
                        digestmod=hashlib.sha256).hexdigest().upper()

    def check_new_payment_authcode(self, request):
        """Validate that success/notify payload authcode matches"""
        is_valid = True
        auth_code_calculation_values = [
            request.GET[param_name]
            for param_name in ('RETURN_CODE', 'ORDER_NUMBER', 'SETTLED', 'CONTACT_ID', 'INCIDENT_ID')
            if param_name in request.GET
        ]
        correct_auth_code = self.calculate_auth_code('|'.join(auth_code_calculation_values))
        auth_code = request.GET['AUTHCODE']
        if not hmac.compare_digest(auth_code, correct_auth_code):
            logger.warning('Incorrect auth code "{}".'.format(auth_code))
            is_valid = False
        return is_valid

    def handle_success_request(self, request):
        """Handle the payform response after user has completed the payment flow in normal fashion"""
        logger.debug('Handling Bambora user return request, params: {}.'.format(request.GET))

        return_url = request.GET.get(UI_RETURN_URL_PARAM_NAME)
        if not return_url:
            # TODO should we actually make the whole thing fail here?
            logger.warning('Return URL missing.')
            return HttpResponseBadRequest()

        if not self.check_new_payment_authcode(request):
            return self.ui_redirect_failure(return_url)

        return_code = request.GET['RETURN_CODE']
        if return_code == '0':
            logger.debug('Payment completed successfully.')
            order = Order.objects.get(order_number=request.GET['ORDER_NUMBER'])
            order.status = Order.CONFIRMED
            order.save()
            return self.ui_redirect_success(return_url)
        elif return_code == '1':
            logger.debug('Payment failed.')
            order = Order.objects.get(order_number=request.GET['ORDER_NUMBER'])
            order.status = Order.REJECTED
            order.save()
            return self.ui_redirect_failure(return_url)
        elif return_code == '4':
            logger.debug('Transaction status could not be updated.')
            # TODO what should we do here? description of the situation:
            # Transaction status could not be updated after customer returned from the web page of a bank.
            # Please use the merchant UI to resolve the payment status.
            return self.ui_redirect_failure(return_url)
        elif return_code == '10':
            logger.debug('Maintenance break.')
            # TODO what now?
            return self.ui_redirect_failure(return_url)
        else:
            logger.debug('Incorrect RETURN_CODE "{}".'.format(return_code))
            return self.ui_redirect_failure(return_url)

    def handle_notify_request(self, request):
        """Handle the asynchronous part of payform response

        Arrives some time after user has completed the payment flow or stopped it abruptly.
        Bambora expects 20x response to acknowledge the notify was received"""
        if not self.check_new_payment_authcode(request):
            return HttpResponse(status=204)

        try:
            order = Order.objects.get(order_number=request.GET['ORDER_NUMBER'])
        except Order.DoesNotExist:
            # Target order might be deleted after posting but before the notify arrives
            logger.debug('Notify: Order not found.')
            return HttpResponse(status=204)

        return_code = request.GET['RETURN_CODE']
        if return_code == '0':
            logger.debug('Notify: Payment completed successfully.')
            if order.status != Order.CONFIRMED:
                order.status = Order.CONFIRMED
                order.save()
        elif return_code == '1':
            logger.debug('Notify: Payment failed.')
            if order.status != Order.REJECTED:
                order.status = Order.REJECTED
                order.save()
        else:
            logger.debug('Incorrect RETURN_CODE "{}".'.format(return_code))

        return HttpResponse(status=204)


class ServiceUnavailableError(PaymentError):
    """When payment service is unreachable, offline for maintenance etc"""


class PayloadValidationError(PaymentError):
    """When something is wrong or missing in the posted payload data"""


class DuplicateOrderError(PaymentError):
    """If order with the same ID has already been previously posted"""


class UnknownReturnCodeError(PaymentError):
    """If service returns a status code that is not recognized by the handler"""
