from base import *
from conflict import *

class Descriptor(BaseModel):
    label = models.CharField(max_length=50)
    sla = models.FloatField()
    conflicts = models.ManyToManyField(Conflict)

    def __unicode__(self):
        return self.label
