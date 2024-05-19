from tarina.lang.model import LangModel, LangItem


class Lang_:
    locale_error: LangItem = LangItem("lang", "locale_error")
    scope_error: LangItem = LangItem("lang", "scope_error")
    type_error: LangItem = LangItem("lang", "type_error")
    miss_require_scope: LangItem = LangItem("lang", "miss_require_scope")
    miss_require_type: LangItem = LangItem("lang", "miss_require_type")


class Lang(LangModel):
    lang = Lang_

