from django.contrib import admin

# Giving admin module access to kwis models
from .models import Team, Round, Answer

admin.site.register(Team)
admin.site.register(Round)
admin.site.register(Answer)
