from tortoise import fields
from tortoise.models import Model


class PublishRecord(Model):
    id = fields.IntField(pk=True)
    filename = fields.CharField(max_length=500)
    scheduled = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    published_at = fields.DatetimeField(null=True)
    blog_id = fields.CharField(max_length=100, null=True)
    workspace = fields.ForeignKeyField("models.Workspace", related_name="publish_records")
    status = fields.CharField(max_length=20, default="pending")  # pending, scheduled, publishing, published, failed
    error_message = fields.TextField(null=True)
    post_id = fields.CharField(max_length=100, null=True)
    post_url = fields.CharField(max_length=500, null=True)
    is_converted = fields.BooleanField(default=False)
    
    class Meta:
        table = "publish_records"
        
    def __str__(self):
        return f"{self.filename} - {self.status}"