"""
PyKAP - Hisse Analizi Örneği
Belirli bir hisse senedi için detaylı analiz
"""

from pykap import KAPClient
from pykap.models import DisclosureType
from collections import defaultdict
from datetime import datetime


def analyze_stock(stock_code: str):
    """
    Belirli bir hisse senedi için detaylı analiz yap
    
    Args:
        stock_code: Hisse kodu (örn: 'THYAO', 'EREGL')
    """
    print(f"\n{'='*70}")
    print(f"HİSSE ANALİZİ: {stock_code}")
    print(f"{'='*70}\n")
    
    client = KAPClient(test_mode=True)
    
    # 1. Şirket bilgilerini al
    print(f"[1/5] Şirket bilgileri alınıyor...")
    company = client.get_company_by_stock_code(stock_code)
    
    if not company:
        print(f"✗ '{stock_code}' hisse kodu bulunamadı!")
        return
    
    print(f"✓ Şirket bulundu: {company.title}")
    print(f"  - ID: {company.id}")
    print(f"  - Tip: {company.member_type}")
    print(f"  - Hisse Kodu: {company.stock_code}\n")
    
    # 2. Son bildirimleri al
    print(f"[2/5] Son bildirimler alınıyor...")
    try:
        disclosures = client.search_disclosures_by_company(
            company_id=company.id
        )
        
        print(f"✓ {len(disclosures)} bildirim bulundu\n")
        
        # 3. Bildirimleri tipe göre grupla
        print(f"[3/5] Bildirimler analiz ediliyor...")
        disclosure_stats = defaultdict(int)
        
        for disclosure in disclosures:
            disclosure_stats[disclosure.disclosure_type] += 1
        
        print(f"✓ Bildirim İstatistikleri:")
        for dtype, count in sorted(disclosure_stats.items()):
            type_names = {
                'FR': 'Finansal Rapor',
                'ODA': 'Özel Durum Açıklaması',
                'DG': 'Diğer Bildirim',
                'DUY': 'Düzenleyici Kurum',
                'FON': 'Fon Bildirimi',
                'CA': 'Hak Kullanım'
            }
            print(f"  - {type_names.get(dtype, dtype)}: {count} adet")
        
        print()
        
        # 4. Son 10 bildirimi göster
        print(f"[4/5] Son bildirimler:")
        for i, disclosure in enumerate(disclosures[:10], 1):
            print(f"  {i}. [{disclosure.disclosure_type}] {disclosure.title}")
            print(f"     Index: {disclosure.disclosure_index}\n")
        
        # 5. Özel durum açıklamalarını detaylı göster
        print(f"[5/5] Özel Durum Açıklamaları (ODA) detaylandırılıyor...")
        
        oda_disclosures = [d for d in disclosures if d.disclosure_type == 'ODA']
        
        if oda_disclosures:
            print(f"✓ {len(oda_disclosures)} adet ODA bulundu")
            print("\nİlk 3 ODA Detayı:\n")
            
            for i, disclosure in enumerate(oda_disclosures[:3], 1):
                try:
                    detail = client.get_disclosure_detail(
                        disclosure_index=int(disclosure.disclosure_index),
                        file_type="data"
                    )
                    
                    print(f"{i}. ODA Detayı:")
                    print(f"   Konu: {detail.subject.tr if detail.subject else 'N/A'}")
                    print(f"   Özet: {detail.summary.tr if detail.summary else 'N/A'}")
                    print(f"   Tarih: {detail.time}")
                    
                    if detail.attachment_urls:
                        print(f"   Ekler: {len(detail.attachment_urls)} adet")
                        for att in detail.attachment_urls:
                            print(f"     - {att.file_name}")
                    
                    print()
                    
                except Exception as e:
                    print(f"   ✗ Detay alınamadı: {e}\n")
        else:
            print("  Özel durum açıklaması bulunamadı")
        
    except Exception as e:
        print(f"✗ Hata oluştu: {e}")
    
    print(f"\n{'='*70}")
    print(f"ANALİZ TAMAMLANDI")
    print(f"{'='*70}\n")


