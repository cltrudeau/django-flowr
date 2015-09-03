from django.db import models

from flowr.models import BaseNodeData

# ============================================================================
# Models used by tests

class Label(BaseNodeData):
    name = models.CharField(max_length=5)

    def __str__(self):
        return 'Label(id=%s %s)' % (self.id, self.name)
