from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import ListView, DetailView, View
from .models import Item, Order, OrderItem, Address, Payment, Cupon, Refund
from .forms import CheckoutForm, CuponForm, RefundForm

import random
import string
import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


def create_ref_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))


class HomeView(ListView):
    # paginate_by = 10
    model = Item
    template_name = 'home.html'

    # queryset = Item.objects.all().order_by('-id')[:8]
    # context_object_name = 'items'

    # for passing queryset =================>

    def get_context_data(self, *args, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(*args, **kwargs)
        # Add in a QuerySet of all the books
        context['items'] = Item.objects.all().order_by('-id')[:8]
        context['shirts'] = Item.objects.filter(
            category='S').order_by('-id')[:4]
        context['outwears'] = Item.objects.filter(
            category='OW').order_by('-id')[:4]
        context['sportwears'] = Item.objects.filter(
            category='SW').order_by('-id')[:4]
        return context


class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                'object': order
            }
            return render(self.request, 'order_summary.html', context)
        except ObjectDoesNotExist:
            messages.warning(self.request, 'You do not have an active order.')
            return redirect('/')


class ItemDetailView(DetailView):
    model = Item
    template_name = 'product.html'


def is_valid_form(values):
    valid = True
    for field in values:
        if field == '':
            valid = False
    return valid


def category_product_view(request, category):
    products = Item.objects.filter(category=category).order_by('-id')

    if category == 'S':
        title = 'shirt'
    elif category == 'SW':
        title = 'sport wear'
    elif category == 'OW':
        title = 'outwear'
    else:
        title = None

    context = {
        'products': products,
        'title': title
    }
    return render(request, 'category_product.html', context)


# class CategoryProductView(View):
#     def get(self, *args, **kwargs):
#         products = Item.objects.filter(category='S').order_by('-id')
#         context = {
#             'products': products
#         }
#         return render(self.request, 'category_product.html', context)


