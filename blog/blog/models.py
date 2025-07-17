from django.db import models
from django.contrib.auth.models import User


class Blog(models.Model):
    """ Blog model """
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=150)
    text = models.TextField()
    published_date = models.DateTimeField(auto_now=True)
    updated_date = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='blog_images/', blank=True, null=True)  # New field for image

    def __str__(self):
        return self.title
    
