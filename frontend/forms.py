from allauth.account.forms import LoginForm
import django.forms

class YourLoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
        super(YourLoginForm, self).__init__(*args, **kwargs)
        self.fields['login'].widget = django.forms.TextInput(attrs={'type': 'email', 'class': 'yourclass'})
        self.fields['password'].widget = django.forms.PasswordInput(attrs={'class': 'yourclass'})