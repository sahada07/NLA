from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone
from django.db.models import Q, Count, Sum
from django.core.mail import send_mail
from django.conf import settings
from decimal import Decimal
import json

from .models import Draw, Bet, GameType, UserSubscription, Notification
from users.models import User

logger = get_task_logger(__name__)

@shared_task
def check_draw_status():
    """
    Check and update draw statuses automatically
    Runs every minute
    """
    logger.info("Checking draw statuses...")
    
    now = timezone.now()
    updated_count = 0
    
    # Check for draws that should open betting
    scheduled_draws = Draw.objects.filter(
        status='scheduled',
        betting_opens_at__lte=now
    )
    
    for draw in scheduled_draws:
        draw.status = 'open'
        draw.save()
        updated_count += 1
        logger.info(f"Draw {draw.draw_number} opened for betting")
        
        # Send notifications to subscribers
        send_draw_opened_notification.delay(draw.id)
    
    # Check for draws that should close betting
    open_draws = Draw.objects.filter(
        status='open',
        betting_closes_at__lte=now
    )
    
    for draw in open_draws:
        draw.status = 'closed'
        draw.save()
        updated_count += 1
        logger.info(f"Draw {draw.draw_number} closed for betting")
        
        # Start draw process after a short delay
        process_draw_results.apply_async(
            args=[draw.id], 
            countdown=300  # 5 minutes after closing
        )
    
    logger.info(f"Updated {updated_count} draw statuses")
    return f"Updated {updated_count} draw statuses"

@shared_task
def process_draw_results(draw_id):
    """
    Process draw results - simulate drawing winning numbers
    This would integrate with actual draw systems in production
    """
    try:
        draw = Draw.objects.get(id=draw_id)
        logger.info(f"Processing draw results for {draw.draw_number}")
        
        # Simulate draw process
        draw.status = 'drawing'
        draw.save()
        
        # TODO: Integrate with actual draw system API
        # For now, generate random winning numbers
        import random
        winning_numbers = random.sample(
            range(draw.game_type.number_range_start, draw.game_type.number_range_end + 1),
            min(5, draw.game_type.max_numbers)
        )
        winning_numbers.sort()
        
        draw.winning_numbers = winning_numbers
        draw.machine_number = f"M{random.randint(1000, 9999)}"
        draw.status = 'completed'
        draw.save()
        
        logger.info(f"Draw {draw.draw_number} completed. Winning numbers: {winning_numbers}")
        
        # Check all bets for this draw
        check_bets_for_draw.delay(draw_id)
        
        # Send notifications
        send_draw_results_notification.delay(draw_id)
        
        return f"Draw {draw.draw_number} processed with numbers {winning_numbers}"
        
    except Draw.DoesNotExist:
        logger.error(f"Draw with id {draw_id} not found")
        return f"Draw with id {draw_id} not found"

@shared_task
def check_bets_for_draw(draw_id):
    """
    Check all bets for a completed draw and determine winners
    """
    try:
        draw = Draw.objects.get(id=draw_id)
        
        if draw.status != 'completed' or not draw.winning_numbers:
            logger.warning(f"Draw {draw.draw_number} not ready for bet checking")
            return f"Draw {draw.draw_number} not ready for bet checking"
        
        active_bets = Bet.objects.filter(draw=draw, status='active')
        total_bets = active_bets.count()
        winners = 0
        total_payout = Decimal('0.00')
        
        logger.info(f"Checking {total_bets} bets for draw {draw.draw_number}")
        
        for bet in active_bets:
            won = bet.check_win()
            if won:
                winners += 1
                total_payout += bet.actual_winnings
        
        # Update draw statistics
        draw.total_payout_amount = total_payout
        draw.save()
        
        logger.info(f"Draw {draw.draw_number}: {winners} winners, total payout: GH₵{total_payout}")
        
        return f"Checked {total_bets} bets, {winners} winners, GH₵{total_payout} paid out"
        
    except Draw.DoesNotExist:
        logger.error(f"Draw with id {draw_id} not found")
        return f"Draw with id {draw_id} not found"

