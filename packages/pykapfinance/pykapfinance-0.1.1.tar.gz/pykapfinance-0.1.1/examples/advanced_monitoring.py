"""
PyKAP - İleri Seviye Örnek: Bildirim Takip Sistemi
Belirli kriterlere göre bildirimleri takip et ve filtrele
"""

from pykap import KAPClient
from pykap.models import DisclosureType, DisclosureClass
import json
from datetime import datetime
from typing import List, Dict


class DisclosureMonitor:
    """Bildirim takip sistemi"""
    
    def __init__(self, test_mode: bool = True):
        """
        Args:
            test_mode: Test ortamı kullan
        """
        self.client = KAPClient(test_mode=test_mode)
        self.last_checked_index = None
        
    def get_new_disclosures(self, keywords: List[str] = None) -> List[Dict]:
        """
        Yeni bildirimleri kontrol et ve filtrele
        
        Args:
            keywords: Arama anahtar kelimeleri
            
        Returns:
            Filtrelenmiş bildirimler
        """
        # Son bildirim indeksini al
        current_index = self.client.get_last_disclosure_index()
        
        # İlk çalıştırmada başlangıç noktası belirle
        if self.last_checked_index is None:
            self.last_checked_index = current_index - 50
        
        # Yeni bildirimleri al
        new_disclosures = []
        
        if current_index > self.last_checked_index:
            disclosures = self.client.get_disclosures(
                disclosure_index=self.last_checked_index + 1
            )
            
            # Anahtar kelime filtresi uygula
            if keywords:
                for disclosure in disclosures:
                    title_lower = disclosure.title.lower()
                    if any(keyword.lower() in title_lower for keyword in keywords):
                        new_disclosures.append({
                            'index': disclosure.disclosure_index,
                            'title': disclosure.title,
                            'type': disclosure.disclosure_type,
                            'class': disclosure.disclosure_class,
                            'company_id': disclosure.company_id
                        })
            else:
                new_disclosures = [{
                    'index': d.disclosure_index,
                    'title': d.title,
                    'type': d.disclosure_type,
                    'class': d.disclosure_class,
                    'company_id': d.company_id
                } for d in disclosures]
            
            # Son kontrol edilen indeksi güncelle
            self.last_checked_index = current_index
        
        return new_disclosures
    
    def monitor_company_disclosures(
        self, 
        stock_code: str, 
        disclosure_types: List[str] = None
    ) -> List[Dict]:
        """
        Belirli bir şirketin bildirimlerini takip et
        
        Args:
            stock_code: Hisse kodu
            disclosure_types: Bildirim tipleri filtresi
            
        Returns:
            Şirket bildirimleri
        """
        # Şirketi bul
        company = self.client.get_company_by_stock_code(stock_code)
        
        if not company:
            return []
        
        # Şirket bildirimlerini al
        disclosures = self.client.search_disclosures_by_company(
            company_id=company.id
        )
        
        results = []
        
        for disclosure in disclosures:
            # Tip filtresi uygula
            if disclosure_types and disclosure.disclosure_type not in disclosure_types:
                continue
            
            results.append({
                'index': disclosure.disclosure_index,
                'title': disclosure.title,
                'type': disclosure.disclosure_type,
                'class': disclosure.disclosure_class
            })
        
        return results
    
    def get_disclosure_with_attachments(self, start_index: int, count: int = 50) -> List[Dict]:
        """
        Ekli bildirimleri bul
        
        Args:
            start_index: Başlangıç indeksi
            count: Kontrol edilecek bildirim sayısı
            
        Returns:
            Ekli bildirimler
        """
        results = []
        
        # Bildirimleri al
        disclosures = self.client.get_disclosures(disclosure_index=start_index)
        
        for disclosure in disclosures[:count]:
            try:
                # Detayı al
                detail = self.client.get_disclosure_detail(
                    disclosure_index=int(disclosure.disclosure_index),
                    file_type="data"
                )
                
                # Ek varsa listeye ekle
                if detail.attachment_urls:
                    results.append({
                        'index': detail.disclosure_index,
                        'title': disclosure.title,
                        'attachments': [
                            {
                                'name': att.file_name,
                                'url': att.url
                            } for att in detail.attachment_urls
                        ]
                    })
            except Exception as e:
                print(f"Hata (Index: {disclosure.disclosure_index}): {e}")
                continue
        
        return results


def example_keyword_monitoring():
    """Örnek: Anahtar kelime ile bildirim takibi"""
    print("\n" + "="*70)
    print("ANAHTAR KELİME İLE BİLDİRİM TAKİBİ")
    print("="*70 + "\n")
    
    monitor = DisclosureMonitor(test_mode=True)
    
    # Aranacak anahtar kelimeler
    keywords = ["birleşme", "devir", "satın alma", "temettü"]
    
    print(f"🔍 Anahtar kelimeler: {', '.join(keywords)}")
    print("📊 Yeni bildirimler kontrol ediliyor...\n")
    
    # Yeni bildirimleri kontrol et
    new_disclosures = monitor.get_new_disclosures(keywords=keywords)
    
    if new_disclosures:
        print(f"✓ {len(new_disclosures)} adet eşleşen bildirim bulundu:\n")
        
        for i, disclosure in enumerate(new_disclosures, 1):
            print(f"{i}. [{disclosure['type']}] {disclosure['title']}")
            print(f"   Index: {disclosure['index']}\n")
    else:
        print("Eşleşen yeni bildirim bulunamadı")


