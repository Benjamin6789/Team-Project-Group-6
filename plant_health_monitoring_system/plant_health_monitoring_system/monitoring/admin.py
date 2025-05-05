from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.html import format_html
from django.db import connection
import os
import csv
import json
import shutil
from .models import PlantData, SystemStatus

# Register for admin-only actions (not tied to a specific model)
@admin.register(admin.models.LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    # Make LogEntry read-only
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    # Add custom admin views for system-wide actions
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('system-settings/', self.admin_site.admin_view(self.system_settings_view), name='system-settings'),
            path('clear-csv/', self.admin_site.admin_view(self.clear_csv_view), name='clear-csv'),
            path('backup-csv/', self.admin_site.admin_view(self.backup_csv_view), name='backup-csv'),
        ]
        return custom_urls + urls
    
    def system_settings_view(self, request):
        # Get data storage paths
        csv_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Get-Data', 'Data.csv')
        db_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'db.sqlite3')
        
        # Get file sizes
        csv_size = os.path.getsize(csv_file_path) if os.path.exists(csv_file_path) else 0
        db_size = os.path.getsize(db_file_path) if os.path.exists(db_file_path) else 0
        
        # Format sizes for display
        csv_size_human = f"{csv_size / (1024 * 1024):.2f} MB" if csv_size > 1024*1024 else f"{csv_size / 1024:.2f} KB"
        db_size_human = f"{db_size / (1024 * 1024):.2f} MB" if db_size > 1024*1024 else f"{db_size / 1024:.2f} KB"
        
        # Get free disk space
        disk_usage = shutil.disk_usage(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        free_space = disk_usage.free
        total_space = disk_usage.total
        free_space_human = f"{free_space / (1024 * 1024 * 1024):.2f} GB"
        total_space_human = f"{total_space / (1024 * 1024 * 1024):.2f} GB"
        usage_percent = (total_space - free_space) / total_space * 100
        
        context = {
            'title': 'System Settings',
            'csv_file_path': csv_file_path,
            'db_file_path': db_file_path,
            'csv_size': csv_size,
            'db_size': db_size,
            'csv_size_human': csv_size_human,
            'db_size_human': db_size_human,
            'free_space': free_space_human,
            'total_space': total_space_human,
            'usage_percent': f"{usage_percent:.1f}%",
        }
        return render(request, 'admin/monitoring/system_settings.html', context)
    
    def clear_csv_view(self, request):
        # Get the CSV file path
        csv_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Get-Data', 'Data.csv')
        
        if request.method == 'POST' and 'confirm' in request.POST:
            # Create backup before clearing
            backup_path = csv_file_path + '.bak'
            if os.path.exists(csv_file_path):
                shutil.copy2(csv_file_path, backup_path)
                
                # Clear the file but keep the header
                with open(csv_file_path, 'r') as f:
                    header = f.readline().strip()
                
                with open(csv_file_path, 'w') as f:
                    f.write(header + '\n')
                
                return JsonResponse({'success': True, 'message': 'CSV file cleared successfully. A backup was created.'})
            else:
                return JsonResponse({'success': False, 'message': 'CSV file does not exist.'})
        
        return render(request, 'admin/monitoring/clear_csv.html', {'csv_file_path': csv_file_path})
    
    def backup_csv_view(self, request):
        # Get the CSV file path
        csv_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Get-Data', 'Data.csv')
        
        if request.method == 'POST' and 'confirm' in request.POST:
            # Create backup
            import datetime
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = csv_file_path + f'.backup_{timestamp}'
            
            if os.path.exists(csv_file_path):
                shutil.copy2(csv_file_path, backup_path)
                return JsonResponse({'success': True, 'message': f'Backup created at {backup_path}'})
            else:
                return JsonResponse({'success': False, 'message': 'CSV file does not exist.'})
        
        return render(request, 'admin/monitoring/backup_csv.html', {'csv_file_path': csv_file_path})

# Admin for PlantData model
@admin.register(PlantData)
class PlantDataAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'temperature_display', 'humidity_display', 'soil_moisture_display', 
                   'air_quality_display', 'light_display', 'pressure_display', 
                   'oxidising_display', 'reducing_display')
    list_filter = ('timestamp',)
    search_fields = ('timestamp',)
    date_hierarchy = 'timestamp'
    readonly_fields = ('timestamp',)
    
    def temperature_display(self, obj):
        return f"{obj.temperature:.1f} °C"
    temperature_display.short_description = "Temperature"
    
    def humidity_display(self, obj):
        return f"{obj.humidity:.1f} %"
    humidity_display.short_description = "Humidity"
    
    def soil_moisture_display(self, obj):
        return f"{obj.soil_moisture:.1f} %"
    soil_moisture_display.short_description = "Soil Moisture"
    
    def air_quality_display(self, obj):
        return f"{obj.air_quality:.2f}"
    air_quality_display.short_description = "Air Quality"
    
    def light_display(self, obj):
        if obj.light is None:
            return "-"
        return f"{obj.light:.1f}"
    light_display.short_description = "Light"
    
    def pressure_display(self, obj):
        if obj.pressure is None:
            return "-"
        return f"{obj.pressure:.2f} hPa"
    pressure_display.short_description = "Pressure"
    
    def oxidising_display(self, obj):
        if obj.oxidising is None:
            return "-"
        return f"{obj.oxidising:.2f}"
    oxidising_display.short_description = "Oxidising"
    
    def reducing_display(self, obj):
        if obj.reducing is None:
            return "-"
        return f"{obj.reducing:.2f}"
    reducing_display.short_description = "Reducing"
    
    # Add custom action to delete old data
    actions = ['delete_old_data']
    
    def delete_old_data(self, request, queryset):
        """Delete data older than the specified number of days"""
        
        # If called from the form in data_management, get days parameter
        days = request.POST.get('days')
        
        if days:
            try:
                days = int(days)
                from django.utils import timezone
                from datetime import timedelta
                
                # Calculate the cutoff date
                cutoff_date = timezone.now() - timedelta(days=days)
                
                # Filter and delete data older than the cutoff date
                old_data = PlantData.objects.filter(timestamp__lt=cutoff_date)
                count = old_data.count()
                old_data.delete()
                
                self.message_user(request, f"Successfully deleted {count} records older than {days} days.")
                return
            except ValueError:
                self.message_user(request, f"Invalid days value: {days}", level='ERROR')
                return
        
        # If we get here, it's a normal action on selected items
        rows_deleted = queryset.delete()[0]
        if rows_deleted == 1:
            message = "1 plant data item was"
        else:
            message = f"{rows_deleted} plant data items were"
        self.message_user(request, f"{message} successfully deleted.")
    delete_old_data.short_description = "Delete selected data"
    
    # Custom admin views for database actions
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('data-management/', self.admin_site.admin_view(self.data_management_view), name='data-management'),
            path('export-csv/', self.admin_site.admin_view(self.export_csv_view), name='export-csv'),
            path('csv-stats/', self.admin_site.admin_view(self.csv_stats_view), name='csv-stats'),
        ]
        return custom_urls + urls
    
    def data_management_view(self, request):
        # Get database stats
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM monitoring_plantdata")
            total_records = cursor.fetchone()[0]
            
            # Get table size information if using PostgreSQL
            # This is PostgreSQL-specific, adjust if using a different database
            try:
                cursor.execute("""
                    SELECT pg_size_pretty(pg_total_relation_size('monitoring_plantdata'))
                """)
                table_size = cursor.fetchone()[0]
            except:
                table_size = "Not available (requires PostgreSQL)"
        
        context = {
            'title': 'Data Management',
            'total_records': total_records,
            'table_size': table_size,
            'opts': self.model._meta,
        }
        return render(request, 'admin/monitoring/data_management.html', context)
    
    def export_csv_view(self, request):
        # Create a CSV file with all data
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="plant_data_export.csv"'
        
        writer = csv.writer(response)
        # Write header
        writer.writerow(['Timestamp', 'Temperature', 'Humidity', 'Soil Moisture', 'Air Quality', 
                        'Light', 'Pressure', 'Oxidising', 'Reducing'])
        
        # Write data
        for data in PlantData.objects.all().order_by('-timestamp'):
            writer.writerow([
                data.timestamp,
                data.temperature,
                data.humidity,
                data.soil_moisture,
                data.air_quality,
                data.light,
                data.pressure,
                data.oxidising,
                data.reducing
            ])
        
        return response
    
    def csv_stats_view(self, request):
        # Get the CSV file path
        csv_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Get-Data', 'Data.csv')
        
        # Get file stats
        stats = {}
        if os.path.exists(csv_file_path):
            stats['exists'] = True
            stats['size'] = os.path.getsize(csv_file_path)
            stats['size_human'] = f"{stats['size'] / (1024 * 1024):.2f} MB" if stats['size'] > 1024*1024 else f"{stats['size'] / 1024:.2f} KB"
            stats['last_modified'] = os.path.getmtime(csv_file_path)
            stats['path'] = csv_file_path
            
            # Count rows in CSV
            with open(csv_file_path, 'r') as f:
                stats['rows'] = sum(1 for line in f)
                stats['data_rows'] = stats['rows'] - 1  # Subtract header row
        else:
            stats['exists'] = False
        
        context = {
            'title': 'CSV File Statistics',
            'stats': stats,
            'opts': self.model._meta,
        }
        return render(request, 'admin/monitoring/csv_stats.html', context)
    
    # Add custom view link to changelist
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['data_management_url'] = 'admin:data-management'
        extra_context['export_csv_url'] = 'admin:export-csv'
        extra_context['csv_stats_url'] = 'admin:csv-stats'
        return super().changelist_view(request, extra_context=extra_context)

# Admin for SystemStatus model
@admin.register(SystemStatus)
class SystemStatusAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'last_collection_time', 'collection_duration_display', 'is_collecting_delayed', 'status_message')
    readonly_fields = ('timestamp', 'last_collection_time', 'collection_duration', 'is_collecting_delayed', 'status_message')
    
    def collection_duration_display(self, obj):
        return f"{obj.collection_duration:.3f} seconds"
    collection_duration_display.short_description = "Collection Duration"
    
    def has_add_permission(self, request):
        # Prevent creating new status objects - we only want one
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deleting the status object
        return False
