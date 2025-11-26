from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
import os


class Command(BaseCommand):
    help = 'Initialize database with migrations - safe for production deployment'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force migration even if tables exist',
        )

    def handle(self, *args, **options):
        self.stdout.write("🗄️ Starting database initialization...")
        
        # Check if we're on Render
        is_render = os.environ.get('RENDER') == 'true'
        
        try:
            # Check if auth_user table exists
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public'
                        AND table_name = 'auth_user'
                    );
                """)
                table_exists = cursor.fetchone()[0]
            
            if table_exists and not options['force']:
                self.stdout.write(
                    self.style.SUCCESS("✅ Database already initialized!")
                )
                return
                
        except Exception as e:
            self.stdout.write(f"⚠️ Could not check table existence: {e}")
            self.stdout.write("Proceeding with migrations...")
        
        # Run migrations
        self.stdout.write("🔄 Running database migrations...")
        try:
            call_command('migrate', verbosity=2, interactive=False)
            self.stdout.write(
                self.style.SUCCESS("✅ Database migrations completed successfully!")
            )
            
            # Create superuser if on Render and no users exist
            if is_render:
                self.stdout.write("👤 Checking for admin user...")
                try:
                    from django.contrib.auth.models import User
                    if not User.objects.filter(is_superuser=True).exists():
                        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@procure-to-pay.com')
                        admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
                        
                        User.objects.create_superuser(
                            username='admin',
                            email=admin_email,
                            password=admin_password
                        )
                        self.stdout.write(
                            self.style.SUCCESS(f"✅ Admin user created: {admin_email}")
                        )
                        self.stdout.write(
                            self.style.WARNING("⚠️ Please change the admin password!")
                        )
                    else:
                        self.stdout.write("✅ Admin user already exists")
                        
                except Exception as e:
                    self.stdout.write(f"❌ Could not create admin user: {e}")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Migration failed: {e}")
            )
            raise
        
        self.stdout.write("🎉 Database initialization completed!")