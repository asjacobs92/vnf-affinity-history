from base import *
from vnf import *

class Conflict(BaseModel):
    nfv_a = models.ForeignKey(VNF, related_name="vnf_a")
    nfv_b = models.ForeignKey(VNF, related_name="vnf_b")

    def __unicode__(self):
        return self.nfv_a.label + " X " + self.nfv_b.label
