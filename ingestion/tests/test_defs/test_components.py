from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from ingestion.components import (
    VALID_WRITE_DISPOSITIONS,
    WRITE_DISPOSITION_TAG,
    RefreshableDltLoadCollectionComponent,
)


@dataclass
class StubContext:
    """Minimal asset execution context stub exposing only run tags."""

    run_tags: dict[str, str]


@dataclass
class RecordedRunCall:
    """A recorded ``run`` invocation captured from the component under test."""

    context: StubContext
    write_disposition: str | None = None


@dataclass
class RecordingDltResource:
    """Minimal dlt resource stub recording ``run`` calls instead of running."""

    calls: list[RecordedRunCall] = field(default_factory=list)

    def run(self, context: StubContext, **kwargs: str) -> list[str]:
        """Record the call and return a single fake event."""

        self.calls.append(
            RecordedRunCall(
                context=context,
                write_disposition=kwargs.get("write_disposition"),
            )
        )
        return ["event"]


def _execute(run_tags: dict[str, str]) -> RecordingDltResource:
    """Execute the component with the given run tags and return the resource."""

    component = RefreshableDltLoadCollectionComponent(loads=[])
    resource = RecordingDltResource()
    list(component.execute(StubContext(run_tags=run_tags), resource))
    return resource


def test_execute_without_tag_uses_resource_defaults() -> None:
    """Without the run tag, no write_disposition kwarg is forwarded."""

    resource = _execute({})

    assert len(resource.calls) == 1
    assert resource.calls[0].write_disposition is None


def test_execute_with_tag_forwards_write_disposition() -> None:
    """With the run tag, the value is forwarded as write_disposition."""

    for value in sorted(VALID_WRITE_DISPOSITIONS):
        resource = _execute({WRITE_DISPOSITION_TAG: value})

        assert len(resource.calls) == 1
        assert resource.calls[0].write_disposition == value


def test_execute_with_invalid_tag_value_fails_fast() -> None:
    """An unsupported tag value raises before any dlt run is started."""

    with pytest.raises(ValueError, match=WRITE_DISPOSITION_TAG):
        _execute({WRITE_DISPOSITION_TAG: "drop"})
