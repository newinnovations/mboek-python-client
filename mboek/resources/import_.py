"""Bank statement import resource."""

from __future__ import annotations

from pathlib import Path
from typing import IO

from mboek._parsers import parse_import_result
from mboek.models.export_import import ImportResult
from mboek.resources._base import BaseResource
from mboek.resources.export_import import _bool_query


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
        allow_duplicates: bool | None = None,
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
                usable ``.name`` attribute). Required for unnamed in-memory
                uploads because the backend uses the filename to detect the
                statement format.
            allow_duplicates: Set ``True`` to re-import transactions already
                present, ``False`` to send an explicit ``false`` value, or
                ``None`` to omit the form field and use the backend default.

        Returns:
            :py:class:`~mboek.models.export_import.ImportResult` with detailed
            import counts and warnings.
        """
        allow_duplicates_value = _bool_query(allow_duplicates)
        form_data = (
            {"allow_duplicates": allow_duplicates_value}
            if allow_duplicates_value is not None
            else None
        )
        if isinstance(file, Path):
            fname = filename or file.name
            with file.open("rb") as fh:
                return parse_import_result(
                    self._post_multipart(
                        f"/api/administraties/{self._admin_id}/import",
                        files={"file": (fname, fh)},
                        data=form_data,
                    )
                )
        fname = filename
        if fname is None:
            raw_name = getattr(file, "name", None)
            if isinstance(raw_name, str):
                fname = Path(raw_name).name or None
        if fname is None:
            raise ValueError(
                "filename is required when uploading a file object without a usable .name"
            )
        return parse_import_result(
            self._post_multipart(
                f"/api/administraties/{self._admin_id}/import",
                files={"file": (fname, file)},
                data=form_data,
            )
        )
