from django.db import models
from django.contrib.auth.models import User

class Challenge(models.Model):
    title = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    description = models.TextField()
    participants = models.ManyToManyField(User, related_name='challenges_participated', blank=True)

    def __str__(self):
        return self.title