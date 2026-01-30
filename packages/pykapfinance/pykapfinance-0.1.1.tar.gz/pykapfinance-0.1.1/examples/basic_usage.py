"""
PyKAP Temel Kullanım Örnekleri
Bu dosya PyKAP kütüphanesinin temel kullanımını gösterir.
"""

from pykap import KAPClient
from pykap.models import DisclosureType, DisclosureClass, MemberType
from pykap.exceptions import KAPAPIError, KAPValidationError
import json


def example_1_basic_usage():
    """Örnek 1: Temel Kullanım"""
    print("\n" + "="*60)
    print("ÖRNEK 1: Temel Kullanım")
    print("="*60)
    
    # Test ortamı için client oluştur
    client = KAPClient(test_mode=True)
    
    # Son bildirim indeksini al
    last_index = client.get_last_disclosure_index()
    print(f"\n✓ Son bildirim indeksi: {last_index}")
    
    # Bildirimleri listele
    print("\n✓ Son 5 bildirim:")
    disclosures = client.get_disclosures(disclosure_index=last_index - 10)
    
    for disclosure in disclosures[:5]:
        print(f"  - [{disclosure.disclosure_index}] {disclosure.title}")
        print(f"    Tip: {disclosure.disclosure_type}, Sınıf: {disclosure.disclosure_class}")


def example_2_company_search():
    """Örnek 2: Şirket Arama ve Bilgileri"""
    print("\n" + "="*60)
    print("ÖRNEK 2: Şirket Arama")
    print("="*60)
    
    client = KAPClient(test_mode=True)
    
    # Hisse koduna göre şirket bul
    stock_code = "THYAO"
    print(f"\n✓ '{stock_code}' hisse kodu aranıyor...")
    
    company = client.get_company_by_stock_code(stock_code)
    
    if company:
        print(f"\n  Şirket Bulundu:")
        print(f"  - Ünvan: {company.title}")
        print(f"  - ID: {company.id}")
        print(f"  - Hisse Kodu: {company.stock_code}")
        print(f"  - Tip: {company.member_type}")
        if company.kfif_url:
            print(f"  - KFIF URL: {company.kfif_url}")
    else:
        print(f"  ✗ Şirket bulunamadı")


def example_3_disclosure_detail():
    """Örnek 3: Bildirim Detayı ve Ekleri"""
    print("\n" + "="*60)
    print("ÖRNEK 3: Bildirim Detayı")
    print("="*60)
    
    client = KAPClient(test_mode=True)
    
    # Önce bir bildirim bul
    disclosures = client.get_disclosures(disclosure_index=1200000)
    
    if disclosures:
        disclosure_index = disclosures[0].disclosure_index
        print(f"\n✓ Bildirim detayı alınıyor: {disclosure_index}")
        
        try:
            detail = client.get_disclosure_detail(
                disclosure_index=int(disclosure_index),
                file_type="data"
            )
            
            print(f"\n  Bildirim Detayları:")
            print(f"  - Gönderen: {detail.sender_title}")
            print(f"  - Konu (TR): {detail.subject.tr if detail.subject else 'N/A'}")
            print(f"  - Özet (TR): {detail.summary.tr if detail.summary else 'N/A'}")
            print(f"  - Yayın Zamanı: {detail.time}")
            print(f"  - Link: {detail.link}")
            
            # Ekler varsa listele
            if detail.attachment_urls:
                print(f"\n  Ekler ({len(detail.attachment_urls)} adet):")
                for i, attachment in enumerate(detail.attachment_urls, 1):
                    print(f"    {i}. {attachment.file_name}")
            else:
                print("\n  Ek dosya bulunmuyor")
                
        except KAPAPIError as e:
            print(f"  ✗ Hata: {e}")


def example_4_company_disclosures():
    """Örnek 4: Şirkete Özel Bildirimleri Listeleme"""
    print("\n" + "="*60)
    print("ÖRNEK 4: Şirkete Özel Bildirimler")
    print("="*60)
    
    client = KAPClient(test_mode=True)
    
    # Bir şirket bul
    company = client.get_company_by_stock_code("EREGL")
    
    if company:
        print(f"\n✓ {company.title} için bildirimler aranıyor...")
        
        try:
            disclosures = client.search_disclosures_by_company(
                company_id=company.id,
                disclosure_type=DisclosureType.ODA
            )
            
            print(f"\n  Bulunan {len(disclosures)} Özel Durum Açıklaması:")
            for disclosure in disclosures[:5]:
                print(f"  - [{disclosure.disclosure_index}] {disclosure.title}")
                
        except KAPAPIError as e:
            print(f"  ✗ Hata: {e}")