def example_company_monitoring():
    """Örnek: Şirket bildirimi takibi"""
    print("\n" + "="*70)
    print("ŞİRKET BİLDİRİMİ TAKİBİ")
    print("="*70 + "\n")
    
    monitor = DisclosureMonitor(test_mode=True)
    
    stock_code = "THYAO"
    disclosure_types = [DisclosureType.ODA, DisclosureType.FR]
    
    print(f"🏢 Şirket: {stock_code}")
    print(f"📋 Filtre: {', '.join(disclosure_types)}\n")
    
    # Şirket bildirimlerini al
    disclosures = monitor.monitor_company_disclosures(
        stock_code=stock_code,
        disclosure_types=disclosure_types
    )
    
    if disclosures:
        print(f"✓ {len(disclosures)} bildirim bulundu:\n")
        
        # Tip bazında grupla
        by_type = {}
        for d in disclosures:
            dtype = d['type']
            by_type[dtype] = by_type.get(dtype, 0) + 1
        
        print("Bildirim Tipleri:")
        for dtype, count in by_type.items():
            print(f"  - {dtype}: {count} adet")
        
        print("\nİlk 10 Bildirim:")
        for i, disclosure in enumerate(disclosures[:10], 1):
            print(f"{i}. [{disclosure['type']}] {disclosure['title']}")
            print(f"   Index: {disclosure['index']}\n")
    else:
        print("Bildirim bulunamadı")


def example_attachment_finder():
    """Örnek: Ekli bildirimleri bul"""
    print("\n" + "="*70)
    print("EKLİ BİLDİRİMLER")
    print("="*70 + "\n")
    
    monitor = DisclosureMonitor(test_mode=True)
    
    # Son bildirim indeksini al
    client = KAPClient(test_mode=True)
    last_index = client.get_last_disclosure_index()
    
    print(f"📎 Ekli bildirimler aranıyor (Son 30 bildirim)...\n")
    
    # Ekli bildirimleri bul
    with_attachments = monitor.get_disclosure_with_attachments(
        start_index=last_index - 30,
        count=30
    )
    
    if with_attachments:
        print(f"✓ {len(with_attachments)} adet ekli bildirim bulundu:\n")
        
        for i, disclosure in enumerate(with_attachments, 1):
            print(f"{i}. {disclosure['title']}")
            print(f"   Index: {disclosure['index']}")
            print(f"   Ekler ({len(disclosure['attachments'])} adet):")
            
            for att in disclosure['attachments']:
                print(f"     - {att['name']}")
            
            print()
    else:
        print("Ekli bildirim bulunamadı")


def example_multi_company_comparison():
    """Örnek: Çoklu şirket karşılaştırmalı analiz"""
    print("\n" + "="*70)
    print("ÇOKLU ŞİRKET KARŞILAŞTIRMALI ANALİZ")
    print("="*70 + "\n")
    
    monitor = DisclosureMonitor(test_mode=True)
    
    # Analiz edilecek şirketler
    companies = ["THYAO", "EREGL", "AKBNK", "GARAN", "TCELL"]
    
    print(f"🏢 Analiz edilen şirketler: {', '.join(companies)}\n")
    
    results = {}
    
    for stock_code in companies:
        print(f"📊 {stock_code} analiz ediliyor...")
        
        disclosures = monitor.monitor_company_disclosures(stock_code=stock_code)
        
        if disclosures:
            # İstatistikleri hesapla
            stats = {
                'total': len(disclosures),
                'by_type': {}
            }
            
            for d in disclosures:
                dtype = d['type']
                stats['by_type'][dtype] = stats['by_type'].get(dtype, 0) + 1
            
            results[stock_code] = stats
            print(f"  ✓ {stats['total']} bildirim\n")
        else:
            print(f"  ✗ Bildirim bulunamadı\n")
    
    # Karşılaştırma tablosu
    print("\n" + "="*70)
    print("KARŞILAŞTIRMA TABLOSU")
    print("="*70 + "\n")
    
    print(f"{'Hisse':<10} {'Toplam':<10} {'ODA':<8} {'FR':<8} {'DG':<8} {'CA':<8}")
    print("-" * 70)
    
    for stock_code, stats in results.items():
        by_type = stats['by_type']
        print(f"{stock_code:<10} "
              f"{stats['total']:<10} "
              f"{by_type.get('ODA', 0):<8} "
              f"{by_type.get('FR', 0):<8} "
              f"{by_type.get('DG', 0):<8} "
              f"{by_type.get('CA', 0):<8}")
    
    print()


def example_export_to_json():
    """Örnek: Bildirimleri JSON dosyasına aktar"""
    print("\n" + "="*70)
    print("BİLDİRİMLERİ JSON'A AKTARMA")
    print("="*70 + "\n")
    
    monitor = DisclosureMonitor(test_mode=True)
    
    stock_code = "THYAO"
    
    print(f"📥 {stock_code} bildirimleri JSON'a aktarılıyor...\n")
    
    # Bildirimleri al
    disclosures = monitor.monitor_company_disclosures(
        stock_code=stock_code,
        disclosure_types=[DisclosureType.ODA]
    )
    
    if disclosures:
        # JSON dosyasına yaz
        filename = f"{stock_code}_disclosures.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(disclosures, f, ensure_ascii=False, indent=2)
        
        print(f"✓ {len(disclosures)} bildirim '{filename}' dosyasına aktarıldı")
        print(f"  Dosya boyutu: {len(json.dumps(disclosures))} byte\n")
    else:
        print("Aktarılacak bildirim bulunamadı")


def main():
    """Ana program"""
    
    print("\n" + "="*70)
    print("PYKAP - İLERİ SEVİYE KULLANIM ÖRNEKLERİ")
    print("="*70)
    
    # Tüm örnekleri çalıştır
    example_keyword_monitoring()
    example_company_monitoring()
    example_attachment_finder()
    example_multi_company_comparison()
    example_export_to_json()
    
    print("\n" + "="*70)
    print("TÜM ÖRNEKLER TAMAMLANDI")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
