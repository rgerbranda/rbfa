from datetime import datetime


def is_match_ended(
    state: str | None,
    endtime: datetime,
    now: datetime,
) -> bool:
    """Check whether a match is considered ended or will not be played."""
    return (
        state in ('finished', 'postponed', 'generalForfeit', 'forfeitByOneTeam')
        or (state == 'planned' and now >= endtime)
    )

def is_match_in_progress(
    state: str | None,
    starttime: datetime,
    endtime: datetime,
    now: datetime,
) -> bool:
    """Check whether a match has started and has not ended."""
    return (
        starttime <= now
        and not is_match_ended(state, endtime, now)
    )