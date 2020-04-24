from django.contrib import admin
from .models import Item, OrderItem, Order, Payment, Cupon, Refund, Address


def make_refund_accepted(modeladmin, request, queryset):
    queryset.update(refund_requested=False, refund_granted=True)


make_refund_accepted.short_description = 'Update orders to make refund granted'


class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'ordered',
        'being_delicered',
        'received',
        'refund_requested',
        'refund_granted',
        'shipping_address',
        'billing_address',
        'payment',
        'cupon'
    ]
    list_display_links = [
        'user',
        'shipping_address',
        'billing_address',
        'payment',
        'cupon'
    ]
    list_filter = [
        'ordered',
        'being_delicered',
        'received',
        'refund_requested',
        'refund_granted'
    ]
    search_fields = ['user__username',
                     'ref_code'
                     ]
    actions = [make_refund_accepted]


class AddressAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'address',
        'secondary_addrs',
        'division',
        'country',
        'zip_code',
        'address_type',
        'default'
    ]
    list_filter = [
        'user',
        'address_type',
        'country'
    ]
    search_fields = [
        'user',
        'address',
        'secondary_addrs',
        'division',
        'country',
        'zip_code'
    ]


admin.site.register(Item)
admin.site.register(OrderItem)
admin.site.register(Order, OrderAdmin)
admin.site.register(Payment)
admin.site.register(Cupon)
admin.site.register(Refund)
admin.site.register(Address, AddressAdmin)
