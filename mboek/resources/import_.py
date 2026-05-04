"""Bank statement import resource."""

from __future__ import annotations

from pathlib import Path
from typing import IO

from mboek._parsers import parse_import_result
from mboek.models.export_import import ImportResult
from mboek.resources._base import BaseResource


class ImportResource(BaseResource):
    """Bank statement import and suggestion engine.

    Instantiated via :py:meth:`AdministratieScope.import_`.

    Supported file formats:

    - **MT940** (``.940``, ``.mt940``)
    - **CAMT.053** (``.xml``, filenames containing ``camt``)
    """

    def __init__(self, client, admin_id: int) -> None:
        super().__init__(client)
        self._admin_id = admin_id

    def upload(
        self,
        file: Path | IO[bytes],
        filename: str | None = None,
    ) -> ImportResult:
        """Upload a bank statement file and import its transactions.

        Transactions are imported as boekingen in the dagboek whose IBAN
        matches the statement's account number. Each boeking gets a temporary
        contra account (bankimportrekening 9990, "Nog te verwerken") until
        manually or automatically processed.

        Duplicate transactions (detected via import hash) are skipped.

        Args:
            file: Path to the bank statement file, or an open binary file
                object.
            filename: Override the filename sent to the server (used for
                format detection when ``file`` is a file object without a
                ``.name`` attribute).

        Returns:
            :py:class:`~mboek.models.export_import.ImportResult` with counts.
        """
        if isinstance(file, Path):
            fname = filename or file.name
            with file.open("rb") as fh:
                return parse_import_result(
                    self._post_multipart(
                        f"/api/administraties/{self._admin_id}/import",
                        files={"file": (fname, fh)},
                    )
                )
        raw_name = getattr(file, "name", "statement.940")
        fname = filename or Path(raw_name).name
        return parse_import_result(
            self._post_multipart(
                f"/api/administraties/{self._admin_id}/import",
                files={"file": (fname, file)},
            )
        )
