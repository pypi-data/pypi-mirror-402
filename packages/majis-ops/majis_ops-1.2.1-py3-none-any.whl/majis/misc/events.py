"""Events module."""

from operator import attrgetter

from planetary_coverage.events.event import (
    AbstractEvent,
    EventsDict,
    EventsList,
)


def flatten(events: tuple | list | EventsList | EventsDict | AbstractEvent) -> EventsList:
    """Flatten multi events object."""
    if isinstance(events, tuple | list | EventsList | EventsDict):
        return EventsList(
            sorted(
                [
                    ev
                    for event in events
                    for ev in (
                        flatten(event)
                        if isinstance(event, EventsList | EventsDict)
                        else [event]
                    )
                ],
                key=attrgetter('start'),
            )
        )

    if isinstance(events, AbstractEvent):
        return EventsList([events])

    raise TypeError(f'Invalid events type: `{type(events)}`')


def group(events: tuple | list | EventsList | EventsDict) -> EventsDict:
    """Group events by observation name."""
    if isinstance(events, tuple | list | EventsList):
        return EventsDict(events)

    if isinstance(events, EventsDict):
        return events

    raise TypeError(f'Invalid events type: `{type(events)}`')


def concatenate(
    *events: EventsList | EventsDict, flat: bool = False, overlap: bool = False
) -> EventsList | EventsDict:
    """Concatenate ITL events.

    Note
    ----
    By default, concatenated blocks must not overlap
    each other. This can be disable with `overlap=True`.

    """
    blocks = flatten(events)

    if blocks and not overlap:
        previous = blocks[0]
        for block in blocks[1:]:
            if block.start < previous.stop:
                raise ValueError(f'Overlap between `{previous}` and `{block}`')
            previous = block

    return blocks if flat else group(blocks)


def flatten_events(func):
    """Events flatten decorator.

    Mainly used as a prolog before saving files.

    """

    def wrapper(
        fout: ...,
        *events: EventsList | EventsDict,
        overlap: bool = False,
        **kwargs,
    ):
        """Concatenate events blocks before the calling the main function."""
        blocks = concatenate(*events, flat=True, overlap=overlap)
        return func(fout, *blocks, **kwargs)

    return wrapper
