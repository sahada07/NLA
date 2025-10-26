from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Check which betting tables exist'
    
    def handle(self, *args, **options):
        expected_tables = [
            'game_types',
            'bet_type',
            'game_odds',
            'draws',
            'bets',
            'bet_transactions',
            'user_subscriptions',
            'notifications',
        ]
        
        with connection.cursor() as cursor:
            # Check each table individually
            for table in expected_tables:
                cursor.execute(f"""
                    SELECT EXISTS (
                        SELECT FROM pg_tables 
                        WHERE schemaname = 'public' 
                        AND tablename = '{table}'
                    )
                """)
                exists = cursor.fetchone()[0]
                
                if exists:
                    self.stdout.write(self.style.SUCCESS(f'✅ {table}'))
                else:
                    self.stdout.write(self.style.ERROR(f'❌ {table}'))