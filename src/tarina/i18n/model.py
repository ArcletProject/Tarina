# This file is @generated by tarina.lang CLI tool
# It is not intended for manual editing.

from tarina.lang.model import LangModel, LangItem


class Lang_Error:
    locale: LangItem = LangItem("lang", "error.locale")
    scope: LangItem = LangItem("lang", "error.scope")
    type: LangItem = LangItem("lang", "error.type")



class Lang_:
    error = Lang_Error
    miss_require_scope: LangItem = LangItem("lang", "miss_require_scope")
    miss_require_type: LangItem = LangItem("lang", "miss_require_type")


class Lang(LangModel):
    lang = Lang_