from django import forms

from .models import AndroidModelPackage


class AndroidModelExportForm(forms.ModelForm):
    export_memo = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3}))

    class Meta:
        model = AndroidModelPackage
        fields = ['trained_model', 'model_version', 'input_size', 'confidence_threshold', 'iou_threshold']

    def clean_trained_model(self):
        trained_model = self.cleaned_data['trained_model']
        if not trained_model.model_path:
            raise forms.ValidationError('Selected TrainedModel has no model_path.')
        return trained_model
