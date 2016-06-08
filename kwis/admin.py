from django.contrib import admin

# Giving admin module access to kwis models
from .models import QTeam, QRound, QAnswer

admin.site.register(QTeam)
admin.site.register(QRound)
admin.site.register(QAnswer)