@shared_task
def check_winning_bets():
    """
    Check for completed draws with winning numbers but unprocessed bets
    Runs every 10 minutes as a safety net
    """
    logger.info("Checking for unprocessed winning bets...")
    
    completed_draws = Draw.objects.filter(
        status='completed',
        winning_numbers__isnull=False
    )
    
    processed = 0
    for draw in completed_draws:
        unprocessed_bets = Bet.objects.filter(
            draw=draw,
            status='active'
        )
        
        if unprocessed_bets.exists():
            logger.info(f"Found {unprocessed_bets.count()} unprocessed bets for draw {draw.draw_number}")
            check_bets_for_draw.delay(draw.id)
            processed += 1
    
    logger.info(f"Initiated processing for {processed} draws")
    return f"Initiated processing for {processed} draws"

@shared_task
def send_draw_opened_notification(draw_id):
    """
    Send notifications when a draw opens for betting
    """
    try:
        draw = Draw.objects.get(id=draw_id)
        subscribers = UserSubscription.objects.filter(
            game_type=draw.game_type,
            is_active=True
        ).select_related('user')
        
        notification_count = 0
        
        for subscription in subscribers:
            Notification.objects.create(
                user=subscription.user,
                game_type=draw.game_type,
                notification_type='game_update',
                title=f'{draw.game_type.name} - Betting Open',
                message=f'Betting for {draw.draw_number} is now open! Closes at {draw.betting_closes_at.strftime("%H:%M")}'
            )
            notification_count += 1
        
        logger.info(f"Sent {notification_count} draw opened notifications")
        return f"Sent {notification_count} draw opened notifications"
        
    except Draw.DoesNotExist:
        logger.error(f"Draw with id {draw_id} not found")
        return f"Draw with id {draw_id} not found"

@shared_task
def send_draw_results_notification(draw_id):
    """
    Send notifications when draw results are published
    """
    try:
        draw = Draw.objects.get(id=draw_id)
        
        # Notify all users who bet on this draw
        users_with_bets = User.objects.filter(
            bets__draw=draw
        ).distinct()
        
        notification_count = 0
        
        for user in users_with_bets:
            Notification.objects.create(
                user=user,
                game_type=draw.game_type,
                notification_type='draw_result',
                title=f'{draw.game_type.name} - Results Published',
                message=f'Results for {draw.draw_number} are out! Winning numbers: {draw.winning_numbers}'
            )
            notification_count += 1
        
        logger.info(f"Sent {notification_count} draw results notifications")
        return f"Sent {notification_count} draw results notifications"
        
    except Draw.DoesNotExist:
        logger.error(f"Draw with id {draw_id} not found")
        return f"Draw with id {draw_id} not found"

@shared_task
def send_bet_result_notification(bet_id):
    """
    Send notification for individual bet results
    """
    try:
        bet = Bet.objects.get(id=bet_id)
        
        if bet.status in ['won', 'lost']:
            if bet.status == 'won':
                title = 'Congratulations! You Won!'
                message = f'Your bet {bet.bet_number} won GH₵{bet.actual_winnings:.2f}!'
            else:
                title = 'Bet Result'
                message = f'Your bet {bet.bet_number} did not win. Better luck next time!'
            
            Notification.objects.create(
                user=bet.user,
                game_type=bet.draw.game_type,
                bet=bet,
                notification_type='bet_won' if bet.status == 'won' else 'bet_lost',
                title=title,
                message=message
            )
            
            logger.info(f"Sent {bet.status} notification for bet {bet.bet_number}")
            return f"Sent {bet.status} notification for bet {bet.bet_number}"
    
    except Bet.DoesNotExist:
        logger.error(f"Bet with id {bet_id} not found")
        return f"Bet with id {bet_id} not found"

