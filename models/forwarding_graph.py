from base import *

class Flow(BaseModel):
    source = models.ForeignKey("VNF", related_name="source_vnf")
    destination = models.ForeignKey("VNF", related_name="destination_vnf")
    latency = models.FloatField()
    traffic = models.FloatField()
    bandwidth_usage = models.FloatField()
    packet_loss = models.FloatField()

    def __unicode__(self):
        return self.src.label + " -> " + self.dst.label

class ForwardingGraph(BaseModel):
    label = models.CharField(max_length=50)
    flows = models.ManyToManyField(Flow)

    class Meta:
        db_table = "amnesia_forwarding_graph"

    def __unicode__(self):
        return self.label
