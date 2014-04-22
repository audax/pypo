from django import forms
import six
from taggit.forms import TagWidget
from .models import Item
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit


def edit_string_for_tags(tags):
    return ', '.join(sorted(tag.name for tag in tags))


class QuotelessTagWidget(TagWidget):
    def render(self, name, value, attrs=None):
        if value is not None and not isinstance(value, six.string_types):
            value = edit_string_for_tags([o.tag for o in value.select_related("tag")])
        return super(QuotelessTagWidget, self).render(name, value, attrs)

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

    def clean(self):
        cleaned_data = self.cleaned_data
        cleaned_data['tags'] = [tag[:99] for tag in cleaned_data['tags']]
        return cleaned_data

    class Meta:
        model = Item
        fields = ('url', 'tags',)
        widgets = {
            'tags': QuotelessTagWidget()
        }

class UpdateItemForm(CreateItemForm):

    class Meta:
        model = Item
        fields = ('tags',)
        widgets = {
            'tags': QuotelessTagWidget()
        }

