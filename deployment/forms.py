from django import forms

from .models import AndroidModelPackage


class AndroidModelExportForm(forms.ModelForm):
    export_memo = forms.CharField(
        required=False,
        label='Export memo',
        widget=forms.Textarea(attrs={'rows': 4}),
        help_text='Optional note stored in the package export log before the export starts.',
    )

    class Meta:
        model = AndroidModelPackage
        fields = ['trained_model', 'model_version', 'input_size', 'confidence_threshold', 'iou_threshold']

    def clean_trained_model(self):
        trained_model = self.cleaned_data['trained_model']
        if not trained_model.model_path:
            raise forms.ValidationError('Selected TrainedModel has no model_path.')
        return trained_model

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        control_class = (
            'mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 '
            'text-sm text-slate-950 shadow-sm outline-none '
            'focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20'
        )
        textarea_class = f'{control_class} min-h-28 resize-y'
        for name, field in self.fields.items():
            field.widget.attrs['class'] = textarea_class if name == 'export_memo' else control_class
        self.fields['trained_model'].empty_label = 'Select a trained model'
        self.fields['model_version'].help_text = 'Use a unique version, e.g. soap_case_color_aug_500_v1_tflite.'
