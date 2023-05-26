from django import forms


class AddInboundForm(forms.Form):
    def __init__(self, *args, server_name_choices=None, **kwargs):
        super(AddInboundForm, self).__init__(*args, **kwargs)
        if server_name_choices:
            self.fields['server_name'].choices = server_name_choices

    server_name = forms.ChoiceField()
    remark = forms.CharField(max_length=128, required=True)
    total = forms.IntegerField(required=True, min_value=0)
    expiry_time = forms.DateTimeField(input_formats=['%Y-%m-%dT%H:%M'], required=True,
                                      widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))
    protocol = forms.ChoiceField(choices=[('vmess', 'vmess-tcp-tls'),
                                          ('vless', 'vless-tcp-xtls'),
                                          ('trojan', 'trojan-tcp-xtls')])
