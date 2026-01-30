from tortoise import fields
from tortoise.models import Model


class Setting(Model):
    key = fields.CharField(max_length=100, pk=True)
    value = fields.TextField()
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "settings"
        
    def __str__(self):
        return f"{self.key}: {self.value}"