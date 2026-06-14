from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from models_registry.models import TrainedModel


class Command(BaseCommand):
    help = 'Set the active server TrainedModel used by /api/detect/server/.'

    def add_arguments(self, parser):
        parser.add_argument('--id', type=int, required=True, dest='model_id')
        parser.add_argument(
            '--allow-missing-file',
            action='store_true',
            help='Allow activation even if model_path does not currently point to a valid .pt file.',
        )

    def handle(self, *args, **options):
        model = TrainedModel.objects.get(pk=options['model_id'])
        path = Path(model.model_path) if model.model_path else None
        if not options['allow_missing_file']:
            if not path:
                raise CommandError('Selected model does not have model_path.')
            if path.suffix.lower() != '.pt':
                raise CommandError(f'Selected model_path must be a .pt file: {path}')
            if not path.exists() or not path.is_file():
                raise CommandError(f'Selected model_path does not exist or is not a file: {path}')

        with transaction.atomic():
            TrainedModel.objects.exclude(pk=model.pk).update(is_active_server_model=False)
            model.is_active_server_model = True
            model.save(update_fields=['is_active_server_model'])

        self.stdout.write(self.style.SUCCESS(f'Active server model set: id={model.id} name={model.name}'))

