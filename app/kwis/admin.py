from django.contrib import admin

# Giving admin module access to kwis models
from .models import Quiz, Team, Round, Answer

admin.site.register(Quiz)
admin.site.register(Team)
admin.site.register(Round)
admin.site.register(Answer)
