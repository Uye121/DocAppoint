from django.db import models
from django.utils.translation import gettext_lazy as _

from .users import User

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_messages")
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-sent_at']
    
    def clean(self):
        super().clean()
        
        if not self.content.strip():
            raise ValueError("Cannot send message without content")    
    
    def __str__(self):
        return f"Message from {self.sender} to {self.recipient}"