class CheckoutView(View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            form = CheckoutForm()
            context = {
                'form': form,
                'order': order,
                'cuponform': CuponForm
            }

            shipping_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type='S',
                default=True
            )
            if shipping_address_qs.exists():
                context.update(
                    {'default_shipping_address': shipping_address_qs[0]}
                )

            billing_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type='B',
                default=True
            )
            if billing_address_qs.exists():
                context.update(
                    {'default_billing_address': billing_address_qs[0]}
                )

            return render(self.request, 'checkout.html', context)

        except ObjectDoesNotExist:
            messages.info(self.request, 'You do not have an active order')
            return redirect('core:checkout')

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)

            if form.is_valid():
                # shipping address
                use_default_shipping = form.cleaned_data.get(
                    'use_default_shipping')
                if use_default_shipping:
                    print('Using default shipping')
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='S',
                        default=True
                    )
                    if address_qs.exists():
                        shipping_address = address_qs[0]
                        order.shipping_address = shipping_address
                        order.save()
                    else:
                        messages.info(
                            self.request, 'No default shipping address')
                        return redirect('core:checkout')
                else:
                    print('User is entering a new shipping address')
                    shipping_address1 = form.cleaned_data.get(
                        'shipping_address')
                    shipping_address2 = form.cleaned_data.get(
                        'shipping_address2')
                    shipping_country = form.cleaned_data.get(
                        'shipping_country')
                    shipping_division = form.cleaned_data.get(
                        'shipping_division')
                    shipping_zip = form.cleaned_data.get('shipping_zip')

                    if is_valid_form([shipping_address1, shipping_country, shipping_division, shipping_zip]):
                        shipping_address = Address(
                            user=self.request.user,
                            address=shipping_address1,
                            secondary_addrs=shipping_address2,
                            division=shipping_division,
                            country=shipping_country,
                            zip_code=shipping_zip,
                            address_type='S'
                        )
                        shipping_address.save()

                        order.shipping_address = shipping_address
                        order.save()

                        # default shipping address
                        set_default_shipping = form.cleaned_data.get(
                            'set_default_shipping')
                        if set_default_shipping:
                            shipping_address.default = True
                            shipping_address.save()

                    else:
                        messages.info(
                            self.request, 'Please fill in the required shipping address fields')

                # Billing address
                use_default_billing = form.cleaned_data.get(
                    'use_default_billing')
                same_billing_address = form.cleaned_data.get(
                    'same_billing_address')

                if same_billing_address:
                    billing_address = shipping_address
                    billing_address.pk = None
                    billing_address.save()
                    billing_address.address_type = 'B'
                    billing_address.save()
                    order.billing_address = billing_address
                    order.save()

                elif use_default_shipping:
                    print('Using default billing')
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='B',
                        default=True
                    )
                    if address_qs.exists():
                        billing_address = address_qs[0]
                        order.billing_address = billing_address
                        order.save()
                    else:
                        messages.info(
                            self.request, 'No default billing address')
                        return redirect('core:checkout')
                else:
                    print('User is entering a new billing address')
                    billing_address1 = form.cleaned_data.get(
                        'billing_address')
                    billing_address2 = form.cleaned_data.get(
                        'billing_address2')
                    billing_country = form.cleaned_data.get(
                        'billing_country')
                    billing_division = form.cleaned_data.get(
                        'billing_division')
                    billing_zip = form.cleaned_data.get('billing_zip')

                    if is_valid_form([billing_address1, billing_country, billing_division, billing_zip]):
                        billing_address = Address(
                            user=self.request.user,
                            address=billing_address1,
                            secondary_addrs=billing_address2,
                            division=billing_division,
                            country=billing_country,
                            zip_code=billing_zip,
                            address_type='B'
                        )
                        billing_address.save()

                        order.billing_address = billing_address
                        order.save()

                        # set default billing address
                        set_default_billing = form.cleaned_data.get(
                            'set_default_billing')
                        if set_default_billing:
                            billing_address.default = True
                            billing_address.save()
                    else:
                        messages.info(
                            self.request, 'Please fill in the required billing address fields')

                # payment
                payment_option = form.cleaned_data.get('payment_option')

                if payment_option == 'C':
                    return redirect('core:payment', payment_option='credit')
                elif payment_option == 'P':
                    return redirect('core:payment', payment_option='paypal')
                else:
                    messages.warning(
                        self.request, 'Invalid Payment Option...!!!')
                    return redirect('core:checkout')
            else:
                messages.warning(self.request, 'Form is not valid')
                return redirect('core:checkout')

        except ObjectDoesNotExist:
            messages.warning(self.request, 'You do not have an active order.')
            return redirect('core:order-summary')


