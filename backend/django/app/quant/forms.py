from django import forms

class MT5LoginForm(forms.Form):
    login = forms.IntegerField(
        label="Login MT5",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '123456789'
        })
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••'
        })
    )
    server = forms.CharField(
        label="Servidor",
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'MetaQuotes-Demo'
        })
    )