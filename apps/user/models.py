from django.db import models
from django.contrib.auth.models import PermissionsMixin, AbstractBaseUser, Permission
from django.contrib.auth.models import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=50, null=True)
    nick_name = models.CharField(max_length=50, null=True)

    is_staff = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False, blank=True)
    is_active = models.BooleanField(default=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True)
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

    @property
    def is_asset_admin(self):
        if self.is_superuser:
            return True
        try:
            return self.admin_profile.is_asset_admin
        except models.ObjectDoesNotExist:
            return False

    @property
    def is_finance_admin(self):
        if self.is_superuser:
            return True
        try:
            return self.admin_profile.is_finance_admin
        except models.ObjectDoesNotExist:
            return False


class AdminProfile(models.Model):
    user = models.OneToOneField(User, related_name="admin_profile", on_delete=models.CASCADE)
    is_asset_admin = models.BooleanField(default=False)
    is_finance_admin = models.BooleanField(default=False)


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


class CreatorBaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    creator = models.ForeignKey(
        User,
        related_name="%(app_label)s_%(class)s",
        on_delete=models.CASCADE)

    class Meta:
        abstract = True

    objects = models.Manager()