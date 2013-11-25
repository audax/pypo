from django import forms
from .models import Item
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit


class CreateItemForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        h = FormHelper()
        h.form_id = 'create-item-form'
        h.form_method = 'post'
        h.form_class = 'form-horizontal'
        h.help_text_inline = True
        h.error_text_inline = True
        h.html5_required = True

        h.add_input(Submit('submit', 'Submit'))
        self.helper = h
        super(CreateItemForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Item
        fields = ('url', 'tags',)

class UpdateItemForm(CreateItemForm):

    class Meta:
        model = Item
        fields = ('tags',)

