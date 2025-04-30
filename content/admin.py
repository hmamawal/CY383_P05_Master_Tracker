from django.contrib import admin
from .models import Challenge, Task, NCOR, Notification

class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'assignee', 'platoon', 'due_date', 'status')
    list_filter = ('status', 'platoon')
    search_fields = ('title', 'description', 'assignee__username')
    
class NCORAdmin(admin.ModelAdmin):
    list_display = ('user', 'task', 'created_date')
    list_filter = ('created_date',)
    search_fields = ('user__username', 'task__title')
    
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'task', 'created_date', 'read')
    list_filter = ('notification_type', 'read', 'created_date')
    search_fields = ('user__username', 'message')

admin.site.register(Challenge)
admin.site.register(Task, TaskAdmin)
admin.site.register(NCOR, NCORAdmin)
admin.site.register(Notification, NotificationAdmin)