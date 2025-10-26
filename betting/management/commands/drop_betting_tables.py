from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Drop all betting tables'
    
    def handle(self, *args, **options):
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
                    cursor.execute(f'DROP TABLE IF EXISTS {table} CASCADE')
                    self.stdout.write(self.style.SUCCESS(f'✅ Dropped {table}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'❌ Error dropping {table}: {e}'))