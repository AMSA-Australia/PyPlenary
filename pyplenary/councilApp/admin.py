from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(Institution)
admin.site.register(Delegate)
admin.site.register(Poll)
admin.site.register(Vote)
admin.site.register(Proxy)
admin.site.register(ResetToken)
admin.site.register(PendingRego)
admin.site.register(Speaker)
