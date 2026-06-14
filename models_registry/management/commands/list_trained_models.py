from pathlib import Path

from django.core.management.base import BaseCommand

from models_registry.models import TrainedModel


class Command(BaseCommand):
    help = 'List trained models and show whether their model_path is usable for server inference.'

    def handle(self, *args, **options):
        models = TrainedModel.objects.select_related('training_job').order_by('id')
        active_count = models.filter(is_active_server_model=True).count()
        self.stdout.write(f'TrainedModel count: {models.count()}')
        self.stdout.write(f'Active server model count: {active_count}')
        for model in models:
            path = Path(model.model_path) if model.model_path else None
            exists = bool(path and path.exists())
            is_file = bool(path and path.is_file())
            suffix = path.suffix if path else ''
            usable = exists and is_file and suffix.lower() == '.pt'
            marker = '*' if model.is_active_server_model else ' '
            self.stdout.write(
                f'{marker} id={model.id} name={model.name} '
                f'path={model.model_path or "-"} exists={exists} is_file={is_file} '
                f'suffix={suffix or "-"} usable_pt={usable}'
            )

