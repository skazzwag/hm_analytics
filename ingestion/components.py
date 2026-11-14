"""Custom Dagster components for the ingestion project."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

from dagster_dlt import DltLoadCollectionComponent

if TYPE_CHECKING:
    import dagster as dg
    from dagster_dlt import DagsterDltResource

WRITE_DISPOSITION_TAG = "dlt/write_disposition"
VALID_WRITE_DISPOSITIONS = frozenset({"replace", "append", "merge"})


class RefreshableDltLoadCollectionComponent(DltLoadCollectionComponent):
    """``DltLoadCollectionComponent`` with a run-level write disposition override.

    When the ``dlt/write_disposition`` run tag is present on the run, its value
    is forwarded to ``DagsterDltResource.run`` as ``write_disposition``. Without
    the tag, execution falls back to the dispositions hardcoded in each dlt
    source.
    """

    def execute(
        self,
        context: dg.AssetExecutionContext,
        dlt_pipeline_resource: DagsterDltResource,
    ) -> Iterator:
        """Run the dlt pipeline, honoring a write disposition run tag when set.

        Parameters
        ----------
        context : dg.AssetExecutionContext
            The asset execution context provided by Dagster.
        dlt_pipeline_resource : DagsterDltResource
            The resource used to run the dlt pipeline.

        Yields
        ------
        Iterator
            Events from the dlt pipeline execution.

        Raises
        ------
        ValueError
            If the write disposition run tag carries an unsupported value.
        """
        write_disposition = context.run_tags.get(WRITE_DISPOSITION_TAG)
        if write_disposition is None:
            yield from super().execute(context, dlt_pipeline_resource)
            return
        if write_disposition not in VALID_WRITE_DISPOSITIONS:
            raise ValueError(
                f"Unsupported {WRITE_DISPOSITION_TAG} run tag value "
                f"{write_disposition!r}; expected one of "
                f"{sorted(VALID_WRITE_DISPOSITIONS)}."
            )
        yield from dlt_pipeline_resource.run(
            context=context,
            write_disposition=write_disposition,
        )
