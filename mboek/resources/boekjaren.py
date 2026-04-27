"""Boekjaren resource."""

from __future__ import annotations

from mboek._parsers import parse_boekjaar
from mboek.models.boekjaren import Boekjaar, CreateBoekjaarInput, UpdateBoekjaarInput
from mboek.resources._base import BaseResource


class BoekjarenResource(BaseResource):
    """CRUD + lifecycle operations for boekjaren (fiscal years).

    Instantiated via :py:meth:`AdministratieScope.boekjaren`.
    """

    def __init__(self, client, admin_id: int) -> None:
        super().__init__(client)
        self._admin_id = admin_id

    def list(self) -> list[Boekjaar]:
        """Return all boekjaren for the administratie.

        Returns:
            List sorted by start date ascending.
        """
        return [
            parse_boekjaar(d)
            for d in self._get(f"/api/administraties/{self._admin_id}/boekjaren")
        ]

    def get(self, id: int) -> Boekjaar:
        """Return a single boekjaar.

        Args:
            id: Boekjaar ID.
        """
        return parse_boekjaar(self._get(f"/api/administraties/{self._admin_id}/boekjaren/{id}"))

    def create(self, input: CreateBoekjaarInput) -> Boekjaar:
        """Create a new boekjaar.

        New boekjaren start with status ``open``.

        Args:
            input: Name and date range.
        """
        return parse_boekjaar(
            self._post(f"/api/administraties/{self._admin_id}/boekjaren", json=input.to_dict())
        )

    def update(self, id: int, input: UpdateBoekjaarInput) -> Boekjaar:
        """Partially update a boekjaar's name or dates.

        To change status use :py:meth:`afsluiten` or :py:meth:`heropenen`.

        Args:
            id: Boekjaar ID.
            input: Fields to update.
        """
        return parse_boekjaar(
            self._patch(
                f"/api/administraties/{self._admin_id}/boekjaren/{id}", json=input.to_dict()
            )
        )

    def delete(self, id: int) -> None:
        """Permanently delete a boekjaar and all its boekingen.

        .. warning::
            Irreversible.

        Args:
            id: Boekjaar ID.
        """
        self._delete(f"/api/administraties/{self._admin_id}/boekjaren/{id}")

    def afsluiten(self, id: int) -> Boekjaar:
        """Close a boekjaar (transition ``open`` → ``gesloten``).

        A closed boekjaar no longer accepts new boekingen. This is a
        prerequisite for finalising a BTW-aangifte via ``vastleggen``.

        Args:
            id: Boekjaar ID.

        Raises:
            :py:class:`~mboek._exceptions.ConflictError`: Already closed.
        """
        return parse_boekjaar(
            self._post(f"/api/administraties/{self._admin_id}/boekjaren/{id}/afsluiten")
        )

    def heropenen(self, id: int) -> Boekjaar:
        """Reopen a gesloten boekjaar (transition ``gesloten`` → ``open``).

        Blocked if there are any definitieve BTW-aangiften for this boekjaar.

        Args:
            id: Boekjaar ID.

        Raises:
            :py:class:`~mboek._exceptions.ConflictError`: Not closed or has
                definitieve BTW-aangiften.
        """
        return parse_boekjaar(
            self._post(f"/api/administraties/{self._admin_id}/boekjaren/{id}/heropenen")
        )

    def set_huidig(self, id: int) -> Boekjaar:
        """Set a boekjaar as the current (default) boekjaar of its administratie.

        The current boekjaar is used as a default in endpoints that accept an
        optional ``boekjaar_id`` query parameter (e.g. dagboek werkstatus).

        Args:
            id: Boekjaar ID to set as current.
        """
        return parse_boekjaar(
            self._post(f"/api/administraties/{self._admin_id}/boekjaren/{id}/set-huidig")
        )

    def find_by_naam(self, naam: str) -> Boekjaar | None:
        """Find a boekjaar by exact name.

        Calls :py:meth:`list` and returns the first match, or ``None``.

        Args:
            naam: Exact boekjaar name to search for (e.g. ``"2024"``).

        Returns:
            The matching :py:class:`~mboek.models.boekjaren.Boekjaar`,
            or ``None`` if not found.
        """
        return next((b for b in self.list() if b.naam == naam), None)
