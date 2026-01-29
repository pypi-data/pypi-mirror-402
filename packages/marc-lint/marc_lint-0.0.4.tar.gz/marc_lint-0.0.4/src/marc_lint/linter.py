"""Python port of the core behavior of `MARC::Lint`.

This is intended as an educational translation so you can see
what the original Perl code is doing, in a more familiar Python
syntax. It assumes `pymarc` records and fields.

Original MARC::Lint Perl module:
    Copyright (C) 2001-2011 Bryan Baldus, Ed Summers, and Dan Lester
    Available under the Perl License (Artistic + GPL)
    https://metacpan.org/dist/MARC-Lint

Python port:
    Copyright (C) 2025 Jacob Collins
    Available under the MIT License
"""

from __future__ import annotations

from typing import Any, Dict, List, Callable, Optional
import re

from pymarc import Record, Field
from stdnum import isbn as stdnum_isbn
from stdnum import issn as stdnum_issn

from .field_rules import RuleGenerator
from .code_data import (
    GEOG_AREA_CODES,
    OBSOLETE_GEOG_AREA_CODES,
    LANGUAGE_CODES,
    OBSOLETE_LANGUAGE_CODES,
    COUNTRY_CODES,
    OBSOLETE_COUNTRY_CODES,
    LEADER_RECORD_STATUS,
    LEADER_TYPE_OF_RECORD,
    LEADER_BIBLIOGRAPHIC_LEVEL,
    LEADER_ENCODING_LEVEL,
    LEADER_TYPE_OF_CONTROL,
    LEADER_CHARACTER_CODING_SCHEME,
    LEADER_DESCRIPTIVE_CATALOGING_FORM,
    LEADER_MULTIPART_RESOURCE_RECORD_LEVEL,
    TYPE_OF_DATE,
    REQUIRED_FIELDS,
)
from .warning import MarcWarning


class RecordResult:
    """Result of linting a single MARC record.

    Attributes:
        record_id: Identifier for the record (from 001 field or index)
        warnings: List of MarcWarning objects for this record
        record: Reference to the original Record object
    """

    def __init__(
        self,
        record_id: str,
        warnings: List[MarcWarning],
        record: Optional[Record] = None,
    ) -> None:
        self.record_id = record_id
        self.warnings = warnings
        self.record = record

    @property
    def is_valid(self) -> bool:
        """Return True if no warnings were generated."""
        return len(self.warnings) == 0

    def __repr__(self) -> str:
        return (
            f"RecordResult(record_id={self.record_id!r}, warnings={len(self.warnings)})"
        )