def example_5_funds():
    """Örnek 5: Fon Bilgileri"""
    print("\n" + "="*60)
    print("ÖRNEK 5: Fon Bilgileri")
    print("="*60)
    
    client = KAPClient(test_mode=True)
    
    # Aktif fonları listele
    print("\n✓ Aktif fonlar listeleniyor...")
    funds = client.get_funds(fund_state=["Y"])  # Y = Aktif
    
    print(f"\n  Toplam {len(funds)} aktif fon bulundu")
    print("\n  İlk 5 Fon:")
    for fund in funds[:5]:
        print(f"  - {fund.fund_name}")
        print(f"    Kod: {fund.fund_code}, Tip: {fund.fund_type}, Sınıf: {fund.fund_class}")


def example_6_member_securities():
    """Örnek 6: Menkul Kıymet Bilgileri"""
    print("\n" + "="*60)
    print("ÖRNEK 6: Menkul Kıymet Bilgileri")
    print("="*60)
    
    client = KAPClient(test_mode=True)
    
    print("\n✓ Şirket menkul kıymet bilgileri alınıyor...")
    securities = client.get_member_securities()
    
    print(f"\n  Toplam {len(securities)} şirketin menkul kıymet bilgisi")
    print("\n  İlk 3 Şirket:")
    
    for item in securities[:3]:
        print(f"\n  {item.member.sirket_unvan}")
        print(f"  Sermaye Sistemi: {item.member.sermaye_sistemi}")
        
        if item.securities:
            print(f"  Menkul Kıymetler ({len(item.securities)} adet):")
            for security in item.securities[:2]:
                print(f"    - {security.isin_desc}")
                print(f"      ISIN: {security.isin}, Borsa Kodu: {security.borsa_kodu}")


def example_7_blocked_disclosures():
    """Örnek 7: Bloklanmış Bildirimler"""
    print("\n" + "="*60)
    print("ÖRNEK 7: Bloklanmış Bildirimler")
    print("="*60)
    
    client = KAPClient(test_mode=True)
    
    print("\n✓ Erişime kapatılmış bildirimler listeleniyor...")
    blocked = client.get_blocked_disclosures()
    
    print(f"\n  Toplam {len(blocked)} bloklanmış bildirim")
    
    if blocked:
        print("\n  İlk 3 Bloklanmış Bildirim:")
        for item in blocked[:3]:
            print(f"\n  - Bildirim ID: {item.disclosure_index}")
            print(f"    Şirket: {item.sender_title}")
            print(f"    Tip: {item.blocked_type}")
            print(f"    Neden: {item.is_blocked_description_tr or 'Belirtilmemiş'}")


def example_8_corporate_actions():
    """Örnek 8: Hak Kullanım Süreç Durumu"""
    print("\n" + "="*60)
    print("ÖRNEK 8: Hak Kullanım Süreç Durumu")
    print("="*60)
    
    client = KAPClient(test_mode=True)
    
    # Test süreç ID'leri
    process_ids = [12941, 13214]
    
    print(f"\n✓ Süreç durumları sorgulanıyor: {process_ids}")
    
    try:
        statuses = client.get_ca_event_status(process_ref_ids=process_ids)
        
        print("\n  Süreç Durumları:")
        for status in statuses:
            print(f"\n  - Süreç ID: {status.ref_id}")
            print(f"    Durum: {status.status_text} ({status.status})")
            if status.complete_date:
                print(f"    Tamamlanma: {status.complete_date}")
                
    except KAPAPIError as e:
        print(f"  ✗ Hata: {e}")


