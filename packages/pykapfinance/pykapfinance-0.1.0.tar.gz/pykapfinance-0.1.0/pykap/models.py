"""
Data models for KAP API
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class DisclosureInfo:
    """Disclosure information from disclosure list"""
    disclosure_index: str
    disclosure_type: str
    disclosure_class: str
    title: str
    company_id: str
    accepted_data_file_types: List[str]
    sub_report_ids: Optional[List[str]] = None
    fund_id: Optional[str] = None
    fund_code: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DisclosureInfo':
        """Create from dictionary"""
        return cls(
            disclosure_index=data.get("disclosureIndex"),
            disclosure_type=data.get("disclosureType"),
            disclosure_class=data.get("disclosureClass"),
            title=data.get("title"),
            company_id=data.get("companyId"),
            accepted_data_file_types=data.get("acceptedDataFileTypes", []),
            sub_report_ids=data.get("subReportIds"),
            fund_id=data.get("fundId"),
            fund_code=data.get("fundCode")
        )


@dataclass
class Subject:
    """Bilingual subject"""
    tr: Optional[str] = None
    en: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional['Subject']:
        """Create from dictionary"""
        if not data:
            return None
        return cls(
            tr=data.get("tr"),
            en=data.get("en")
        )


@dataclass
class AttachmentUrl:
    """Attachment URL information"""
    url: str
    file_name: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AttachmentUrl':
        """Create from dictionary"""
        return cls(
            url=data.get("url"),
            file_name=data.get("fileName")
        )


@dataclass
class RelatedStock:
    """Related stock information"""
    code: str
    stock: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RelatedStock':
        """Create from dictionary"""
        return cls(
            code=data.get("code"),
            stock=data.get("stock")
        )


@dataclass
class DisclosureDetail:
    """Detailed disclosure information"""
    disclosure_index: str
    sender_id: str
    sender_title: str
    sender_exch_codes: List[str]
    disclosure_type: str
    disclosure_class: str
    subject: Subject
    summary: Subject
    time: str
    link: str
    disclosure_reason: Optional[str] = None
    behalf_sender_id: Optional[str] = None
    behalf_sender_title: Optional[str] = None
    behalf_sender_exch_codes: Optional[List[str]] = None
    behalf_fund_code: Optional[str] = None
    behalf_fund_title: Optional[str] = None
    disclosure_delay_status: Optional[str] = None
    related_disclosure_index: Optional[str] = None
    consolidation: Optional[str] = None
    year: Optional[str] = None
    period: Optional[Subject] = None
    related_stocks: Optional[List[RelatedStock]] = None
    attachment_urls: Optional[List[AttachmentUrl]] = None
    event_type: Optional[str] = None
    event_id: Optional[int] = None
    presentation: Optional[List[Dict]] = None
    flat_data: Optional[Dict] = None
    html_message: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DisclosureDetail':
        """Create from dictionary"""
        return cls(
            disclosure_index=data.get("disclosureIndex"),
            sender_id=data.get("senderId"),
            sender_title=data.get("senderTitle"),
            sender_exch_codes=data.get("senderExchCodes", []),
            disclosure_type=data.get("disclosureType"),
            disclosure_class=data.get("disclosureClass"),
            subject=Subject.from_dict(data.get("subject")),
            summary=Subject.from_dict(data.get("summary")),
            time=data.get("time"),
            link=data.get("link"),
            disclosure_reason=data.get("disclosureReason"),
            behalf_sender_id=data.get("behalfSenderId"),
            behalf_sender_title=data.get("behalfSenderTitle"),
            behalf_sender_exch_codes=data.get("behalfSenderExchCodes"),
            behalf_fund_code=data.get("behalfFundCode"),
            behalf_fund_title=data.get("behalfFundTitle"),
            disclosure_delay_status=data.get("disclosureDelayStatus"),
            related_disclosure_index=data.get("relatedDisclosureIndex"),
            consolidation=data.get("consolidation"),
            year=data.get("year"),
            period=Subject.from_dict(data.get("period")),
            related_stocks=[RelatedStock.from_dict(s) for s in data.get("relatedStocks", [])],
            attachment_urls=[AttachmentUrl.from_dict(a) for a in data.get("attachmentUrls", [])],
            event_type=data.get("eventType"),
            event_id=data.get("eventId"),
            presentation=data.get("presentation"),
            flat_data=data.get("flatData"),
            html_message=data.get("htmlMessage")
        )


@dataclass
class MemberInfo:
    """KAP member (company) information"""
    id: str
    title: str
    stock_code: str
    member_type: str
    kfif_url: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemberInfo':
        """Create from dictionary"""
        return cls(
            id=data.get("id"),
            title=data.get("title"),
            stock_code=data.get("stockCode"),
            member_type=data.get("memberType"),
            kfif_url=data.get("kfifUrl")
        )


@dataclass
class Security:
    """Security information"""
    isin: str
    isin_desc: str
    borsa_kodu: str
    takas_kodu: str
    tertip_group: Optional[str] = None
    capital: Optional[float] = None
    current_capital: Optional[float] = None
    group_code: Optional[str] = None
    group_code_desc: Optional[str] = None
    borsada_isleme_acik: Optional[bool] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Security':
        """Create from dictionary"""
        return cls(
            isin=data.get("isin"),
            isin_desc=data.get("isinDesc"),
            borsa_kodu=data.get("borsaKodu"),
            takas_kodu=data.get("takasKodu"),
            tertip_group=data.get("tertipGroup"),
            capital=data.get("capital"),
            current_capital=data.get("currentCapital"),
            group_code=data.get("groupCode"),
            group_code_desc=data.get("groupCodeDesc"),
            borsada_isleme_acik=data.get("borsadaIslemeAcik")
        )


@dataclass
class Member:
    """Member basic information"""
    id: str
    member_type: str
    sermaye_sistemi: str
    sirket_unvan: str
    kayitli_sermaye_tavani: Optional[float] = None
    kst_son_gecerlilik_tarihi: Optional[str] = None
    mks_mbr_id: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Member':
        """Create from dictionary"""
        return cls(
            id=data.get("id"),
            member_type=data.get("memberType"),
            sermaye_sistemi=data.get("sermayeSistemi"),
            sirket_unvan=data.get("sirketUnvan"),
            kayitli_sermaye_tavani=data.get("kayitliSermayeTavani"),
            kst_son_gecerlilik_tarihi=data.get("kstSonGecerlilikTarihi"),
            mks_mbr_id=data.get("mksMbrId")
        )


@dataclass
class MemberSecuritiesResponse:
    """Member securities response"""
    member: Member
    securities: List[Security]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemberSecuritiesResponse':
        """Create from dictionary"""
        return cls(
            member=Member.from_dict(data.get("member", {})),
            securities=[Security.from_dict(s) for s in data.get("securities", [])]
        )


@dataclass
class FundInfo:
    """Fund information"""
    fund_id: int
    fund_name: str
    fund_code: str
    fund_type: str
    fund_class: str
    fund_expiry: str
    fund_state: str
    kap_url: str
    non_inactive_count: int
    fund_company_id: str
    fund_company_title: str
    umb_member_types: Optional[str] = None
    fund_member_types: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FundInfo':
        """Create from dictionary"""
        return cls(
            fund_id=data.get("fundId"),
            fund_name=data.get("fundName"),
            fund_code=data.get("fundCode"),
            fund_type=data.get("fundType"),
            fund_class=data.get("fundClass"),
            fund_expiry=data.get("fundExpiry"),
            fund_state=data.get("fundState"),
            kap_url=data.get("kapUrl"),
            non_inactive_count=data.get("nonInactiveCount"),
            fund_company_id=data.get("fundCompanyId"),
            fund_company_title=data.get("fundCompanyTitle"),
            umb_member_types=data.get("umbMemberTypes"),
            fund_member_types=data.get("fundMemberTypes")
        )


@dataclass
class BlockedDisclosure:
    """Blocked/removed disclosure information"""
    blocked_type: str
    sender_title: str
    behalf_sender_title: str
    disclosure_index: int
    is_blocked_description_tr: Optional[str] = None
    is_blocked_description_en: Optional[str] = None
    attachment_urls: Optional[List[AttachmentUrl]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BlockedDisclosure':
        """Create from dictionary"""
        attachment_urls = None
        if data.get("attachmentUrls"):
            attachment_urls = [AttachmentUrl.from_dict(a) for a in data["attachmentUrls"]]
        
        return cls(
            blocked_type=data.get("blockedType"),
            sender_title=data.get("senderTitle"),
            behalf_sender_title=data.get("behalfSenderTitle"),
            disclosure_index=data.get("disclosureIndex"),
            is_blocked_description_tr=data.get("isBlockedDescriptionTr"),
            is_blocked_description_en=data.get("isBlockedDescriptionEn"),
            attachment_urls=attachment_urls
        )


@dataclass
class CAProcessStatus:
    """Corporate action process status"""
    ref_id: int
    status: str
    complete_date: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CAProcessStatus':
        """Create from dictionary"""
        return cls(
            ref_id=data.get("refId"),
            status=data.get("status"),
            complete_date=data.get("completeDate")
        )
    
    @property
    def status_text(self) -> str:
        """Get status text in Turkish"""
        status_map = {
            "DV": "Devam Ediyor",
            "TM": "Tamamlandı",
            "YM": "Yapılmadı",
            "IP": "İptal"
        }
        return status_map.get(self.status, self.status)


# Enums and Constants
class DisclosureClass:
    """Disclosure class constants"""
    FR = "FR"  # Finansal Rapor Bildirimi
    ODA = "ODA"  # Özel Durum Açıklaması Bildirimi
    DG = "DG"  # Diğer Bildirim
    DUY = "DUY"  # Düzenleyici Kurum Bildirimi


class DisclosureType:
    """Disclosure type constants"""
    FR = "FR"  # Finansal Rapor Bildirimi
    ODA = "ODA"  # Özel Durum Açıklaması Bildirimi
    DG = "DG"  # Diğer Bildirim
    DUY = "DUY"  # Düzenleyici Kurum Bildirimi
    FON = "FON"  # Fon Bildirimi
    CA = "CA"  # Hak Kullanım Bildirimi


class MemberType:
    """Member type constants"""
    IGS = "IGS"  # İşlem Gören Şirket
    IGMS = "IGMS"  # İşlem Görmeyen Şirket
    YK = "YK"  # Yatırım Kuruluşu
    PYS = "PYS"  # Portföy Yönetim Şirketi
    DDK = "DDK"  # Düzenleyici Denetleyici Kurum
    FK = "FK"  # Fon Kurucu -Temsilci
    BDK = "BDK"  # Bağımsız Denetim Kuruluşu
    DCS = "DCS"  # Derecelendirme Şirketi
    DS = "DS"  # Değerlendirme Şirketi
    DG = "DG"  # Diğer


class FundState:
    """Fund state constants"""
    ACTIVE = "Y"  # Aktif
    PASSIVE = "N"  # Pasif
    LIQUIDATION = "T"  # Tasfiye


class FundType:
    """Fund type constants"""
    SYF = "SYF"  # Şemsiye Yatırım Fonu
    KGF = "KGF"  # Koruma Amaçlı - Garantili Şemsiye Yatırım Fonu
    EYF = "EYF"  # Emeklilik Yatırım Fonu
    OKS = "OKS"  # OKS Emeklilik Yatırım Fonu
    YYF = "YYF"  # Yabancı Yatırım Fonu
    BYF = "BYF"  # Borsa Yatırım Fonu
    VFF = "VFF"  # Varlık Finansman Fonları
    KFF = "KFF"  # Konut Finansman Fonları
    GMF = "GMF"  # Gayrimenkul Yatırım Fonları
    GSF = "GSF"  # Girişim Sermayesi Yatırım Fonu
    PFF = "PFF"  # Proje Finansman Fonu
