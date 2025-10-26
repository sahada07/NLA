from django.core.management.base import BaseCommand
from django.db import connection
import os
import glob

class Command(BaseCommand):
    help = 'Complete clean slate for betting app'
    
    def handle(self, *args, **options):
        # 1. Drop all betting tables
        tables = [
            'notifications',
            'user_subscriptions', 
            'bet_transactions',
            'bets',
            'draws',
            'game_odds',
            'bet_type',
            'game_types',
        ]
        
        with connection.cursor() as cursor:
            for table in tables:
                try:
                    cursor.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')
                    self.stdout.write(self.style.SUCCESS(f'✅ Dropped {table}'))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'⚠️ {table}: {str(e)}'))
            
            # 2. Clear migration records
            try:
                cursor.execute("DELETE FROM django_migrations WHERE app = 'betting'")
                self.stdout.write(self.style.SUCCESS('✅ Cleared migration records'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Error clearing records: {e}'))
        
        # 3. Delete migration files
        migration_dir = 'betting/migrations'
        migration_files = glob.glob(f'{migration_dir}/[0-9]*.py')
        
        for file in migration_files:
            try:
                os.remove(file)
                self.stdout.write(self.style.SUCCESS(f'✅ Deleted {file}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Error deleting {file}: {e}'))
        
        self.stdout.write(self.style.SUCCESS('\n🎯 Clean slate complete!'))
        self.stdout.write('Next steps:')
        self.stdout.write('  1. python manage.py makemigrations betting')
        self.stdout.write('  2. python manage.py migrate betting')