def example_9_filtering_disclosures():
    """Örnek 9: Gelişmiş Bildirim Filtreleme"""
    print("\n" + "="*60)
    print("ÖRNEK 9: Gelişmiş Bildirim Filtreleme")
    print("="*60)
    
    client = KAPClient(test_mode=True)
    
    # Finansal raporları filtrele
    print("\n✓ Finansal Raporlar filtreleniyor...")
    disclosures = client.get_disclosures(
        disclosure_index=1200000,
        disclosure_class=DisclosureClass.FR,
        disclosure_type=DisclosureType.FR
    )
    
    print(f"\n  Bulunan {len(disclosures)} Finansal Rapor")
    print("\n  İlk 5 Finansal Rapor:")
    for disclosure in disclosures[:5]:
        print(f"  - {disclosure.title}")
        print(f"    Index: {disclosure.disclosure_index}")


def example_10_context_manager():
    """Örnek 10: Context Manager Kullanımı"""
    print("\n" + "="*60)
    print("ÖRNEK 10: Context Manager Kullanımı")
    print("="*60)
    
    print("\n✓ Context manager ile otomatik kaynak yönetimi...")
    
    # Client otomatik olarak açılır ve kapanır
    with KAPClient(test_mode=True) as client:
        companies = client.get_members()
        print(f"\n  {len(companies)} şirket listelendi")
        
        # İşlemler burada yapılır
        last_index = client.get_last_disclosure_index()
        print(f"  Son bildirim indeksi: {last_index}")
    
    print("\n  ✓ Client otomatik olarak kapatıldı")


def example_11_error_handling():
    """Örnek 11: Hata Yönetimi"""
    print("\n" + "="*60)
    print("ÖRNEK 11: Hata Yönetimi")
    print("="*60)
    
    client = KAPClient(test_mode=True)
    
    print("\n✓ Geçersiz parametre testi...")
    
    try:
        # Geçersiz disclosure_index (538004'ten küçük)
        disclosures = client.get_disclosures(disclosure_index=100)
        
    except KAPValidationError as e:
        print(f"  ✓ Beklenen hata yakalandı: {e}")
    
    print("\n✓ API hata testi...")
    
    try:
        # Geçersiz file_type
        detail = client.get_disclosure_detail(
            disclosure_index=1200000,
            file_type="invalid"
        )
        
    except KAPValidationError as e:
        print(f"  ✓ Beklenen hata yakalandı: {e}")


def example_12_batch_processing():
    """Örnek 12: Toplu İşlem"""
    print("\n" + "="*60)
    print("ÖRNEK 12: Toplu İşlem")
    print("="*60)
    
    client = KAPClient(test_mode=True)
    
    print("\n✓ Belirli bir aralıktaki bildirimler alınıyor...")
    
    start_index = 1200000
    end_index = 1200100
    
    all_disclosures = []
    current_index = start_index
    
    while current_index < end_index:
        try:
            batch = client.get_disclosures(disclosure_index=current_index)
            
            if not batch:
                break
            
            all_disclosures.extend(batch)
            
            # Son bildirimin index'inden devam et
            last_disclosure_index = int(batch[-1].disclosure_index)
            
            if last_disclosure_index >= end_index:
                break
                
            current_index = last_disclosure_index + 1
            
        except KAPAPIError as e:
            print(f"  ✗ Hata: {e}")
            break
    
    print(f"\n  ✓ Toplam {len(all_disclosures)} bildirim alındı")
    
    # Tip bazında grupla
    by_type = {}
    for disclosure in all_disclosures:
        dtype = disclosure.disclosure_type
        by_type[dtype] = by_type.get(dtype, 0) + 1
    
    print("\n  Bildirim Tipleri:")
    for dtype, count in by_type.items():
        print(f"    - {dtype}: {count} adet")


def main():
    """Tüm örnekleri çalıştır"""
    print("\n" + "="*60)
    print("PYKAP - Kullanım Örnekleri")
    print("="*60)
    
    examples = [
        example_1_basic_usage,
        example_2_company_search,
        example_3_disclosure_detail,
        example_4_company_disclosures,
        example_5_funds,
        example_6_member_securities,
        example_7_blocked_disclosures,
        example_8_corporate_actions,
        example_9_filtering_disclosures,
        example_10_context_manager,
        example_11_error_handling,
        example_12_batch_processing,
    ]
    
    for i, example_func in enumerate(examples, 1):
        try:
            example_func()
        except Exception as e:
            print(f"\n  ✗ Örnek {i} çalıştırılırken hata oluştu: {e}")
    
    print("\n" + "="*60)
    print("Örnekler Tamamlandı!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
