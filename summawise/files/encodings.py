from enum import Enum
from typing import Optional

class Encoding(Enum):
    """
    Encodings supported by the chardet library, turned into an enum.
    Source: https://github.com/chardet/chardet/blob/9630f2382faa50b81be2f96fd3dfab5f6739a0ef/docs/supported-encodings.rst
    """
    BIG5 = "Big5"
    GB2312 = "GB2312"
    GB18030 = "GB18030"
    EUC_TW = "EUC-TW"
    HZ_GB_2312 = "HZ-GB-2312"
    ISO_2022_CN = "ISO-2022-CN"
    EUC_JP = "EUC-JP"
    SHIFT_JIS = "SHIFT_JIS"
    ISO_2022_JP = "ISO-2022-JP"
    EUC_KR = "EUC-KR"
    ISO_2022_KR = "ISO-2022-KR"
    KOI8_R = "KOI8-R"
    MAC_CYRILLIC = "MacCyrillic"
    IBM855 = "IBM855"
    IBM866 = "IBM866"
    ISO_8859_5_RUS = "ISO-8859-5"
    WINDOWS_1251_RUS = "windows-1251"
    ISO_8859_2_HUN = "ISO-8859-2"
    WINDOWS_1250_HUN = "windows-1250"
    ISO_8859_5_BUL = "ISO-8859-5"
    WINDOWS_1251_BUL = "windows-1251"
    ISO_8859_1_WEU = "ISO-8859-1"
    WINDOWS_1252_WEU = "windows-1252"
    ISO_8859_7_GREEK = "ISO-8859-7"
    WINDOWS_1253_GREEK = "windows-1253"
    ISO_8859_8_HEB_VIS = "ISO-8859-8"
    WINDOWS_1255_HEB_VIS = "windows-1255"
    ISO_8859_8_HEB_LOG = "ISO-8859-8"
    WINDOWS_1255_HEB_LOG = "windows-1255"
    TIS_620 = "TIS-620"
    UTF_32_BE = "UTF-32 BE"
    UTF_32_LE = "UTF-32 LE"
    UTF_32_3412 = "UTF-32 3412"
    UTF_32_2143 = "UTF-32 2143"
    UTF_16_BE = "UTF-16 BE"
    UTF_16_LE = "UTF-16 LE"
    UTF_8 = "UTF-8"
    ASCII = "ASCII"
    
    @classmethod
    def from_string(cls, encoding_str) -> Optional["Encoding"]:
        """
        Get 'Encoding' Enum from chardet string. 
        Returns 'None' if no match is found.
        """
        for encoding in cls:
            if encoding.value.lower() == encoding_str.lower():
                return encoding
        return None
