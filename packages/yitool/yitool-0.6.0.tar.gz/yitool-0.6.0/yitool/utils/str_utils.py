import yitool.utils._humps as _humps


class StrUtils:
    """String utilities."""

    @staticmethod
    def is_empty(s: str) -> bool:
        """Check if string is empty."""
        return s is None or s.strip() == ""

    @staticmethod
    def is_not_empty(s: str) -> bool:
        """Check if string is not empty."""
        return not StrUtils.is_empty(s)

    @staticmethod
    def safe(s: str) -> str:
        """Safe string access, returns empty string for None."""
        return s if s is not None else ""

    @staticmethod
    def camel_ize(str_or_iter: str) -> str:
        """Convert to camelCase."""
        return _humps.camelize(str_or_iter)

    @staticmethod
    def de_camelize(str_or_iter: str) -> str:
        """Convert from camelCase to snake_case."""
        return _humps.decamelize(str_or_iter)

    @staticmethod
    def pascal_ize(str_or_iter: str) -> str:
        """Convert to PascalCase."""
        return _humps.pascalize(str_or_iter)

    @staticmethod
    def kebab_ize(str_or_iter: str) -> str:
        """Convert to kebab-case."""
        return _humps.kebabize(str_or_iter)

    @staticmethod
    def split(s: str, delimiter: str = ",") -> list:
        """Split string into list."""
        if StrUtils.is_empty(s):
            return []
        return [item.strip() for item in s.split(delimiter) if item.strip()]

    @staticmethod
    def camelize_dict_keys(d: dict) -> dict:
        """Convert dictionary keys to camelCase."""
        if d is None:
            return {}
        return {StrUtils.camel_ize(k): v for k, v in d.items()}

    @staticmethod
    def decamelize_dict_keys(d: dict) -> dict:
        """Convert dictionary keys to snake_case."""
        if d is None:
            return {}
        return {StrUtils.de_camelize(k): v for k, v in d.items()}

    @staticmethod
    def camelize_dicts(lst: list) -> list:
        """Convert list of dicts keys to camelCase."""
        if lst is None:
            return []
        return [StrUtils.camelize_dict_keys(item) if isinstance(item, dict) else item for item in lst]

    @staticmethod
    def decamelize_dicts(lst: list) -> list:
        """Convert list of dicts keys to snake_case."""
        if lst is None:
            return []
        return [StrUtils.decamelize_dict_keys(item) if isinstance(item, dict) else item for item in lst]
