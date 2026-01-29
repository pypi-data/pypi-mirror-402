from typing import Set, Optional

class CountryList:
    """Helper class for validating country codes."""

    VALID_COUNTRY_CODES: Set[str] = {
        "AF", "AL", "DZ", "AS", "AD", "AO", "AI", "AQ", "AG", "AR", "AM", "AW", "AU", "AT", "AZ",
        "BS", "BH", "BD", "BB", "BY", "BE", "BZ", "BJ", "BM", "BT", "BO", "BA", "BW", "BV", "BR",
        "BQ", "IO", "VG", "BN", "BG", "BF", "BI", "KH", "CM", "CA", "CT", "CV", "KY", "CF", "TD",
        "CL", "CN", "CX", "CC", "CO", "KM", "CG", "CD", "CK", "CR", "HR", "CU", "CY", "CZ", "CI",
        "DK", "DJ", "DM", "DO", "NQ", "EC", "EG", "SV", "GQ", "ER", "EE", "ET", "FK", "FO", "FJ",
        "FI", "FR", "GF", "PF", "TF", "FQ", "GA", "GM", "GE", "DE", "GH", "GI", "GR", "GL", "GD",
        "GP", "GU", "GT", "GG", "GN", "GW", "GY", "HT", "HM", "HN", "HK", "HU", "IS", "IN", "ID",
        "IR", "IQ", "IE", "IM", "IL", "IT", "JM", "JP", "JE", "JT", "JO", "KZ", "KE", "KI", "KW",
        "KG", "LA", "LV", "LB", "LS", "LR", "LY", "LI", "LT", "LU", "MO", "MK", "MG", "MW", "MY",
        "MV", "ML", "MT", "MH", "MQ", "MR", "MU", "YT", "FX", "MX", "FM", "MI", "MD", "MC", "MN",
        "ME", "MS", "MA", "MZ", "MM", "NA", "NR", "NP", "NL", "AN", "NT", "NC", "NZ", "NI", "NE",
        "NG", "NU", "NF", "KP", "VD", "MP", "NO", "OM", "PC", "PK", "PW", "PS", "PA", "PZ", "PG",
        "PY", "YD", "PE", "PH", "PN", "PL", "PT", "PR", "QA", "RO", "RU", "RW", "RE", "BL", "SH",
        "KN", "LC", "MF", "SX", "PM", "VC", "WS", "SM", "SA", "SN", "RS", "CS", "SC", "SL", "SG",
        "SK", "SI", "SB", "SO", "ZA", "GS", "KR", "ES", "LK", "SD", "SR", "SJ", "SZ", "SE", "CH",
        "SY", "ST", "TW", "TJ", "TZ", "TH", "TL", "TG", "TK", "TO", "TT", "TN", "TR", "TM", "TC",
        "TV", "UM", "PU", "VI", "UG", "UA", "AE", "GB", "UY", "UZ", "VU", "VA", "VE", "VN", "WK",
        "WF", "EH", "YE", "ZM", "ZW", "AX"
    }

    def is_valid_country_code(self, country_code: str) -> bool:
        """Check if a country code is valid."""
        if not country_code:
            return False
        return country_code.upper() in self.VALID_COUNTRY_CODES

    def get_country_code_by_name(self, country_name: str) -> Optional[str]:
        """
        Look up a country code by name.
        Note: This would typically require a large mapping dictionary.
        For now, we will return the code if the input is already a valid code,
        or None if not found (placeholder for full mapping implementation).
        """
        if self.is_valid_country_code(country_name):
            return country_name.upper()
        # TODO: Implement full name-to-code mapping if needed/available.
        return None
