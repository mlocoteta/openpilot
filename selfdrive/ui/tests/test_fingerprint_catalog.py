from openpilot.selfdrive.ui.lib.fingerprint_catalog import _extract_fingerprint_models_for_make, get_fingerprint_catalog


def test_tesla_hardware_specific_docs_are_available_for_manual_fingerprinting():
  tesla_models = _extract_fingerprint_models_for_make("tesla")

  assert ("TESLA_MODEL_3", "Tesla Model 3 (with HW3) 2019-23", "Tesla") in tesla_models
  assert ("TESLA_MODEL_3", "Tesla Model 3 (with HW4) 2024-26", "Tesla") in tesla_models
  assert ("TESLA_MODEL_Y", "Tesla Model Y (with HW3) 2020-23", "Tesla") in tesla_models
  assert ("TESLA_MODEL_X", "Tesla Model X (with HW4) 2024", "Tesla") in tesla_models


def test_tesla_model_3_hardware_variants_remain_distinct_menu_options():
  _, models_by_make, _, _ = get_fingerprint_catalog()
  model_3_options = [option for option in models_by_make["Tesla"] if option.value == "TESLA_MODEL_3"]

  assert [option.label for option in model_3_options] == [
    "Tesla Model 3 (with HW3) 2019-23",
    "Tesla Model 3 (with HW4) 2024-26",
  ]


def test_catalog_parses_shared_sources_once_and_preserves_make_order(tmp_path, monkeypatch):
  from pathlib import Path
  from openpilot.selfdrive.ui.lib import fingerprint_catalog as catalog

  values = tmp_path / 'opendbc' / 'car' / 'honda' / 'values.py'
  values.parent.mkdir(parents=True)
  values.write_text('''
SHARED = PlatformConfig([
  HondaCarDocs("Honda Accord 2018"),
  HondaCarDocs("Acura ILX 2019"),
  HondaCarDocs("Honda Accord 2018"),
], specs=CarSpecs())
SECOND = PlatformConfig([
  HondaCarDocs("Honda Accord 2018"),
  HondaCarDocs("Honda Civic 2020", footnotes=[Footnote.SAMPLE]),
], specs=CarSpecs())
''')
  monkeypatch.setattr(catalog, 'FINGERPRINT_MAKE_TO_VALUES_DIR', {'honda': 'honda', 'acura': 'honda', 'missing': 'missing'})
  roots = []
  monkeypatch.setattr(catalog, '_get_openpilot_root', lambda: roots.append(tmp_path) or tmp_path)
  reads = []
  read_text = Path.read_text

  def tracked_read(path, *args, **kwargs):
    reads.append(path)
    return read_text(path, *args, **kwargs)

  monkeypatch.setattr(Path, 'read_text', tracked_read)
  catalog.get_fingerprint_catalog.cache_clear()
  try:
    result = catalog.get_fingerprint_catalog()
    makes, by_make, by_value, make_by_model = result
    assert makes == ('Acura', 'Honda')
    assert [option.value for option in by_make['Honda']] == ['SHARED', 'SECOND', 'SECOND']
    assert [option.option_label for option in by_make['Honda']] == ['Honda Accord 2018', 'Honda Accord 2018 (SECOND)', 'Civic 2020']
    assert by_value['SHARED'].label == 'Acura ILX 2019'
    assert make_by_model['SHARED'] == 'Acura'
    assert reads == [values]
    assert roots == [tmp_path]
    assert catalog.get_fingerprint_catalog() is result
    assert reads == [values]

    catalog.get_fingerprint_catalog.cache_clear()
    assert catalog.get_fingerprint_catalog() == result
    assert reads == [values, values]
  finally:
    catalog.get_fingerprint_catalog.cache_clear()


def test_extract_uses_legacy_source_when_opendbc_source_is_missing(tmp_path, monkeypatch):
  from openpilot.selfdrive.ui.lib import fingerprint_catalog as catalog

  values = tmp_path / 'selfdrive' / 'car' / 'honda' / 'values.py'
  values.parent.mkdir(parents=True)
  values.write_text('CAR = PlatformConfig([CarDocs("Acura ILX 2019")], specs=CarSpecs())')
  monkeypatch.setattr(catalog, '_get_openpilot_root', lambda: tmp_path)

  assert catalog._extract_fingerprint_models_for_make('acura') == [('CAR', 'Acura ILX 2019', 'Acura')]
  assert catalog._extract_fingerprint_models_for_make('honda') == []
  assert catalog._extract_fingerprint_models_for_make('missing') == []


def test_extract_keeps_empty_result_when_selected_source_cannot_be_read(tmp_path, monkeypatch):
  from pathlib import Path
  from openpilot.selfdrive.ui.lib import fingerprint_catalog as catalog

  for directory in ('opendbc', 'selfdrive'):
    values = tmp_path / directory / 'car' / 'honda' / 'values.py'
    values.parent.mkdir(parents=True)
    values.write_text('CAR = PlatformConfig([CarDocs("Honda Civic 2020")], specs=CarSpecs())')
  monkeypatch.setattr(catalog, '_get_openpilot_root', lambda: tmp_path)
  reads = []

  def failed_read(path, **kwargs):
    reads.append(path)
    raise OSError('unreadable source')

  monkeypatch.setattr(Path, 'read_text', failed_read)

  assert catalog._extract_fingerprint_models_for_make('honda') == []
  assert reads == [tmp_path / 'opendbc' / 'car' / 'honda' / 'values.py']
