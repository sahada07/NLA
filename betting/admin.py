from django.contrib import admin
from .models import *
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone

# Define ModelAdmin classes FIRST, then register



@admin.register(GameType)
class GameTypeAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'code', 'category', 'min_stake', 'max_stake',
        'status_badge', 'total_subscribers'
    ]
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'code', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'category', 'description')
        }),
        ('Game Configuration', {
            'fields': (
                'min_numbers', 'max_numbers',
                'number_range_start', 'number_range_end'
            )
        }),
        ('Stake Configuration', {
            'fields': ('min_stake', 'max_stake')
        }),
        ('Draw Schedule', {
            'fields': ('draw_time', 'draw_days')
        }),
        ('Status', {
            'fields': ('is_active', 'created_at', 'updated_at')
        }),
    )
    
    def status_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px;">Active</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 3px;">Inactive</span>'
        )
    status_badge.short_description = 'Status'
    
    def total_subscribers(self, obj):
        count = obj.subscribers.filter(is_active=True).count()
        return format_html('<strong>{}</strong>', count)
    total_subscribers.short_description = 'Subscribers'


# ==========================================
# BET TYPE ADMIN
# ==========================================

@admin.register(BetType)
class BetTypeAdmin(admin.ModelAdmin):
    list_display = [
        'display_name', 'name', 'base_odds',
        'min_numbers_required', 'max_numbers_allowed', 'is_active'
    ]
    list_filter = ['is_active']
    search_fields = ['name', 'display_name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'display_name', 'description')
        }),
        ('Odds & Requirements', {
            'fields': (
                'base_odds',
                'min_numbers_required',
                'max_numbers_allowed'
            )
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


# ==========================================
# GAME ODDS ADMIN
# ==========================================

@admin.register(GameOdds)
class GameOddsAdmin(admin.ModelAdmin):
    list_display = [
        'game_type', 'bet_type', 'numbers_count',
        'numbers_matched', 'payout_multiplier'
    ]
    list_filter = ['game_type', 'bet_type']
    search_fields = ['game_type__name', 'bet_type__display_name']
    
    fieldsets = (
        ('Game & Bet Type', {
            'fields': ('game_type', 'bet_type')
        }),
        ('Configuration', {
            'fields': (
                'numbers_count',
                'numbers_matched',
                'payout_multiplier'
            )
        }),
    )

@admin.register(Draw)
class DrawAdmin(admin.ModelAdmin):
    list_display = [
        'draw_number', 'game_type', 'draw_date', 'draw_time',
        'status_badge', 'total_bets', 'total_stake_display',
        'betting_status'
    ]
    list_filter = ['status', 'game_type', 'draw_date']
    search_fields = ['draw_number', 'game_type__name']
    readonly_fields = [
        'total_bets', 'total_stake_amount', 'total_payout_amount',
        'created_at', 'updated_at'
    ]
    date_hierarchy = 'draw_date'
    
    fieldsets = (
        ('Draw Information', {
            'fields': ('game_type', 'draw_number', 'draw_date', 'draw_time')
        }),
        ('Betting Window', {
            'fields': ('betting_opens_at', 'betting_closes_at', 'status')
        }),
        ('Results', {
            'fields': ('winning_numbers', 'machine_number'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': (
                'total_bets', 'total_stake_amount', 'total_payout_amount'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        'open_betting', 'close_betting', 'process_results',
        'cancel_draw'
    ]
    
    def status_badge(self, obj):
        colors = {
            'scheduled': '#6c757d',
            'open': '#28a745',
            'closed': '#ffc107',
            'drawing': '#17a2b8',
            'completed': '#007bff',
            'cancelled': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def total_stake_display(self, obj):
        return format_html('<strong>GH₵ {}</strong>', obj.total_stake_amount)
    total_stake_display.short_description = 'Total Stakes'
    
    def betting_status(self, obj):
        if obj.is_betting_open():
            return format_html('<span style="color: green;">● Open</span>')
        return format_html('<span style="color: red;">● Closed</span>')
    betting_status.short_description = 'Betting'
    
    def open_betting(self, request, queryset):
        updated = queryset.filter(status='scheduled').update(status='open')
        self.message_user(request, f'{updated} draws opened for betting')
    open_betting.short_description = 'Open betting for selected draws'
    
    def close_betting(self, request, queryset):
        updated = queryset.filter(status='open').update(status='closed')
        self.message_user(request, f'{updated} draws closed for betting')
    close_betting.short_description = 'Close betting for selected draws'
    
    def cancel_draw(self, request, queryset):
        for draw in queryset:
            bets = draw.bets.filter(status='active')
            for bet in bets:
                bet.user.account_balance += bet.stake_amount
                bet.user.save()
                bet.status = 'cancelled'
                bet.save()
        
        queryset.update(status='cancelled')
        self.message_user(request, f'Draws cancelled and bets refunded')
    cancel_draw.short_description = 'Cancel selected draws (refund bets)'
    
    def process_results(self, request, queryset):
        processed = 0
        for draw in queryset.filter(status='completed'):
            if draw.winning_numbers:
                bets = draw.bets.filter(status='active')
                for bet in bets:
                    bet.check_win()
                processed += 1
        
        self.message_user(request, f'{processed} draws processed')
    process_results.short_description = 'Process results for selected draws'



@admin.register(Bet)
class BetAdmin(admin.ModelAdmin):
    list_display = [
        'bet_number', 'user_link', 'game_name', 'draw_number',
        'stake_display', 'potential_win_display', 'status_badge',
        'placed_at'
    ]
    list_filter = ['status', 'draw__game_type', 'placed_at']
    search_fields = [
        'bet_number', 'user__username', 'user__email',
        'draw__draw_number'
    ]
    # REMOVED readonly_fields to allow editing!
    readonly_fields = [
        'bet_number', 'placed_at', 'processed_at', 'paid_at'
    ]
    date_hierarchy = 'placed_at'
    
    # Make fields editable in admin
    fields = (
        'bet_number',
        'user',
        'draw',
        'bet_type',
        'selected_numbers',
        'stake_amount',
        'potential_winnings',
        'actual_winnings',
        'status',
        'agent',
        'agent_commission',
        'placed_at',
        'processed_at',
        'paid_at'
    )
    
    actions = ['check_results', 'mark_as_paid']
    
    def user_link(self, obj):
        url = reverse('admin:users_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'
    
    def game_name(self, obj):
        return obj.draw.game_type.name
    game_name.short_description = 'Game'
    
    def draw_number(self, obj):
        url = reverse('admin:betting_draw_change', args=[obj.draw.id])
        return format_html('<a href="{}">{}</a>', url, obj.draw.draw_number)
    draw_number.short_description = 'Draw'
    
    def stake_display(self, obj):
        return format_html('<strong>GH₵ {}</strong>', obj.stake_amount)
    stake_display.short_description = 'Stake'
    
    def potential_win_display(self, obj):
        return format_html('GH₵ {}', obj.potential_winnings)
    potential_win_display.short_description = 'Potential Win'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#6c757d',
            'active': '#17a2b8',
            'won': '#28a745',
            'lost': '#dc3545',
            'cancelled': '#6c757d',
            'paid': '#007bff',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def check_results(self, request, queryset):
        checked = 0
        for bet in queryset.filter(status='active'):
            if bet.draw.status == 'completed' and bet.draw.winning_numbers:
                bet.check_win()
                checked += 1
        
        self.message_user(request, f'{checked} bets checked')
    check_results.short_description = 'Check results for selected bets'
    
    def mark_as_paid(self, request, queryset):
        updated = queryset.filter(status='won').update(
            status='paid',
            paid_at=timezone.now()
        )
        self.message_user(request, f'{updated} bets marked as paid')
    mark_as_paid.short_description = 'Mark as paid'
    
    # Override save_model to generate bet_number if not provided
    def save_model(self, request, obj, form, change):
        if not obj.bet_number:
            from .models import generate_bet_number
            obj.bet_number = generate_bet_number()
        
        # Calculate potential winnings if not set
        if not change:  # Only on creation
            obj.save()  # Save first to get ID
            obj.calculate_potential_winnings()
        
        super().save_model(request, obj, form, change)



@admin.register(BetTransaction)
class BetTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'reference', 'user_link', 'transaction_type',
        'amount_display', 'balance_after', 'created_at'
    ]
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['reference', 'user__username', 'bet__bet_number']
    readonly_fields = [
        'bet', 'user', 'transaction_type', 'amount',
        'balance_before', 'balance_after', 'reference', 'created_at'
    ]
    date_hierarchy = 'created_at'
    
    # Don't allow adding transactions manually
    def has_add_permission(self, request):
        return False
    
    def user_link(self, obj):
        url = reverse('admin:users_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'
    
    def amount_display(self, obj):
        color = 'green' if obj.transaction_type in ['win', 'refund'] else 'red'
        symbol = '+' if obj.transaction_type in ['win', 'refund'] else '-'
        return format_html(
            '<span style="color: {};">{} GH₵ {}</span>',
            color, symbol, obj.amount
        )
    amount_display.short_description = 'Amount'



@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        'user_link', 'game_type', 'status_badge', 'subscribed_at'
    ]
    list_filter = ['is_active', 'game_type', 'subscribed_at']
    search_fields = ['user__username', 'game_type__name']
    date_hierarchy = 'subscribed_at'
    
    fields = ('user', 'game_type', 'is_active', 'subscribed_at', 'unsubscribed_at')
    readonly_fields = ['subscribed_at']
    
    def user_link(self, obj):
        url = reverse('admin:users_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'
    
    def status_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px;">Active</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 3px;">Inactive</span>'
        )
    status_badge.short_description = 'Status'




@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'user_link', 'notification_type',
        'read_badge', 'created_at'
    ]
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['title', 'message', 'user__username']
    readonly_fields = ['created_at', 'read_at']
    date_hierarchy = 'created_at'
    
    fields = (
        'user',
        'game_type',
        'bet',
        'notification_type',
        'title',
        'message',
        'is_read',
        'created_at',
        'read_at'
    )
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def user_link(self, obj):
        url = reverse('admin:users_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'
    
    def read_badge(self, obj):
        if obj.is_read:
            return format_html('<span style="color: green;">✓ Read</span>')
        return format_html('<span style="color: orange;">● Unread</span>')
    read_badge.short_description = 'Status'
    
    def mark_as_read(self, request, queryset):
        updated = queryset.filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        self.message_user(request, f'{updated} notifications marked as read')
    mark_as_read.short_description = 'Mark as read'
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False, read_at=None)
        self.message_user(request, f'{updated} notifications marked as unread')
    mark_as_unread.short_description = 'Mark as unread'



admin.site.site_header = "NLA Betting System Administration"
admin.site.site_title = "NLA Admin"
admin.site.index_title = "Welcome to NLA Betting System Admin"
# NOW register all models with their Admin classes
# admin.site.register(GameType, GameTypeAdmin)
# admin.site.register(BetType, BetTypeAdmin)
# admin.site.register(GameOdds, GameOddsAdmin)
# admin.site.register(Draw, DrawAdmin)
# admin.site.register(Bet, BetAdmin)
# admin.site.register(BetTransaction, BetTransactionAdmin)
# admin.site.register(UserSubscription, UserSubscriptionAdmin)
# admin.site.register(Notification, NotificationAdmin)