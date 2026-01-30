from tortoise import fields
from tortoise.models import Model


class Workspace(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)
    folder_path = fields.CharField(max_length=500)
    blog_id = fields.CharField(max_length=100, null=True)
    publish_interval = fields.CharField(max_length=50, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    publish_records: fields.ReverseRelation["PublishRecord"]
    
    class Meta:
        table = "workspaces"
        
    def __str__(self):
        return self.name