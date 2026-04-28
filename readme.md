Kullanım akışı
1
Browser session aç
2
Prompt çalıştır
3
Yanlış selector çıktıysa:
Selector Picker Başlat
browser penceresinde doğru elementi tıkla
geri gelip Seçilen Selector'ü Oku
4
Sonra:
kategori key yaz
action index yaz
Seçilen Selector'ü Config'e Uygula
5
Sonra:
Düzeltilmiş Config'i Çalıştır

Beklenen örnek
Örneğin Login_Credentials içindeki ilk action’a selector uygulamak istiyorsan:
Kategori Key: Login_Credentials
Action Index: 0
password action için:
Kategori Key: Login_Credentials
Action Index: 1
login click için:
Kategori Key: Login_Submit
Action Index: 0

-----------------------------------------------------------------
Uçtan uca akış kurarken
Akış Oluşturma Modu → Mevcut flow config üzerine ekle
İş bittiğinde
Flow Config'i Kaydet
Yeni bir otomasyon başlatırken
Yeni Akış Başlat
Önceki bir akışı tekrar açmak için
Flow Config Yükle

--------------------------------------------------------------------
Kullanım örneği
Diyelim şu action başarısız oldu:
Login_Submit / #0 / click / Giriş yap butonuna tıkla
Akış:
Selector picker ile doğru butonu seç
Selector’ü action’a uygula
“Tekrar Çalıştırılacak Action” dropdown’ından bunu seç
Seçilen Action'ı Tekrar Çalıştır
Bu şekilde sadece bozulan adımı test edersin.