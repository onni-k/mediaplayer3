# Soitin ja Tiedot

Päänäkymän oletusnäkymä. Näyttää mitä parhaillaan toistetaan --
paikallisia tiedostoja tai internetradioasemaa -- sekä kansikuvan,
toiston edistymisen ja tilan, sekä Soittolista-sarakkeen ja
Soitin/Tiedot-sarakkeen näiden alapuolella rinnakkain.

Paina SININEN vaihtaaksesi oikean sarakkeen Soittimen ja Tietojen
välillä; uusi painallus vaihtaa takaisin.

## Soitin

Oikean sarakkeen oma oletustila, näyttää nykyisen kappaleen
toistotilan ylimmän tietorivin ohella.

## Tiedot

Näyttää lisätietoja parhaillaan toistettavasta. Käytettävissä olevat
sivut riippuvat täysin siitä, mitä nykyisellä kappaleella tai asemalla
todella on -- tyhjää sivua ei koskaan näytetä.

Paikallisella musiikilla mahdollisia sivuja ovat Sanoitukset
(synkronoidut, upotetut tai pelkkä teksti), Metatiedot ja
Koodekkitiedot. Podcast-jaksolla, joka on toistettu Podcastit-
ruudusta, ensimmäinen sivu on Kuvaus. Internetradiolla mahdollisia sivuja ovat Radio-EPG
(nykyinen ohjelma sekä muutama seuraava, kun asemalla on
ohjelmatietoja), Soi nyt, Aseman tiedot ja Koodekkitiedot.

Kun kappale tai asema vaihtuu, paneeli näyttää viimeksi valitsemasi
sivun, jos uudella kohteella on se, ja muuten parhaan saatavilla
olevan sivun (esimerkiksi ohjelmatiedot radioasemalla, jolla on
sellaiset, tai sanoitukset kappaleella, jolla ne ovat) -- paneeli ei
jää sivulle, jota ei enää ole.

VASEN/OIKEA vaihtaa käytettävissä olevien Tiedot-sivujen välillä;
YLÖS/ALAS vierittää nykyistä sivua (tai synkronoiduissa sanoituksissa
siirtää sanoituksia aikaisemmaksi/myöhemmäksi suhteessa kappaleeseen,
jos ajoitus tuntuu hieman pielessä olevan).

## Soittolista-sarake

Vasen sarake, aina näkyvissä riippumatta siitä näyttääkö oikea
sarake Soitinta vai Tietoja. Näyttää edellisen, nykyisen ja seuraavan
kappaleen (paikallinen musiikki) tai radioaseman (internetradio),
nykyinen korostettuna.

## Näppäimet

- OK: jos mitään ei toisteta, avaa valitsimen (Internetradio /
  Paikallinen musiikki / Musiikkikirjasto / Soittolistat / Podcastit).
  Muussa tapauksessa avaa pienen valikon: Takaisin (palaa sinne mistä
  toisto aloitettiin), Pysäytä/Jatka, Peruuta -- sekä
  internetradiota kuunnellessa: Tyhjennä historia, Lisää suosikkeihin,
  Poista suosikeista, Aloita tallennus / Lopeta tallennus (tallentaa
  aseman tiedostoon; katso Huomioita).
- PLAY / PAUSE / STOP: hallitse toistoa suoraan.
- VASEN / OIKEA: siirry lyhyt askel taakse/eteen paikallisissa
  tiedostoissa (Soitin-tila), tai vaihda Tiedot-sivujen välillä
  (Tiedot-tila). Internetradiota kuunnellessa vaihtaa sen sijaan
  aktiivista suosikkilistaa, koska suoraa lähetystä ei voi kelata.
- FF / RW: siirry pidempi askel taakse/eteen (vain paikalliset
  tiedostot).
- YLÖS / ALAS: edellinen/seuraava kappale (tai edellinen/seuraava
  radioasema internetradiota kuunnellessa) Soitin-tilassa; vierittää
  nykyistä sivua Tiedot-tilassa.
