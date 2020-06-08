from django.db import models

class Listings(models.Model):
    id = models.AutoField(primary_key=True)
    game = models.TextField()
    platform = models.TextField()
    price = models.TextField()
    seller = models.TextField()

    def __str__(self):
        return self.id

    class Meta:
        managed = False
        db_table = 'listings'

class Users(models.Model):
    username = models.TextField(primary_key=True)
    password = models.TextField()

    def __str__(self):
        return self.username

    class Meta:
        managed = False
        db_table = 'users'