class MarcLint:
    """Rough Python equivalent of `MARC::Lint`.

    Main entrypoint is `check_record(record)`, after which you can
    inspect `warnings()` for any messages. For batch processing,
    use `check_records(records)` to validate multiple records at once.
    """

    def __init__(self) -> None:
        self._warnings: list[MarcWarning] = []
        self._rules = RuleGenerator().rules
        self._current_record_id: Optional[str] = None
        self._current_record: Optional[Record] = None
        self._field_positions: Dict[
            str, int
        ] = {}  # Track positions of repeating fields

    # -------- warning handling --------

    def warnings(self) -> List[str]:
        """Return warnings accumulated by the last `check_record` call as strings.

        For backward compatibility, this returns strings.
        Use warnings_structured() for structured warning objects.
        """
        return [str(w) for w in self._warnings]

    def warnings_structured(self) -> List[MarcWarning]:
        """Return warnings as structured MarcWarning objects."""
        return list(self._warnings)

    def clear_warnings(self) -> None:
        self._warnings = []
        self._field_positions = {}
        self._current_record = None

    def warn(
        self,
        field: str,
        message: str,
        subfield: Optional[str] = None,
        position: Optional[int] = None,
        record_id: Optional[str] = None,
    ) -> None:
        """Add a structured warning.

        Args:
            field: The MARC field tag (e.g., "020", "245", "LDR" for leader)
            message: The error message
            subfield: Optional subfield code (e.g., "a", "z")
            position: Optional position for repeating fields (0-based index)
            record_id: Optional record identifier (defaults to current record if set)
        """
        # Use provided record_id or fall back to current record context
        rid = record_id if record_id is not None else self._current_record_id
        self._warnings.append(
            MarcWarning(
                field=field,
                message=message,
                subfield=subfield,
                position=position,
                record_id=rid,
            )
        )

    # -------- main record check --------

    def check_record(
        self, marc: Record, record_id: Optional[str] = None
    ) -> List[MarcWarning]:
        """Run lint checks on a `pymarc.Record`.

        Mirrors the Perl `check_record` method: validates leader, 1XX count,
        presence of 245, field repeatability, indicators, subfields,
        control-field rules, and then any tag-specific `check_xxx`
        method that exists on this class.

        Args:
            marc: A pymarc.Record object to validate
            record_id: Optional identifier for the record. If not provided,
                       will attempt to use the 001 field value.

        Returns:
            List of MarcWarning objects for this record.
        """

        self.clear_warnings()

        if not isinstance(marc, Record):
            self.warn("", "Must pass a MARC::Record-like object to check_record")
            return self._warnings

        # Set current record ID for context
        if record_id:
            self._current_record_id = record_id
        else:
            # Try to get record ID from 001 field
            field_001 = marc.get_fields("001")
            if field_001 and hasattr(field_001[0], "data"):
                self._current_record_id = field_001[0].data
            else:
                self._current_record_id = None

        # Store current record for use by field checkers
        self._current_record = marc

        # Check leader first
        self.check_leader(marc)

        one_xx = [f for f in marc.get_fields() if f.tag.startswith("1")]
        if len(one_xx) > 1:
            self.warn(
                "1XX",
                f"Only one 1XX tag is allowed, but I found {len(one_xx)} of them.",
            )
        # Check for presence of 245
        field_tags = {f.tag for f in marc.fields}
        missing = REQUIRED_FIELDS - field_tags
        if missing:
            for tag in sorted(missing):
                self.warn(tag, f"No {tag} tag.")

        field_seen: Dict[str, int] = {}
        rules = self._rules
        for field in marc.get_fields():
            tagno = field.tag

            tagrules: dict[str, Any] | None = None

            # Track field position for this tag
            key = f"880.{tagno}" if tagno == "880" else tagno
            position = field_seen.get(key, 0)
            self._field_positions[tagno] = position

            if tagno == "880":
                sub6 = field.get_subfields("6")
                if not sub6:  # no subfield 6 in 880 field
                    self.warn("880", "No subfield 6.", position=position)
                    field_seen[key] = position + 1
                    continue
                # Check the referenced field
                tagno = sub6[0][:3]
                tagrules = rules.get(tagno)
                if not tagrules:
                    field_seen[key] = position + 1
                    continue
                if not tagrules.get("repeatable") and position > 0:
                    self.warn(tagno, "Field is not repeatable.", position=position)
            else:
                tagrules = rules.get(tagno)
                if not tagrules:
                    field_seen[key] = position + 1
                    continue
                if not tagrules.get("repeatable") and position > 0:
                    self.warn(tagno, "Field is not repeatable.", position=position)

            try:
                tag_int = int(tagno)
            except ValueError:
                tag_int = 10

            if tag_int >= 10:
                self.check_indicators(tagno, field, tagrules, position)
                self.check_subfields(tagno, field, tagrules, position)
            else:
                # control fields (<010): no subfield delimiters allowed
                if "\x1f" in (field.data or ""):
                    self.warn(
                        tagno,
                        "Subfields are not allowed in fields lower than 010",
                        position=position,
                    )

            # call tag-specific checker method if it exists
            checker_name = f"check_{tagno}"
            checker: Callable[[Field, int], None] | None = getattr(
                self, checker_name, None
            )
            if callable(checker):
                checker(field, position)

            field_seen[key] = position + 1

        # Reset current record context
        self._current_record_id = None
        self._current_record = None

        return self._warnings

    def check_records(
        self, records: List[Record], use_index_as_id: bool = False
    ) -> List[RecordResult]:
        """Run lint checks on multiple MARC records.

        Args:
            records: List of pymarc.Record objects to validate
            use_index_as_id: If True, use the 0-based index as record_id when
                            001 field is not available. If False, record_id
                            may be None for records without 001.

        Returns:
            List of RecordResult objects, one for each input record.
        """
        results: List[RecordResult] = []

        for idx, record in enumerate(records):
            # Determine record ID
            record_id: Optional[str] = None
            field_001 = record.get_fields("001") if isinstance(record, Record) else []
            if field_001 and hasattr(field_001[0], "data"):
                record_id = field_001[0].data
            elif use_index_as_id:
                record_id = str(idx)

            # Check the record
            warnings = self.check_record(record, record_id=record_id)

            # Create result object
            result = RecordResult(
                record_id=record_id or str(idx),
                warnings=list(warnings),  # Copy the list
                record=record,
            )
            results.append(result)

        return results

    # # -------- General checks --------

    def check_leader(self, marc: Record) -> None:
        """Validate the MARC record leader.

        Checks positions:
        - 05: Record status
        - 06: Type of record
        - 07: Bibliographic level
        - 08: Type of control
        - 09: Character coding scheme
        - 17: Encoding level
        - 18: Descriptive cataloging form
        - 19: Multipart resource record level
        """
        # Handle both string and Leader object (pymarc 4.x vs 5.x)
        raw_leader = marc.leader if marc.leader else ""
        leader = str(raw_leader) if raw_leader else ""

        if len(leader) < 24:
            self.warn(
                "LDR",
                f"Leader must be 24 characters, found {len(leader)}.",
            )
            return

        # Position 05: Record status
        if leader[5] not in LEADER_RECORD_STATUS:
            self.warn(
                "LDR",
                f"Invalid record status '{leader[5]}' at position 05.",
            )

        # Position 06: Type of record
        if leader[6] not in LEADER_TYPE_OF_RECORD:
            self.warn(
                "LDR",
                f"Invalid type of record '{leader[6]}' at position 06.",
            )

        # Position 07: Bibliographic level
        if leader[7] not in LEADER_BIBLIOGRAPHIC_LEVEL:
            self.warn(
                "LDR",
                f"Invalid bibliographic level '{leader[7]}' at position 07.",
            )

        # Position 08: Type of control
        if leader[8] not in LEADER_TYPE_OF_CONTROL:
            self.warn(
                "LDR",
                f"Invalid type of control '{leader[8]}' at position 08.",
            )

        # Position 09: Character coding scheme
        if leader[9] not in LEADER_CHARACTER_CODING_SCHEME:
            self.warn(
                "LDR",
                f"Invalid character coding scheme '{leader[9]}' at position 09.",
            )

        # Position 17: Encoding level
        if leader[17] not in LEADER_ENCODING_LEVEL:
            self.warn(
                "LDR",
                f"Invalid encoding level '{leader[17]}' at position 17.",
            )

        # Position 18: Descriptive cataloging form
        if leader[18] not in LEADER_DESCRIPTIVE_CATALOGING_FORM:
            self.warn(
                "LDR",
                f"Invalid descriptive cataloging form '{leader[18]}' at position 18.",
            )

        # Position 19: Multipart resource record level
        if leader[19] not in LEADER_MULTIPART_RESOURCE_RECORD_LEVEL:
            self.warn(
                "LDR",
                f"Invalid multipart resource record level '{leader[19]}' at position 19.",
            )

    def check_indicators(
        self, tagno: str, field: Field, tagrules: dict[str, Any], position: int = 0
    ) -> None:
        """General indicator checks for any field."""
        # indicator checks (pymarc exposes them via `indicators` list)
        indicator_rules = tagrules.get("indicators", {})
        for ind_index in (1, 2):
            indicator_rule = indicator_rules.get(f"ind{ind_index}")
            # ind_index is 1- or 2-based; convert to 0-based index
            ind_value = " "
            # pymarc represents missing indicators as ' ' (space) or None
            if hasattr(field, "indicators") and len(field.indicators) >= ind_index:
                ind_value = field.indicators[ind_index - 1] or " "
            regex = indicator_rule.get("regex")
            desc = indicator_rule.get("description")
            if regex is None:
                continue
            pattern = re.compile(regex) if isinstance(regex, str) else regex
            if not pattern.match(ind_value):
                self.warn(
                    tagno,
                    f'Indicator {ind_index} must be {desc} but it\'s "{ind_value}"',
                    position=position if position > 0 else None,
                )

    def check_subfields(
        self, tagno: str, field: Field, tagrules: dict[str, Any], position: int = 0
    ) -> None:
        """General subfield checks for any field."""
        subpairs = self._get_subfield_pairs(field)
        # Check subfields against repeat rules
        sub_seen: dict[str, int] = {}
        subfields_rules = tagrules.get("subfields", {})
        for code, data in subpairs:
            rule = subfields_rules.get(code)
            # rule = tagrules.get(code)
            if rule is None:
                self.warn(
                    tagno,
                    f"Subfield _{code} is not allowed.",
                    position=position if position > 0 else None,
                )
            elif not rule.get("repeatable") and sub_seen.get(code):
                self.warn(
                    tagno,
                    f"Subfield _{code} is not repeatable.",
                    position=position if position > 0 else None,
                )

            if any(ch in data for ch in ("\t", "\r", "\n")):
                self.warn(
                    tagno,
                    f"Subfield _{code} has an invalid control character",
                    subfield=code,
                    position=position if position > 0 else None,
                )

            sub_seen[code] = sub_seen.get(code, 0) + 1

    # -------- specific tag checks (subset) --------

    def check_020(self, field: Field, position: int = 0) -> None:
        """Validate ISBNs in 020$a and 020$z.

        Uses python-stdnum library for standard ISBN validation.
        """

        subpairs = self._get_subfield_pairs(field)
        pos = position if position > 0 else None

        for code, data in subpairs:
            # Extract ISBN number (remove hyphens and extract digits/X)
            isbnno = data.replace("-", "")
            m = re.search(r"\D*(\d{9,12}[X\d])\b", isbnno)
            isbnno = m.group(1) if m else ""

            if code == "a":
                if isbnno and not data.startswith(isbnno):
                    self.warn(
                        "020",
                        "may have invalid characters.",
                        subfield="a",
                        position=pos,
                    )

                if "(" in data and not re.search(r"[X0-9] \(", data):
                    self.warn(
                        "020",
                        f"qualifier must be preceded by space, {data}.",
                        subfield="a",
                        position=pos,
                    )

                if not re.match(r"^(?:\d{10}|\d{13}|\d{9}X)$", isbnno):
                    self.warn(
                        "020",
                        f"has the wrong number of digits, {data}.",
                        subfield="a",
                        position=pos,
                    )
                else:
                    # Use python-stdnum for validation
                    if not stdnum_isbn.is_valid(isbnno):
                        if len(isbnno) == 10:
                            self.warn(
                                "020",
                                f"has bad checksum, {data}.",
                                subfield="a",
                                position=pos,
                            )
                        elif len(isbnno) == 13:
                            self.warn(
                                "020",
                                f"has bad checksum (13 digit), {data}.",
                                subfield="a",
                                position=pos,
                            )

            elif code == "z":
                if data.startswith("ISBN") or re.match(r"^\d*-\d+", data):
                    if len(isbnno) == 10 and stdnum_isbn.is_valid(isbnno):
                        self.warn(
                            "020", "is numerically valid.", subfield="z", position=pos
                        )

    def check_022(self, field: Field, position: int = 0) -> None:
        """Validate ISSNs in 022$a, 022$y, and 022$z.

        Uses python-stdnum library for standard ISSN validation.
        - $a: valid ISSN
        - $y: incorrect ISSN (but should be numerically valid)
        - $z: canceled ISSN
        """

        subpairs = self._get_subfield_pairs(field)
        pos = position if position > 0 else None

        for code, data in subpairs:
            # Extract ISSN number (remove hyphens and find 8-digit sequence)
            # ISSN format: 8 characters (7 digits + check digit which can be X)
            m = re.search(r"(\d{4}-?\d{3}[X\d])\b", data, re.I)
            if m:
                issnno = m.group(1).replace("-", "").upper()
            else:
                issnno = ""

            if code == "a":
                # Check if ISSN appears to be at start of subfield
                if issnno and not re.match(r"^\d{4}-?\d{3}[X\d]", data, re.I):
                    self.warn(
                        "022",
                        "may have invalid characters.",
                        subfield="a",
                        position=pos,
                    )

                # Check for proper hyphen format if hyphen is present
                if "-" in data and issnno:
                    # Should be XXXX-XXXX format
                    if not re.match(r"^\d{4}-\d{3}[\dXx]", data, re.I):
                        self.warn(
                            "022",
                            f"has improper hyphen placement, {data}.",
                            subfield="a",
                            position=pos,
                        )

                # Check length
                if not re.match(r"^\d{7}[X\d]$", issnno, re.I):
                    self.warn(
                        "022",
                        f"has the wrong number of digits, {data}.",
                        subfield="a",
                        position=pos,
                    )
                else:
                    # Use python-stdnum for validation
                    if not stdnum_issn.is_valid(issnno):
                        self.warn(
                            "022",
                            f"has bad checksum, {data}.",
                            subfield="a",
                            position=pos,
                        )

            elif code == "y":
                # Incorrect ISSN - warn if it's actually valid
                if issnno and stdnum_issn.is_valid(issnno):
                    self.warn(
                        "022", "is numerically valid.", subfield="y", position=pos
                    )

            elif code == "z":
                # Canceled ISSN - just check format (length)
                if not issnno:
                    self.warn(
                        "022",
                        f"has invalid format, {data}.",
                        subfield="z",
                        position=pos,
                    )
                elif not re.match(r"^\d{7}[X\d]$", issnno, re.I):
                    self.warn(
                        "022",
                        f"has invalid format, {data}.",
                        subfield="z",
                        position=pos,
                    )

    def check_041(self, field: Field, position: int = 0) -> None:
        """Language code validation for 041.

        - If indicator 2 is not '7', each subfield value must have
          length divisible by 3.
        - Each 3-character chunk is validated against language code
          tables from `CodeData.pm`.
        """

        subpairs = self._get_subfield_pairs(field)
        pos = position if position > 0 else None

        ind2 = ""
        if hasattr(field, "indicators") and len(field.indicators) >= 2:
            ind2 = field.indicators[1] or ""

        if ind2 != "7":
            for code, value in subpairs:
                if len(value) % 3 != 0:
                    self.warn(
                        "041",
                        f"must be evenly divisible by 3 or exactly three characters if ind2 is not 7, ({value}).",
                        subfield=code,
                        position=pos,
                    )
                    continue

                codes041: List[str] = [
                    value[pos : pos + 3] for pos in range(0, len(value), 3)
                ]
                for c in codes041:
                    valid = 1 if LANGUAGE_CODES.get(c) else 0
                    obsolete = 1 if OBSOLETE_LANGUAGE_CODES.get(c) else 0
                    if not valid:
                        if obsolete:
                            self.warn(
                                "041",
                                f"{value}, may be obsolete.",
                                subfield=code,
                                position=pos,
                            )
                        else:
                            self.warn(
                                "041",
                                f"{value} ({c}), is not valid.",
                                subfield=code,
                                position=pos,
                            )

    def check_043(self, field: Field, position: int = 0) -> None:
        """Geographic area code validation for 043$a."""

        subpairs = self._get_subfield_pairs(field)
        pos = position if position > 0 else None

        for code, value in subpairs:
            if code != "a":
                continue
            if len(value) != 7:
                self.warn(
                    "043",
                    f"must be exactly 7 characters, {value}",
                    subfield="a",
                    position=pos,
                )
            else:
                valid = 1 if GEOG_AREA_CODES.get(value) else 0
                obsolete = 1 if OBSOLETE_GEOG_AREA_CODES.get(value) else 0
                if not valid:
                    if obsolete:
                        self.warn(
                            "043",
                            f"{value}, may be obsolete.",
                            subfield="a",
                            position=pos,
                        )
                    else:
                        self.warn(
                            "043", f"{value}, is not valid.", subfield="a", position=pos
                        )

    def check_008(self, field: Field, position: int = 0) -> None:
        """Control field 008 validation.

        Validates:
        - Field length (must be 40 characters)
        - Position 06: Type of date/publication status
        - Positions 07-10: Date 1 (YYYY format)
        - Positions 11-14: Date 2 (YYYY format or blanks/special values)
        - Positions 15-17: Place of publication/production (country code)
        - Positions 35-37: Language code
        - Position 38: Modified record indicator
        - Position 39: Cataloging source
        """
        pos = position if position > 0 else None

        # Get field data (control fields store data directly, not in subfields)
        data = getattr(field, "data", "") or ""

        # Check length
        if len(data) != 40:
            self.warn(
                "008",
                f"Field must be 40 characters, found {len(data)}.",
                position=pos,
            )
            # Can't validate positions if length is wrong
            if len(data) < 40:
                return

        # Position 06: Type of date/publication status
        type_of_date = data[6]
        if type_of_date not in TYPE_OF_DATE:
            self.warn(
                "008",
                f"Invalid type of date/publication status '{type_of_date}' at position 06.",
                position=pos,
            )

        # Positions 07-10: Date 1 (should be YYYY, blanks, or special)
        date1 = data[7:11]
        if not self._is_valid_008_date(date1):
            self.warn(
                "008",
                f"Invalid Date 1 '{date1}' at positions 07-10.",
                position=pos,
            )

        # Positions 11-14: Date 2
        date2 = data[11:15]
        if not self._is_valid_008_date(date2):
            self.warn(
                "008",
                f"Invalid Date 2 '{date2}' at positions 11-14.",
                position=pos,
            )

        # Positions 15-17: Place of publication (country code)
        # Country codes can be 2 or 3 characters, right-padded with space
        country = data[15:18]
        country_stripped = country.strip()
        valid_country = COUNTRY_CODES.get(country) or COUNTRY_CODES.get(
            country_stripped
        )
        obsolete_country = OBSOLETE_COUNTRY_CODES.get(
            country
        ) or OBSOLETE_COUNTRY_CODES.get(country_stripped)
        if not valid_country and country_stripped != "":
            if obsolete_country:
                self.warn(
                    "008",
                    f"Country code '{country}' at positions 15-17 may be obsolete.",
                    position=pos,
                )
            elif country != "   " and country != "|||":  # blanks or no attempt to code
                self.warn(
                    "008",
                    f"Invalid country code '{country}' at positions 15-17.",
                    position=pos,
                )

        # Positions 35-37: Language code
        language = data[35:38]
        valid_lang = LANGUAGE_CODES.get(language)
        obsolete_lang = OBSOLETE_LANGUAGE_CODES.get(language)
        if not valid_lang:
            if obsolete_lang:
                self.warn(
                    "008",
                    f"Language code '{language}' at positions 35-37 may be obsolete.",
                    position=pos,
                )
            elif (
                language != "   " and language != "|||"
            ):  # blanks or no attempt to code
                self.warn(
                    "008",
                    f"Invalid language code '{language}' at positions 35-37.",
                    position=pos,
                )

        # Position 38: Modified record
        modified_record = data[38]
        valid_modified = {" ", "d", "o", "r", "s", "x", "|"}
        if modified_record not in valid_modified:
            self.warn(
                "008",
                f"Invalid modified record indicator '{modified_record}' at position 38.",
                position=pos,
            )

        # Position 39: Cataloging source
        cataloging_source = data[39]
        valid_cataloging = {" ", "c", "d", "u", "|"}
        if cataloging_source not in valid_cataloging:
            self.warn(
                "008",
                f"Invalid cataloging source '{cataloging_source}' at position 39.",
                position=pos,
            )

    def _is_valid_008_date(self, date_str: str) -> bool:
        """Check if an 008 date string is valid.

        Valid formats:
        - YYYY (4 digits, 0000-9999)
        - '    ' (4 blanks)
        - '||||' (no attempt to code)
        - 'uuuu' (unknown)
        - Partial unknowns like '19uu' or '199u'
        """
        if len(date_str) != 4:
            return False

        # All blanks is valid
        if date_str == "    ":
            return True

        # No attempt to code
        if date_str == "||||":
            return True

        # Check for valid year pattern (digits and 'u' for unknown)
        for char in date_str:
            if char not in "0123456789u":
                return False

        return True

    def check_130(self, field: Field, position: int = 0) -> None:
        """Uniform title heading - validate non-filing indicator."""
        self._check_article(field, position)

    def check_240(self, field: Field, position: int = 0) -> None:
        """Uniform title - validate non-filing indicator."""
        self._check_article(field, position)

    def check_245(self, field: Field, position: int = 0) -> None:
        """Port of the complex 245 title checks from Perl.

        This method enforces:
        - presence and position of subfield a (and 6 when present)
        - final punctuation
        - punctuation and spacing around subfields b, c, h, n, p
        - calls `_check_article` for non-filing indicator logic.
        """

        tagno = "245"
        pos = position if position > 0 else None

        # Use safe subfield access; `get_subfields` returns [] if missing
        if not field.get_subfields("a"):
            self.warn("245", "Must have a subfield _a.", position=pos)

        subs = field.subfields
        flat: List[str] = []
        has_sub_6 = False
        # Support flat [code, data, ...] or Subfield objects
        if subs and isinstance(subs[0], str):
            iterable = list(zip(subs[0::2], subs[1::2]))  # type: ignore[arg-type]
        else:
            iterable = []
            for sf in subs:
                code = getattr(sf, "code", None)
                data = getattr(sf, "value", None)
                if code is None or data is None:
                    continue
                iterable.append((code, data))

        # Build flat list in natural order: [code0, data0, code1, data1, ...]
        for code, data in iterable:
            if code == "6":
                has_sub_6 = True
            flat.append(str(code))
            flat.append(str(data))

        # Final punctuation check looks at the last data element
        last_data = flat[-1] if flat else ""
        if isinstance(last_data, str) and not re.search(r"[.?!]$", last_data):
            self.warn("245", "Must end with . (period).", position=pos)
        elif isinstance(last_data, str) and re.search(r"[?!]$", last_data):
            self.warn(
                "245",
                "MARC21 allows ? or ! as final punctuation but LCRI 1.0C, Nov. 2003 (LCPS 1.7.1 for RDA records), requires period.",
                position=pos,
            )

        if has_sub_6:
            if len(flat) < 4:
                self.warn("245", "May have too few subfields.", position=pos)
            else:
                if flat[0] != "6":
                    self.warn(
                        tagno,
                        f"First subfield must be _6, but it is _{flat[0]}",
                        position=pos,
                    )
                if flat[2] != "a":
                    self.warn(
                        tagno,
                        f"First subfield after subfield _6 must be _a, but it is _{flat[2]}",
                        position=pos,
                    )
        else:
            if flat and flat[0] != "a":
                self.warn(
                    tagno,
                    f"First subfield must be _a, but it is _{flat[0]}",
                    position=pos,
                )

        if field.get_subfields("c"):
            for i in range(2, len(flat), 2):
                if flat[i] == "c":
                    if not re.search(r"\s/$", flat[i - 1]):
                        self.warn(
                            "245", "Subfield _c must be preceded by /", position=pos
                        )
                    if re.search(r"\b\w\. \b\w\.", flat[i + 1]) and not re.search(
                        r"\[\bi\.e\. \b\w\..*\]", flat[i + 1]
                    ):
                        self.warn(
                            "245",
                            "Subfield _c initials should not have a space.",
                            position=pos,
                        )
                    break

        if field.get_subfields("b"):
            for i in range(2, len(flat), 2):
                if flat[i] == "b" and not re.search(r" [:;=]$", flat[i - 1]):
                    self.warn(
                        "245",
                        "Subfield _b should be preceded by space-colon, space-semicolon, or space-equals sign.",
                        position=pos,
                    )

        if field.get_subfields("h"):
            for i in range(2, len(flat), 2):
                if flat[i] == "h":
                    if not re.search(r"(\S$)|(\-\- $)", flat[i - 1]):
                        self.warn(
                            "245",
                            "Subfield _h should not be preceded by space.",
                            position=pos,
                        )
                    if not re.match(r"^\[\w*\s*\w*\]", flat[i + 1]):
                        self.warn(
                            "245",
                            f"Subfield _h must have matching square brackets, {flat[i]}.",
                            position=pos,
                        )

        if field.get_subfields("n"):
            for i in range(2, len(flat), 2):
                if flat[i] == "n" and not re.search(r"(\S\.$)|(\-\- \.$)", flat[i - 1]):
                    self.warn(
                        "245",
                        "Subfield _n must be preceded by . (period).",
                        position=pos,
                    )

        if field.get_subfields("p"):
            for i in range(2, len(flat), 2):
                if flat[i] == "p":
                    if flat[i - 2] == "n" and not re.search(
                        r"(\S,$)|(\-\- ,$)", flat[i - 1]
                    ):
                        self.warn(
                            "245",
                            "Subfield _p must be preceded by , (comma) when it follows subfield _n.",
                            position=pos,
                        )
                    elif flat[i - 2] != "n" and not re.search(
                        r"(\S\.$)|(\-\- \.$)", flat[i - 1]
                    ):
                        self.warn(
                            "245",
                            "Subfield _p must be preceded by . (period) when it follows a subfield other than _n.",
                            position=pos,
                        )

        self._check_article(field, position)

    def check_630(self, field: Field, position: int = 0) -> None:
        """Subject added entry-Uniform title - validate non-filing indicator."""
        self._check_article(field, position)

    def check_730(self, field: Field, position: int = 0) -> None:
        """Added entry-Uniform title - validate non-filing indicator."""
        self._check_article(field, position)

    def check_830(self, field: Field, position: int = 0) -> None:
        """Series added entry-Uniform title - validate non-filing indicator."""
        self._check_article(field, position)

    # -------- internal helpers --------

    def _get_record_language(self) -> Optional[str]:
        """Get the language code from the current record's 008 field.

        Returns the 3-character language code from positions 35-37 of the 008
        field, or None if not available or invalid.
        """

        fields_008 = self._current_record.get_fields("008")
        if not fields_008:
            return None

        data = getattr(fields_008[0], "data", "") or ""
        if len(data) < 38:
            return None

        language = data[35:38]

        # Return None for blank/unknown values
        if language in ("   ", "|||", "   ", "und", "zxx"):
            return None

        # Validate against known language codes
        if LANGUAGE_CODES.get(language) or OBSOLETE_LANGUAGE_CODES.get(language):
            return language

        return None

    def _get_subfield_pairs(self, field: Field) -> List[tuple[str, str]]:
        """Extract subfield code/data pairs from a field.

        Supports both flat list format ['a', 'Title', 'b', 'Subtitle']
        and Subfield object format [Subfield('a', 'Title'), Subfield('b', 'Subtitle')].

        Returns:
            List of (code, data) tuples.
        """
        raw_subs = getattr(field, "subfields", [])
        subpairs: List[tuple[str, str]] = []

        if raw_subs and isinstance(raw_subs[0], str):
            # Flat form: [code, data, code, data, ...]
            subpairs = list(zip(raw_subs[0::2], raw_subs[1::2]))  # type: ignore[arg-type]
        else:
            # Object form: [Subfield(code, value), ...]
            for sf in raw_subs:
                code = getattr(sf, "code", None)
                data = getattr(sf, "value", None)
                if code is None or data is None:
                    continue
                subpairs.append((str(code), str(data)))

        return subpairs

    def _check_article(self, field: Field, position: int = 0) -> None:
        """Validate non-filing indicators for article-initial titles.

        Checks whether the non-filing character count indicator correctly
        reflects the presence and length of initial articles in various
        languages. Used for uniform titles and main titles (130, 240, 245,
        630, 730, 830).

        Articles are matched against a curated list of known indefinite/
        definite articles from multiple languages, with exceptions for
        phrases that start with article-like words but shouldn't be treated
        as articles (e.g., "Los Angeles", "A & E").
        """

        # Map article strings to language codes where they function as articles
        # Format: article (lowercase) -> list of ISO 639-2 language codes
        # Note: Language codes are for documentation; validation only checks key existence
        ARTICLES = {
            "'n": ["afr"],
            "a": ["eng", "glg", "hun", "por", "yid"],
            "an": ["eng", "gle", "yid"],
            "as": ["por"],
            "az": ["hun"],
            "das": ["ger"],
            "de": ["dut"],
            "dem": ["ger"],
            "den": ["dan", "ger", "nor", "swe"],
            "der": ["ger", "yid"],
            "des": ["fre", "ger"],
            "det": ["dan", "nor", "swe"],
            "di": ["yid"],
            "die": ["afr", "ger"],
            "dos": ["yid"],
            "du": ["fre"],
            "een": ["dut"],
            "egy": ["hun"],
            "ein": ["ger"],
            "eine": ["ger"],
            "einem": ["ger"],
            "einen": ["ger"],
            "einer": ["ger"],
            "eines": ["ger"],
            "el": ["cat", "spa"],
            "els": ["cat"],
            "en": ["cat", "dan", "nor", "swe"],
            "et": ["dan", "nor"],
            "ett": ["swe"],
            "gl": ["ita"],
            "gli": ["ita"],
            "het": ["dut"],
            "hin": ["ice"],
            "hinn": ["ice"],
            "hið": ["ice"],
            "hina": ["ice"],
            "hinir": ["ice"],
            "hinar": ["ice"],
            "hinu": ["ice"],
            "hinum": ["ice"],
            "hinni": ["ice"],
            "hins": ["ice"],
            "hinnar": ["ice"],
            "hinna": ["ice"],
            "i": ["ita"],
            "il": ["ita", "mlt"],
            "l": ["cat", "fre", "ita", "mlt"],
            "la": ["cat", "epo", "fre", "ita", "spa"],
            "las": ["spa"],
            "le": ["fre", "ita"],
            "les": ["cat", "fre"],
            "lo": ["ita", "spa"],
            "los": ["spa"],
            "o": ["por"],
            "os": ["por"],
            "na": ["gle"],
            "the": ["eng"],
            "uno": ["ita"],
            "un": ["cat", "fre", "ita", "spa"],
            "una": ["cat", "ita", "spa"],
            "unes": ["cat"],
            "uns": ["cat", "por"],
            "um": ["por"],
            "uma": ["por"],
            "umas": ["por"],
            "une": ["fre"],
            "unas": ["spa"],
            "unos": ["spa"],
            "y": ["wel"],
            "yr": ["wel"],
        }

        # Phrases that begin with article-like words but should NOT be
        # treated as having a non-filing article (proper nouns, acronyms, etc.)
        ARTICLE_EXCEPTIONS = {
            "A & E",  # TV channel/brand
            "A & ",  # Generic "A and" pattern
            "A-",  # A-prefix words (A-level, etc.)
            "A+",  # Grade designation
            "A is ",  # "A" as subject
            "A isn't ",  # "A" as subject
            "A l'",  # French "à l'" (not article "a")
            "A la ",  # "À la" French phrase
            "A posteriori",  # Latin phrase
            "A priori",  # Latin phrase
            "A to ",  # "A" as letter/item
            "El Nino",  # Weather phenomenon
            "El Salvador",  # Country name
            "L is ",  # "L" as subject
            "L-",  # L-prefix words
            "La Salle",  # Proper name
            "Las Vegas",  # City name
            "Lo cual",  # Spanish relative pronoun phrase
            "Lo mein",  # Food name
            "Lo que",  # Spanish relative pronoun phrase
            "Los Alamos",  # City name
            "Los Angeles",  # City name
        }

        # Languages we have article data for - only judge these
        SUPPORTED_ARTICLE_LANGUAGES = {
            "afr",
            "cat",
            "dan",
            "dut",
            "eng",
            "epo",
            "fre",
            "ger",
            "gle",
            "glg",
            "hun",
            "ice",
            "ita",
            "mlt",
            "nor",
            "por",
            "spa",
            "swe",
            "wel",
            "yid",
        }

        # Determine which field we're checking (handle 880 linked fields)
        tagno = field.tag
        if tagno == "880" and field["6"]:
            tagno = field["6"][:3]

        # Only validate fields that use non-filing indicators
        if tagno not in {"130", "240", "245", "440", "630", "730", "830"}:
            return

        pos = position if position > 0 else None

        # Different fields use different indicator positions:
        # - 130, 630, 730 use indicator 1 (first)
        # - 240, 245, 830 use indicator 2 (second)
        if tagno in {"130", "630", "730"}:
            ind = ""
            if hasattr(field, "indicators") and len(field.indicators) >= 1:
                ind = field.indicators[0] or ""
            first_or_second = "1st"
        else:
            ind = ""
            if hasattr(field, "indicators") and len(field.indicators) >= 2:
                ind = field.indicators[1] or ""
            first_or_second = "2nd"

        # Indicator must be numeric (0-9)
        if not re.match(r"^[0-9]$", ind):
            self.warn(tagno, "Non-filing indicator is non-numeric", position=pos)

        # Extract title from subfield $a
        sub_a = field.get_subfields("a")
        title = sub_a[0] if sub_a else ""

        # Count and strip leading non-alphanumeric characters
        # (quotes, brackets, parentheses, asterisks)
        char1_notalphanum = 0
        while title and title[0] in "\"'[*":
            char1_notalphanum += 1
            title = title[1:]

        # Extract first word and following separator/text
        # Pattern matches: word + optional separator + rest of string
        m = re.match(r"^([^ \(\)\[\]'\"\-]+)([ \(\)\[\]'\"])?(.*)", title, re.I)
        if m:
            firstword, separator, etc = m.group(1), m.group(2) or "", m.group(3) or ""
        else:
            firstword, separator, etc = "", "", ""

        # Calculate non-filing character count:
        # article length + leading punctuation + trailing space
        nonfilingchars = len(firstword) + char1_notalphanum + 1

        # Check if title starts with an exception phrase (case-insensitive)
        isan_exception = any(
            re.match(rf"^{re.escape(k)}", title, re.I) for k in ARTICLE_EXCEPTIONS
        )

        # Check if first word is an article (and not an exception)
        fw_lower = firstword.lower()
        article_langs = ARTICLES.get(fw_lower)

        # Get the record's language from 008 field (positions 35-37)
        record_lang = self._get_record_language()

        # Only consider it an article if:
        # 1. The word is in our articles list
        # 2. It's not an exception phrase
        # 3. The record's language matches one where this word is an article
        isan_article = False
        if article_langs and not isan_exception:
            if record_lang is None:
                # Can't determine language - don't make assumptions about articles
                # Just check if indicator is valid (0-9) which we did above
                pass
            elif record_lang in article_langs:
                # Record's language matches one where this word is an article
                isan_article = True
            # else: word exists as article in other languages but not this record's language

        if isan_article:
            # If there's a separator and following text, count additional
            # leading punctuation characters
            if separator and etc and etc[0] in " ()[]'\"-":
                while etc and etc[0] in " \"'[]()*":
                    nonfilingchars += 1
                    etc = etc[1:]

            # Special case: "en" is ambiguous (could be article or not)
            # Accept either 0 (not treated as article) or 3 (treated as article)
            if fw_lower == "en":
                if ind not in {"3", "0"}:
                    self.warn(
                        tagno,
                        f"First word, , {fw_lower}, may be an article, check {first_or_second} indicator ({ind}).",
                        position=pos,
                    )
            # Standard case: indicator should match calculated non-filing count
            elif str(nonfilingchars) != ind:
                self.warn(
                    tagno,
                    f"First word, {fw_lower}, may be an article, check {first_or_second} indicator ({ind}).",
                    position=pos,
                )
        else:
            # If first word is not an article in this language, indicator should be 0
            # But only warn if we have article data for this language
            if ind != "0" and record_lang in SUPPORTED_ARTICLE_LANGUAGES:
                self.warn(
                    tagno,
                    f"First word, {fw_lower}, does not appear to be an article, check {first_or_second} indicator ({ind}).",
                    position=pos,
                )