- CH+ / CH-: edellinen/seuraava kappale (ei välttämättä toimi
  kaikilla kaukosäätimillä tai imageilla).
- PVR: avaa saman valitsimen kuin OK (Internetradio / Paikallinen
  musiikki / Musiikkikirjasto / Soittolistat / Podcastit).
- PUNAINEN: lisää nykyisen kappaleen soittolistalle tai poistaa sen
  sieltä, tai avaa Soittolistat-ruudun soittolistojen muokkausta
  varten.
- VIHREÄ: avaa lähdevalikon (sama kuin PVR).
- KELTAINEN: näyttää sanoitukset koko ruudulla -- tai podcast-jaksolla
  sen kuvauksen koko ruudulla (vieritys YLÖS / ALAS). KELTAINEN, OK tai
  EXIT sulkee koko ruudun näkymän.
- SININEN: vaihtaa paneelia Soitin-tilan ja Tiedot-tilan välillä.
- EPG / INFO: avaa tämän ohjeen.
- MENU: avaa asetukset.
- HELP: näytä kaukosäätimen näppäinopas.
- EXIT: pysäyttää toiston; uusi painallus sulkee MediaPlayer3:n ja
  palaa suoraan lähetykseen.

## Huomioita

Radiotallennus: Aloita tallennus kopioi toistettavan aseman lähetyksen
tiedostoon (nimi VVVV-KK-PP-hh.mm_kanava) asetuksissa valittuun
tallennuskansioon ja lisää sen "Tallennukset (Radio)" -soittolistalle
tallennuksen päätyttyä. Tallennus päättyy, kun vaihdat asemaa,
pysäytät toiston tai suljet MediaPlayer3:n. Tallennuksen aikana
tilarivillä näkyy REC ja kulunut aika.

HLS (.m3u8) -asemat voi myös tallentaa; ääni tallentuu tavalliseksi
.aac / .mp3 -tiedostoksi. Salattuja lähetyksiä ei voi tallentaa.

Tunnista kappale: OK-valikon Tunnista kappale ottaa näytteen soivasta
kanavasta (tai tiedostosta) ja hakee tiedot AcoustID-palvelusta. Se
käyttää pluginin mukana tulevaa sormenjälkityökalua ja tarvitsee
vastaanottimessa äänidekooderin (ffmpeg tai gst-launch-1.0). Mukana tulevaa
AcoustID-avainta käytetään, ellet anna omaa avainta asetuksissa.

Radion ajansiirto: soiva asema puskuroidaan levylle (tallennuskansioon),
jolloin kokonaisaika kasvaa ja jäljellä oleva aika näyttää viiveen
livestä. PAUSE pysäyttää toiston, kelauspainikkeet (FF / RW) liikkuvat
puskurissa ja OK-valikon "Siirry live-tilaan" palaa suoraan lähetykseen.
Tallennuksen aloitus viiveen ollessa päällä kysyy, tallennetaanko
ajansiirron alusta vai nykyisestä kohdasta. Toiminnon voi poistaa
käytöstä ja pituutta muuttaa asetuksista (Radion ajansiirto, Ajansiirron
pituus).

Internetradioasemat jatkuvat automaattisesti viimeisimmästä
historiamerkinnästä, kun valitset Internetradion aloitusvalitsimesta.
Jos historiaa ei ole, käytetään "General"-suosikkilistaa, ja viimeisenä
vaihtoehtona avataan asemahaku.

Podcast-jaksolla, joka on toistettu Podcastit-ruudusta, ylin
tietoruutu näyttää podcastin nimen ja sen alla jakson nimen.

Ylin tietorivi näyttää paikallisilla tiedostoilla nykyisen kappaleen
tunnistetiedot, ja internetradiolla aseman Now Playing -tiedot silloin
kun ne ovat saatavilla. Jos kyseiseltä asemalta ei saada
soi nyt -tietoa, näytetään pelkkä aseman nimi.
