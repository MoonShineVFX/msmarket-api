from django.db import models
from django.contrib.auth.models import PermissionsMixin, AbstractBaseUser
from django.contrib.auth.models import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=50, null=True)
    nick_name = models.CharField(max_length=50, null=True)
    is_deleted = models.BooleanField(default=False, blank=True)
    is_active = models.BooleanField(default=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    is_anonymous = False
    is_authenticated = True

    def __unicode__(self):
        return self.email

    @property
    def username(self):
        return self.email


class EditorBaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True)
    creator = models.ForeignKey(
        User,
        related_name="%(app_label)s_%(class)s_creation",
        on_delete=models.CASCADE)
    updater = models.ForeignKey(
        User,
        related_name="%(app_label)s_%(class)s_update",
        on_delete=models.CASCADE,
        null=True)

    class Meta:
        abstract = True

    objects = models.Manager()


class Customer(AbstractBaseUser):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=50, null=True)

    is_deleted = models.BooleanField(default=False, blank=True)
    is_active = models.BooleanField(default=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'