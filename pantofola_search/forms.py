from django import forms
from django.templatetags.i18n import language
from haystack.forms import SearchForm


class MovieSearchByLanguageForm(SearchForm):
    lang = forms.ComboField(required=False)
    video_format = forms.ComboField(required=False)
    video_codec = forms.ComboField(required=False)
    video_source = forms.ComboField(required=False)
    audio_source = forms.ComboField(required=False)

    def search(self):

        sqs = super(MovieSearchByLanguageForm, self).search()

        sqs = sqs.exclude(is_broken=True)

        if not self.is_valid():
            return self.no_query_found()

        if self.cleaned_data['lang']:
            lang_code = self.cleaned_data['lang'].upper()
            print lang_code
            sqs = sqs.filter(language__iexact=lang_code)

        if self.cleaned_data['video_format']:
            code = self.cleaned_data['video_format']
            sqs = sqs.filter(video_format__iexact=code)

        if self.cleaned_data['video_codec']:
            code = self.cleaned_data['video_codec']
            sqs = sqs.filter(video_codec__iexact=code)

        if self.cleaned_data['video_source']:
            code = self.cleaned_data['video_source']
            sqs = sqs.filter(video_source__iexact=code)

        if self.cleaned_data['audio_source']:
            code = self.cleaned_data['audio_source']
            sqs = sqs.filter(audio_source__iexact=code)

        sqs = sqs.order_by('-seed', '-leech')

        return sqs