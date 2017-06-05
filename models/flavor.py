from base import *

class Flavor(BaseModel):
    label = models.CharField(max_length=50)
    minimum_cpu = models.FloatField()
    minimum_memory = models.FloatField()
    minimum_storage = models.FloatField()

    def __unicode__(self):
        return self.label
