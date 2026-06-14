from django import forms

from .models import TrainingJob


class TrainingJobForm(forms.ModelForm):
    field_class = (
        'mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 '
        'text-sm text-slate-950 shadow-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20'
    )
    number_class = (
        'mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 '
        'text-sm text-slate-950 shadow-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20'
    )

    class Meta:
        model = TrainingJob
        fields = ['name', 'dataset_version', 'base_model', 'imgsz', 'epochs', 'batch', 'device', 'patience', 'workers', 'memo']
        labels = {
            'imgsz': 'Image size',
            'batch': 'Batch size',
            'memo': 'Training memo',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': self.field_class})

        for name in ['imgsz', 'epochs', 'batch', 'patience']:
            self.fields[name].widget.attrs.update({'class': self.number_class, 'min': '1'})

        self.fields['memo'].widget.attrs.update({
            'rows': '5',
            'class': f'{self.field_class} min-h-32 resize-y',
        })

    def clean_dataset_version(self):
        dataset_version = self.cleaned_data['dataset_version']
        if dataset_version.status != 'built':
            raise forms.ValidationError('Select a built DatasetVersion.')
        return dataset_version
