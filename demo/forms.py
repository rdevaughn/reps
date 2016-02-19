from django import forms

class ZipForm(forms.Form):
    zip = forms.CharField(label='Zip', max_length=5)

class AddressForm(forms.Form):
    street = forms.CharField(label="Street", max_length=100)
    zip = forms.CharField(label='Zip', max_length=5)
