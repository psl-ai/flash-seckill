from enum import Enum

class ActivityStatus(str, Enum):
    DRAFT = 'draft'; PUBLISHED = 'published'; REGISTRATION_OPEN = 'registration_open'; SOLD_OUT = 'sold_out'; ENDED = 'ended'; CANCELED = 'canceled'

_TRANSITIONS = {
    (ActivityStatus.DRAFT, 'publish'): ActivityStatus.PUBLISHED,
    (ActivityStatus.PUBLISHED, 'open'): ActivityStatus.REGISTRATION_OPEN,
    (ActivityStatus.REGISTRATION_OPEN, 'sold_out'): ActivityStatus.SOLD_OUT,
    (ActivityStatus.REGISTRATION_OPEN, 'end'): ActivityStatus.ENDED,
    (ActivityStatus.PUBLISHED, 'cancel'): ActivityStatus.CANCELED,
    (ActivityStatus.REGISTRATION_OPEN, 'cancel'): ActivityStatus.CANCELED,
}
def transition_status(current: ActivityStatus, action: str) -> ActivityStatus:
    try: return _TRANSITIONS[(current, action)]
    except KeyError: raise ValueError(f'invalid transition {current.value}->{action}')
