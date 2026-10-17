# Rise or Crouch

**Deve mi, cüce mi?** Liderin komutuna göre ekranı kaydırarak kalk (DEVE) ya da
eğil (CÜCE). Flutter ve [Flame 3D](https://pub.dev/packages/flame_3d) ile yapılmış,
9 bölümlük 3D refleks oyunu.

- Yukarı kaydır: **DEVE** (ayağa kalk)
- Aşağı kaydır: **CÜCE** (eğil)

Yanlış hareket edersen ya da geç kalırsan bir can gider. Sıradaki rakipler de
hata yapıp elenir; elenen her oyuncu iki yandaki kapılardan birine yürüyüp
kaybolur. Son bölümde yanında kimse kalmayınca oyunu kazanırsın.

## Bölümler

Her bölüm kendi sahnesinde geçer ve yeni bir kural getirir.

| # | Bölüm | Yeni kural |
|---|---|---|
| 1 | Orman | Temel DEVE / CÜCE |
| 2 | Zindan | Daha hızlı tempo |
| 3 | Karlı Vadi | **Kandırma:** lider söylediğinin tersini yapabilir |
| 4 | Korsan Koyu | **SABİT KAL!** ve ters kontroller |
| 5 | Perili Mezarlık | Rakipler ekranı **kör eder** |
| 6 | Şehir Sokağı | Ters kontrol ve körleme bir arada |
| 7 | Restoran | Rakipler **laf sokar** |
| 8 | Fabrika | **Çift komut:** "DEVE, CÜCE!" sırayla |
| 9 | Ortaçağ Kalesi | Final: hepsinden biraz; son kalan kazanır |

İlk üç bölümde kimse elenmez; 4–8. bölümlerde rakipler birer birer elenir ve
son bölüme 1–2 rakiple girilir.

## Mağaza

Bölüm bitirince kazanılan altınla:

- **Ekstra Can:** her bölüme bir can fazlasıyla başlanır.
- **Kör Et (ayna):** dokununca lider 4 sn kör olur; bu sürede hatalar sayılmaz.
- **Kalkan:** dokununca 15 sn rakiplerin körleme, ters kontrol ve laf sokmalarına karşı korur.

## Diller

Türkçe, English, Español, Português, Français, Deutsch, Italiano, Русский,
العربية (sağdan sola), हिन्दी, 日本語, 한국어, 中文.

## Çalıştırma

Gerekenler: [Flutter](https://docs.flutter.dev/get-started/install) (3.47 ya da üstü)
ve bir Android telefon ya da emülatör.

```bash
flutter pub get
flutter run --release
```

> Oyun 3D olduğu için **gerçek telefonda `--release` ile** denenmeli. Debug modunda
> ya da emülatörde belirgin şekilde yavaş çalışır.

Testler:

```bash
flutter test
```

## Proje yapısı

```
lib/
  main.dart                 Uygulamanın başlangıcı ve oyun üstü ekranlar
  game/
    data/                   Oyuncu profili (kayıt), karakterler, mağaza ürünleri
    l10n/strings.dart       13 dilde bütün metinler
    level_design/           Bölüm ayarları (levels.dart), gökyüzü, kar, kapılar
    logic/                  Oyun kuralları, karakterler, kamera, ekran göstergeleri (HUD)
    ui/                     Menü sayfaları, butonlar, oyun içi paneller
    viewmodel/              Arayüzün dinlediği menü ve mağaza ViewModel'leri
assets/
  audio/                    Müzik ve buzzer sesi
  images/                   İkonlar ve oyuncu portreleri
  models/                   Bölüm sahneleri, karakterler, lider, kapı (glTF)
test/                       Bölüm ve eleme planı testleri
tools/                      Sahneleri ve karakterleri üreten Blender / Python scriptleri
```

Mimari MVVM'e yakındır: `PlayerProfile` (model) kalıcı bilgileri tutar, oyun
mantığı `RiseCrouchGame`'de çalışır, arayüz yalnızca `MenuViewModel` ve
`ShopViewModel`'i dinler.

### Sahneleri yeniden üretmek (isteğe bağlı)

Bölüm sahneleri `tools/build_*.py` scriptleriyle Blender'da kurulur ve
`tools/export_scene.py` ile `assets/models/levels/` altına aktarılır. Bunun için
gereken kaynak modeller (`tools/source_models/`, ~120 MB) depoya konmamıştır;
oyunu çalıştırmak için gerekmez.

## Krediler

3D modellerin kaynakları ve lisansları için [CREDITS.md](CREDITS.md) dosyasına bakın.
