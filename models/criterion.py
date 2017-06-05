from base import *

class Criterion(BaseModel):
    CRITERIA_TYPES = (
        ('static', 'Static'),
        ('dynamic', 'Dynamic'),
    )
    CRITERIA_SCOPE = (
        ('PM', 'Physical Machine'),
        ('FG', 'Forwarding Graph'),
    )

    name = models.CharField(max_length=50, unique=True)
    label = models.CharField(max_length=100, default="Criterion")
    type = models.CharField(max_length=50, choices=CRITERIA_TYPES)
    scope = models.CharField(max_length=50, choices=CRITERIA_SCOPE)
    weight = models.IntegerField(default=0)
    default_weight = models.IntegerField(default=1)
    formula = models.CharField(max_length=100,default="")

    def __unicode__(self):
        return self.name