def compare_stocks(stock_codes: list):
    """
    Birden fazla hisse senedini karşılaştır
    
    Args:
        stock_codes: Hisse kodları listesi
    """
    print(f"\n{'='*70}")
    print(f"HİSSE KARŞILAŞTIRMA: {', '.join(stock_codes)}")
    print(f"{'='*70}\n")
    
    client = KAPClient(test_mode=True)
    
    results = {}
    
    for stock_code in stock_codes:
        print(f"📊 {stock_code} analiz ediliyor...")
        
        company = client.get_company_by_stock_code(stock_code)
        
        if not company:
            print(f"  ✗ Bulunamadı\n")
            continue
        
        try:
            disclosures = client.search_disclosures_by_company(
                company_id=company.id
            )
            
            # İstatistikleri topla
            stats = {
                'company': company.title,
                'total_disclosures': len(disclosures),
                'oda_count': len([d for d in disclosures if d.disclosure_type == 'ODA']),
                'fr_count': len([d for d in disclosures if d.disclosure_type == 'FR']),
            }
            
            results[stock_code] = stats
            
            print(f"  ✓ {stats['total_disclosures']} bildirim bulundu")
            print(f"    - ODA: {stats['oda_count']}")
            print(f"    - FR: {stats['fr_count']}\n")
            
        except Exception as e:
            print(f"  ✗ Hata: {e}\n")
    
    # Karşılaştırma tablosu
    print(f"\n{'='*70}")
    print("KARŞILAŞTIRMA TABLOSU")
    print(f"{'='*70}\n")
    
    print(f"{'Hisse':<10} {'Şirket':<35} {'Toplam':<10} {'ODA':<8} {'FR':<8}")
    print("-" * 70)
    
    for stock_code, stats in results.items():
        print(f"{stock_code:<10} {stats['company'][:35]:<35} "
              f"{stats['total_disclosures']:<10} "
              f"{stats['oda_count']:<8} "
              f"{stats['fr_count']:<8}")
    
    print()


def find_recent_financial_reports():
    """
    Son finansal raporları bul ve listele
    """
    print(f"\n{'='*70}")
    print(f"SON FİNANSAL RAPORLAR")
    print(f"{'='*70}\n")
    
    client = KAPClient(test_mode=True)
    
    print("📊 Son finansal raporlar alınıyor...")
    
    # Son bildirim indeksini al
    last_index = client.get_last_disclosure_index()
    
    # Son 200 bildirimi al ve finansal raporları filtrele
    disclosures = client.get_disclosures(
        disclosure_index=last_index - 200,
        disclosure_type=DisclosureType.FR
    )
    
    print(f"✓ {len(disclosures)} finansal rapor bulundu\n")
    
    # Şirket bazında grupla
    by_company = defaultdict(list)
    for disclosure in disclosures:
        by_company[disclosure.title].append(disclosure)
    
    print("Şirket Bazında Finansal Raporlar:\n")
    
    for i, (company, reports) in enumerate(list(by_company.items())[:10], 1):
        print(f"{i}. {company}")
        print(f"   Rapor Sayısı: {len(reports)}")
        
        for report in reports[:3]:  # İlk 3 rapor
            print(f"   - Index: {report.disclosure_index}")
        
        if len(reports) > 3:
            print(f"   ... ve {len(reports) - 3} rapor daha")
        
        print()


def main():
    """Ana program"""
    
    # Örnek 1: Tek hisse analizi
    analyze_stock("THYAO")
    
    # Örnek 2: Çoklu hisse karşılaştırması
    compare_stocks(["THYAO", "EREGL", "AKBNK"])
    
    # Örnek 3: Son finansal raporlar
    find_recent_financial_reports()


if __name__ == "__main__":
    main()