@shared_task
def send_daily_digest():
    """
    Send daily digest of betting activity to users
    Runs at 8 PM daily
    """
    logger.info("Sending daily digest notifications...")
    
    yesterday = timezone.now() - timezone.timedelta(days=1)
    
    users_with_activity = User.objects.filter(
        Q(bets__placed_at__date=yesterday.date()) |
        Q(notifications__created_at__date=yesterday.date())
    ).distinct()
    
    sent_count = 0
    
    for user in users_with_activity:
        # Get yesterday's bets
        yesterday_bets = Bet.objects.filter(
            user=user,
            placed_at__date=yesterday.date()
        )
        
        # Get unread notifications count
        unread_notifications = Notification.objects.filter(
            user=user,
            is_read=False
        ).count()
        
        if yesterday_bets.exists() or unread_notifications > 0:
            Notification.objects.create(
                user=user,
                notification_type='daily_digest',
                title='Daily Betting Digest',
                message=f'Yesterday: {yesterday_bets.count()} bets placed. You have {unread_notifications} unread notifications.'
            )
            sent_count += 1
    
    logger.info(f"Sent {sent_count} daily digest notifications")
    return f"Sent {sent_count} daily digest notifications"

@shared_task
def cleanup_old_data():
    """
    Clean up old data to maintain database performance
    Runs at 2 AM daily
    """
    logger.info("Cleaning up old data...")
    
    # Keep data for 90 days
    cutoff_date = timezone.now() - timezone.timedelta(days=90)
    
    # Archive and delete old notifications
    old_notifications = Notification.objects.filter(
        created_at__lt=cutoff_date,
        is_read=True
    )
    notifications_deleted = old_notifications.count()
    old_notifications.delete()
    
    # Archive old completed bets (you might want to move to archive table instead)
    old_bets = Bet.objects.filter(
        status__in=['won', 'lost', 'cancelled'],
        processed_at__lt=cutoff_date
    )
    bets_archived = old_bets.count()
    # old_bets.delete()  # Uncomment if you want to actually delete
    
    logger.info(f"Cleanup: {notifications_deleted} notifications deleted, {bets_archived} bets archived")
    return f"Cleanup: {notifications_deleted} notifications deleted, {bets_archived} bets archived"

@shared_task
def calculate_user_statistics(user_id):
    """
    Calculate and cache user statistics
    """
    try:
        user = User.objects.get(id=user_id)
        
        bets = Bet.objects.filter(user=user)
        total_bets = bets.count()
        total_staked = bets.aggregate(Sum('stake_amount'))['stake_amount__sum'] or Decimal('0.00')
        
        won_bets = bets.filter(status='won')
        total_won = won_bets.count()
        total_winnings = won_bets.aggregate(Sum('actual_winnings'))['actual_winnings__sum'] or Decimal('0.00')
        
        win_rate = (total_won / total_bets * 100) if total_bets > 0 else Decimal('0.00')
        active_bets = bets.filter(status='active').count()
        
        # Cache these statistics (you could store in user profile or cache)
        statistics = {
            'total_bets': total_bets,
            'total_staked': float(total_staked),
            'total_won': total_won,
            'total_winnings': float(total_winnings),
            'win_rate': float(win_rate),
            'active_bets': active_bets,
            'calculated_at': timezone.now().isoformat()
        }
        
        logger.info(f"Calculated statistics for user {user.username}")
        return statistics
        
    except User.DoesNotExist:
        logger.error(f"User with id {user_id} not found")
        return None

@shared_task
def process_completed_draws():
    """
    Process all completed draws that haven't been checked yet
    Runs every 5 minutes
    """
    logger.info("Processing completed draws...")
    
    completed_draws = Draw.objects.filter(
        status='completed',
        winning_numbers__isnull=False
    )
    
    processed = 0
    for draw in completed_draws:
        unprocessed_bets = Bet.objects.filter(
            draw=draw,
            status='active'
        )
        
        if unprocessed_bets.exists():
            logger.info(f"Processing {unprocessed_bets.count()} bets for draw {draw.draw_number}")
            check_bets_for_draw.delay(draw.id)
            processed += 1
    
    logger.info(f"Processed {processed} draws")
    return f"Processed {processed} draws"