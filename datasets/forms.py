from django import forms

from .models import DatasetVersion, ObjectClass

DATASET_BUILD_FIELD_CLASS = 'mt-2 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm'
DATASET_BUILD_CHECKBOX_CLASS = 'h-4 w-4 rounded border-slate-300 text-blue-600'


class ObjectClassForm(forms.ModelForm):
    class Meta:
        model = ObjectClass
        fields = ['name', 'display_name', 'description', 'color', 'is_active', 'sort_order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'color': forms.TextInput(attrs={'type': 'color'}),
        }


class ImageUploadForm(forms.Form):
    object_class = forms.ModelChoiceField(
        queryset=ObjectClass.objects.none(),
        required=False,
        empty_label='No class hint',
    )
    images = forms.FileField(required=False)
    zip_file = forms.FileField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['object_class'].queryset = ObjectClass.objects.filter(is_active=True).order_by('sort_order', 'name')

    def clean(self):
        cleaned_data = super().clean()
        images = self.files.getlist('images')
        zip_file = cleaned_data.get('zip_file')
        if not images and not zip_file:
            raise forms.ValidationError('Select image files or a ZIP file.')
        return cleaned_data


class DatasetBuildForm(forms.ModelForm):
    include_only_labeled_images = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': DATASET_BUILD_CHECKBOX_CLASS}),
    )
    exclude_invalid_boxes = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': DATASET_BUILD_CHECKBOX_CLASS}),
    )
    build_memo = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'class': DATASET_BUILD_FIELD_CLASS}),
    )

    class Meta:
        model = DatasetVersion
        fields = ['name', 'description', 'train_ratio', 'val_ratio', 'test_ratio', 'random_seed']
        widgets = {
            'name': forms.TextInput(attrs={'class': DATASET_BUILD_FIELD_CLASS}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': DATASET_BUILD_FIELD_CLASS}),
            'train_ratio': forms.NumberInput(attrs={'class': DATASET_BUILD_FIELD_CLASS}),
            'val_ratio': forms.NumberInput(attrs={'class': DATASET_BUILD_FIELD_CLASS}),
            'test_ratio': forms.NumberInput(attrs={'class': DATASET_BUILD_FIELD_CLASS}),
            'random_seed': forms.NumberInput(attrs={'class': DATASET_BUILD_FIELD_CLASS}),
        }

    def clean(self):
        cleaned_data = super().clean()
        train = cleaned_data.get('train_ratio') or 0
        val = cleaned_data.get('val_ratio') or 0
        test = cleaned_data.get('test_ratio') or 0
        if train <= 0 or val <= 0 or test <= 0:
            raise forms.ValidationError('Train, val, and test ratios must each be greater than 0.')
        if train + val + test != 100:
            raise forms.ValidationError('Train, val, and test ratios must add up to 100.')
        return cleaned_data


class AugmentedDatasetBuildForm(DatasetBuildForm):
    target_images_per_class = forms.IntegerField(
        label='Target images per class',
        required=False,
        initial=500,
        min_value=1,
        widget=forms.NumberInput(attrs={'class': DATASET_BUILD_FIELD_CLASS}),
    )
    max_augmentations_per_source_image = forms.IntegerField(
        label='Max augmentations per source image',
        required=False,
        initial=100,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': DATASET_BUILD_FIELD_CLASS}),
    )
    color_safe_augmentation = forms.BooleanField(
        label='Color-safe augmentation',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': DATASET_BUILD_CHECKBOX_CLASS}),
    )
