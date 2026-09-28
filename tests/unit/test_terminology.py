"""Tests for annotate code-system aliases (009)."""

import pytest

from rh_mod_skills.terminology import (
    SYSTEM_URIS,
    normalize_plan_system,
    parse_candidate_flag,
    system_uri,
)


def test_system_uri_new_aliases():
    assert system_uri("rxnorm") == "http://www.nlm.nih.gov/research/umls/rxnorm"
    assert system_uri("ucum") == "http://unitsofmeasure.org"
    assert system_uri("icd-10-cm") == "http://hl7.org/fhir/sid/icd-10-cm"
    assert system_uri("icd-10") == "http://hl7.org/fhir/sid/icd-10"
    assert system_uri("snomed") == "http://snomed.info/sct"
    assert system_uri("loinc") == "http://loinc.org"


def test_system_uri_http_passthrough():
    uri = "http://example.org/cs"
    assert system_uri(uri) == uri


def test_system_uri_all_is_search_mode():
    with pytest.raises(ValueError, match="search mode"):
        system_uri("all")


def test_system_uri_unknown():
    with pytest.raises(ValueError, match="Unknown code system"):
        system_uri("not-a-system")


def test_normalize_plan_system_aliases_and_all():
    assert normalize_plan_system("RxNorm") == "rxnorm"
    assert normalize_plan_system("all") == "all"
    assert normalize_plan_system("http://loinc.org") == "http://loinc.org"


def test_normalize_plan_system_unknown():
    with pytest.raises(ValueError, match="Unknown code system"):
        normalize_plan_system("foo")


@pytest.mark.parametrize(
    "alias,uri",
    list(SYSTEM_URIS.items()),
)
def test_parse_candidate_expands_aliases(alias, uri):
    hit = parse_candidate_flag(f"{alias}|ABC|Display")
    assert hit["system"] == uri
    assert hit["code"] == "ABC"
    assert hit["display"] == "Display"


def test_parse_candidate_http_passthrough():
    hit = parse_candidate_flag("http://snomed.info/sct|263495000|Gender")
    assert hit["system"] == "http://snomed.info/sct"
    assert hit["code"] == "263495000"


def test_parse_candidate_rejects_all():
    with pytest.raises(ValueError, match="search mode"):
        parse_candidate_flag("all|x|y")
