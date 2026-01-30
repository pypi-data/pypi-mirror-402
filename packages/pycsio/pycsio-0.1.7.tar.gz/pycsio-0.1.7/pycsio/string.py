class StringExt:
    @staticmethod
    def Escape(val):
        if not val:
            return ""
        return ''.join(c for c in val if not c.isspace())