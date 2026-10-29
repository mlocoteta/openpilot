from openpilot.system.ui.lib.multilang import Multilang, PLURAL_SELECTORS


def test_external_language_selection_and_english_fallback():
  language = Multilang()
  class SavedLanguage:
    value = 'vi'

    def get(self, key):
      assert key == 'LanguageSetting'
      return self.value

  saved = SavedLanguage()
  language._params = saved
  language.refresh_language()
  assert language.language == 'vi'
  assert language.tr('Cancel') == 'Hủy'
  assert language.tr('Untranslated text') == 'Untranslated text'
  assert language.trn('{} day ago', '{} days ago', 2) == '{} ngày trước'
  assert PLURAL_SELECTORS['vi'](0) == PLURAL_SELECTORS['vi'](2) == 0
  saved.value = 'main_ja'
  language.refresh_language()
  assert language.language == 'ja' and language.requires_font_fallback()
  saved.value = 'unknown'
  language.refresh_language()
  assert language.language == 'en' and language.tr('Cancel') == 'Cancel'
