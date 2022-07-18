from django.core.management.base import BaseCommand

from django.db.models import Q
from ...models import Cart
from django.contrib.sessions.models import Session


class Command(BaseCommand):
    help = "Delete all carts with expired sessions and no user_id"

    def handle(self, *args, **options):
        cart_length = clear_carts()
        self.stdout.write("Delete %d expired carts" % cart_length)


def clear_carts():
    session_key_query = Session.objects.only('session_key').all()
    carts = Cart.objects.filter(Q(user_id__isnull=True) & ~Q(session_key__in=session_key_query))
    cart_length = len(carts)
    carts.delete()
    return cart_length
