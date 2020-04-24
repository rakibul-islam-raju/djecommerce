from django import forms
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget


DIVISION_CHOICES = (
    ('BAR', 'Barishal'),
    ('CHI', 'Chittagong'),
    ('DHA', 'Dhaka'),
    ('KHU', 'Khulna'),
    ('MYM', 'Mymensingh'),
    ('RAJ', 'Rajshahi'),
    ('RAN', 'Rangpur'),
    ('SYL', 'Sylhet')
)

PAYMENT_CHOICES = (
    ('C', 'Credit Card'),
    ('P', 'Paypal'),
)


class CheckoutForm(forms.Form):

    # shipping ===============>

    shipping_address = forms.CharField(max_length=100, required=False, widget=forms.TextInput(
        attrs={
            'class': 'form-control',
            'placeholder': 'Mirpur 2'
        }
    ))
    shipping_address2 = forms.CharField(max_length=100, required=False, widget=forms.TextInput(
        attrs={
            'class': 'form-control',
            'placeholder': 'Love Road'
        }
    ))
    shipping_country = CountryField(blank_label='(select country)').formfield(
        required=False,
        widget=CountrySelectWidget(
            attrs={
                'class': 'custom-select d-block w-100'}
        )
    )
    shipping_division = forms.ChoiceField(
        choices=DIVISION_CHOICES,
        widget=forms.Select(
            attrs={
                'class': 'custom-select d-block w-100'}
        ))
    shipping_zip = forms.CharField(
        max_length=6, widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Zip Code'
            }
        ))

    # billing ==============>

    billing_address = forms.CharField(max_length=100, required=False, widget=forms.TextInput(
        attrs={
            'class': 'form-control',
            'placeholder': 'Mirpur 2'
        }
    ))
    billing_address2 = forms.CharField(max_length=100, required=False, widget=forms.TextInput(
        attrs={
            'class': 'form-control',
            'placeholder': 'Love Road'
        }
    ))
    billing_country = CountryField(blank_label='(select country)').formfield(
        required=False,
        widget=CountrySelectWidget(
            attrs={
                'class': 'custom-select d-block w-100'}
        )
    )
    billing_division = forms.ChoiceField(
        choices=DIVISION_CHOICES,
        widget=forms.Select(
            attrs={
                'class': 'custom-select d-block w-100'}
        ))

    billing_zip = forms.CharField(
        max_length=6, widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Zip Code'
            }
        ))

    # checkbox ============>

    same_billing_address = forms.BooleanField(
        required=False, widget=forms.CheckboxInput(
            attrs={
                'class': 'custom-control-input'
            }
        ))

    set_default_shipping = forms.BooleanField(
        required=False, widget=forms.CheckboxInput(
            attrs={
                'class': 'custom-control-input'
            }
        ))
    use_default_shipping = forms.BooleanField(
        required=False, widget=forms.CheckboxInput(
            attrs={
                'class': 'custom-control-input'
            }
        ))

    set_default_billing = forms.BooleanField(
        required=False, widget=forms.CheckboxInput(
            attrs={
                'class': 'custom-control-input'
            }
        ))
    use_default_billing = forms.BooleanField(
        required=False, widget=forms.CheckboxInput(
            attrs={
                'class': 'custom-control-input'
            }
        ))

    payment_option = forms.ChoiceField(
        widget=forms.RadioSelect(), choices=PAYMENT_CHOICES)


class CuponForm(forms.Form):
    cupon = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Promo code',
        'aria_label': 'Recipient\'s username',
        'aria-describedby': 'basic-addon2'
    }))


class RefundForm(forms.Form):
    ref_code = forms.CharField(max_length=20)
    email = forms.EmailField()
    message = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}))
