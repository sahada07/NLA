from django.core.management.base import BaseCommand
from betting.models import (GameType,BetType,GameOdds,Draw
                            ,Bet,BetTransaction)



class Command(BaseCommand):
    help= 'Create test data for betting app'

    