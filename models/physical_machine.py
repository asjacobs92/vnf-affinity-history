from base import *

class PhysicalMachine(BaseModel):
    label = models.CharField(max_length=50)
    cpu = models.FloatField()
    memory = models.FloatField()
    storage = models.FloatField()

    class Meta():
        db_table = 'amnesia_physical_machine'

    def __unicode__(self):
        return self.label
