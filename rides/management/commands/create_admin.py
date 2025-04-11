from django.core.management.base import BaseCommand
from rides.models import User
from rest_framework.authtoken.models import Token

class Command(BaseCommand):
    help = 'Creates an admin user and returns their authentication token'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Admin username')
        parser.add_argument('--email', type=str, help='Admin email')
        parser.add_argument('--password', type=str, help='Admin password')

    def handle(self, *args, **options):
        username = options['username'] or 'admin'
        email = options['email'] or 'admin@example.com'
        password = options['password'] or 'admin123'

        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            self.stdout.write(self.style.WARNING(f'User {username} already exists'))
        else:
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                first_name='Admin',
                last_name='User',
                phone_number='555-000-0000',
                role='admin'
            )
            self.stdout.write(self.style.SUCCESS(f'Created admin user: {username}'))

        # Create or get the token
        token, created = Token.objects.get_or_create(user=user)
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created new token for {username}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Using existing token for {username}'))

        self.stdout.write(self.style.SUCCESS(f'Authentication token: {token.key}'))
        self.stdout.write(self.style.SUCCESS(f'Use this token in the Authorization header: Token {token.key}')) 