class PaymentView(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        if order.billing_address:
            context = {
                'order': order
            }
            return render(self.request, 'stripe.html', context)
        else:
            messages.warning(
                self.request, 'You have not added a billing address')
            return redirect(('core:checkout'))

    def post(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        token = self.request.POST.get('stripeToken')
        amount = int(order.get_total() * 100)  # cents

        try:
            charge = stripe.Charge.create(
                amount=amount,
                currency="usd",
                source=token
            )

            # create the payment
            payment = Payment()
            payment.stripe_charge_id = charge['id']
            payment.user = self.request.user
            payment.amount = order.get_total()
            payment.save()

            # assign the payment to order
            order_items = order.items.all()
            order_items.update(ordered=True)
            for item in order_items:
                item.save()

            order.ordered = True
            order.payment = payment
            order.ref_code = create_ref_code()
            order.save()

            messages.success(self.request, 'Your order successfully placed.')
            return redirect('/')

        except stripe.error.CardError as e:
            # Since it's a decline, stripe.error.CardError will be caught
            messages.warning(self.request, f'{e.error.message}')
            return redirect('/')

        except stripe.error.RateLimitError as e:
            # Too many requests made to the API too quickly
            messages.warning(self.request, 'Rate limit error')
            return redirect('/')

        except stripe.error.InvalidRequestError as e:
            # Invalid parameters were supplied to Stripe's API
            messages.warning(self.request, 'Invalid parameters')
            return redirect('/')

        except stripe.error.AuthenticationError as e:
            # Authentication with Stripe's API failed
            # (maybe you changed API keys recently)
            messages.warning(self.request, 'Not authenticated')
            return redirect('/')

        except stripe.error.APIConnectionError as e:
            # Network communication with Stripe failed
            messages.warning(self.request, 'Network error')
            return redirect('/')

        except stripe.error.StripeError as e:
            # Display a very generic error to the user, and maybe send
            # yourself an email
            messages.warning(
                self.request, 'Something went wrong. You were not charged. Pleage try again.')
            return redirect('/')

        except Exception as e:
            # send email to ourselves
            messages.warning(
                self.request, 'A serious error occured. We have been notified.')
            return redirect('/')


@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        item=item, user=request.user, ordered=False)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, 'This item quantity was updated.')
            return redirect('core:order-summary')
        else:
            order.items.add(order_item)
            messages.info(request, 'This item was added to your cart.')
            return redirect('core:order-summary')
    else:
        order_date = timezone.now()
        order = Order.objects.create(
            user=request.user, order_date=order_date)
        order.items.add(order_item)
        messages.info(request, 'This item was added to your cart.')
        return redirect('core:order-summary')


@login_required
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item, user=request.user, ordered=False)[0]
            order.items.remove(order_item)
            messages.info(request, 'This item was removed from your cart.')
            return redirect('core:order-summary')
        else:
            messages.info(request, 'This item was not in your cart.')
            return redirect('core:product', slug=slug)
    else:
        # add a message saying the doesnt have an order
        messages.info(request, 'You do not have an active order.')
        return redirect('core:product', slug=slug)


@login_required
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item, user=request.user, ordered=False)[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
            messages.info(request, 'This item quantity updated')
            return redirect('core:order-summary')
        else:
            messages.info(request, 'This item was not in your cart.')
            return redirect('core:product', slug=slug)
    else:
        # add a message saying the doesnt have an order
        messages.info(request, 'You do not have an active order.')
        return redirect('core:product', slug=slug)


def get_cupon(request, cupon):
    try:
        cupon = Cupon.objects.get(cupon=cupon)
        return cupon
    except ObjectDoesNotExist:
        messages.info(request, 'This Cupon does not exist')
        return redirect('core:checkout')


class AddCuponView(View):
    def post(self, *args, **kwargs):
        form = CuponForm(self.request.POST or None)
        if form.is_valid():
            try:
                cupon = form.cleaned_data.get('cupon')
                order = Order.objects.get(
                    user=self.request.user, ordered=False)
                order.cupon = get_cupon(self.request, cupon)
                order.save()
                messages.success(self.request, 'Successfully added cupon')
                return redirect('core:checkout')
            except ObjectDoesNotExist:
                messages.info(self.request, 'You do not have an active order')
                return redirect('core:checkout')


class RequestRefundView(View):
    def get(self, *args, **kwargs):
        form = RefundForm()
        context = {
            'form': form
        }
        return render(self.request, 'request_refund.html', context)

    def post(self, *args, **kwargs):
        form = RefundForm(self.request.POST)
        if form.is_valid():
            ref_code = form.cleaned_data.get('ref_code')
            email = form.cleaned_data.get('email')
            message = form.cleaned_data.get('message')
            # edit the order
            try:
                order = Order.objects.get(ref_code=ref_code)
                order.refund_requested = True
                order.save()

                # store the refund
                refund = Refund()
                refund.order = order
                refund.reason = message
                refund.email = email
                refund.save()

                messages.info(self.request, 'Your request was received')
                return redirect('core:request-refund')

            except ObjectDoesNotExist:
                messages.info(self.request, 'Order Does not exist')
                return redirect('core:request-refund')
