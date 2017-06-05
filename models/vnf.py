from base import *
from flavor import *
from physical_machine import *
from forwarding_graph import *

class VNF(BaseModel):
    label = models.CharField(max_length=50)
    vm_cpu = models.FloatField()
    vm_memory = models.FloatField()
    vm_storage = models.FloatField()
    cpu_usage = models.FloatField()
    memory_usage = models.FloatField()
    storage_usage = models.FloatField()

    flavor = models.ForeignKey(Flavor)
    physical_machine = models.ForeignKey(PhysicalMachine)
    forwarding_graphs = models.ManyToManyField(ForwardingGraph)

    def __unicode__(self):
        return self.label
