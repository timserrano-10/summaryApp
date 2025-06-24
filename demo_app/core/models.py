from django.db import models

# structure of database, controls how django interacts with each document
class Document(models.Model):
    title = models.CharField(max_length=255)
    uploaded_file = models.FileField(upload_to='uploads/', blank=True, null=True)
    raw_text = models.TextField(blank=True, null=True)
    summary = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
