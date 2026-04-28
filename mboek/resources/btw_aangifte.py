"""BTW-aangifte resource."""

from __future__ import annotations

from mboek._parsers import parse_btw_aangifte
from mboek.models.btw_aangifte import BtwAangifte
from mboek.resources._base import BaseResource


class BtwAangifteResource(BaseResource):
    """Quarterly BTW-aangifte (VAT return) workflow.

    Instantiated via :py:meth:`BoekjaarScope.btw_aangifte`.

    **Workflow:**

    1. :py:meth:`berekenen` — calculate the quarter (creates a *concept* aangifte).
    2. Review the returned :py:class:`~mboek.models.btw_aangifte.BtwAangifte`.
    3. :py:meth:`vastleggen` — lock the aangifte and create the balancing
       memoriaal boeking.
    4. To redo: :py:meth:`delete` the concept and :py:meth:`berekenen` again.
    """

    def __init__(self, client, admin_id: int, boekjaar_id: int) -> None:
        super().__init__(client)
        self._admin_id = admin_id
        self._boekjaar_id = boekjaar_id

    def list(self) -> list[BtwAangifte]:
        """Return all BTW-aangiften for the boekjaar.

        Returns:
            List of aangiften (concept and definitief).
        """
        return [
            parse_btw_aangifte(d)
            for d in self._get(
                f"/api/administraties/{self._admin_id}/btw-aangiften",
                params={"boekjaar_id": self._boekjaar_id},
            )
        ]

    def berekenen(self, kwartaal: int) -> BtwAangifte:
        """Calculate (or recalculate) the BTW-aangifte for a quarter.

        Aggregates all boekingsregels with BTW codes in the specified quarter
        and produces a concept aangifte with a full per-rubriek breakdown.

        If a concept aangifte already exists for this quarter it is
        **deleted and recalculated** (a new ID is returned).

        Args:
            kwartaal: Quarter number (1–4).

        Returns:
            New concept :py:class:`~mboek.models.btw_aangifte.BtwAangifte`.
        """
        return parse_btw_aangifte(
            self._post(
                f"/api/administraties/{self._admin_id}/btw-aangiften/berekenen",
                json={"boekjaar_id": self._boekjaar_id, "kwartaal": kwartaal},
            )
        )

    def vastleggen(self, aangifte_id: int) -> BtwAangifte:
        """Lock a concept aangifte and create the balancing memoriaal boeking.

        Transitions the aangifte from ``concept`` to ``definitief``.  Also
        creates a memoriaal boeking that records the net BTW position (r5g).

        The boekjaar must be **gesloten** before calling this.

        Args:
            aangifte_id: BTW-aangifte ID.

        Returns:
            The updated definitief aangifte.
        """
        return parse_btw_aangifte(
            self._post(
                f"/api/administraties/{self._admin_id}/btw-aangiften/{aangifte_id}/vastleggen"
            )
        )

    def delete(self, aangifte_id: int) -> None:
        """Delete a concept BTW-aangifte (and its associated boeking).

        Only concept aangiften can be deleted.

        Args:
            aangifte_id: BTW-aangifte ID.
        """
        self._delete(
            f"/api/administraties/{self._admin_id}/btw-aangiften/{aangifte_id}"
        )
