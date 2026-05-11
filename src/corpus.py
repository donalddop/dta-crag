"""
Dutch tax law corpus.
Sources: Wet IB 2001, Wet OB 1968, Wet VPB 1969, Wet LB 1964.
Each chunk is a dict with keys: id, source, article, title, text.
"""

CORPUS: list[dict] = [
    # ── WET INKOMSTENBELASTING 2001 (IB) ─────────────────────────────────────

    {
        "id": "ib_1_1",
        "source": "Wet IB 2001",
        "article": "Art. 1.1",
        "title": "Belastingplicht binnenlandse belastingplichtigen",
        "text": (
            "Onder de naam inkomstenbelasting wordt een directe belasting geheven "
            "van natuurlijke personen. Belastingplichtig voor de inkomstenbelasting "
            "zijn de natuurlijke personen die in Nederland wonen (binnenlandse "
            "belastingplichtigen) of die niet in Nederland wonen maar wel Nederlands "
            "inkomen genieten (buitenlandse belastingplichtigen). "
            "Wie in Nederland woont, wordt bepaald naar de omstandigheden."
        ),
    },
    {
        "id": "ib_2_17",
        "source": "Wet IB 2001",
        "article": "Art. 2.17",
        "title": "Toerekening gemeenschappelijke inkomensbestanddelen",
        "text": (
            "Gemeenschappelijke inkomensbestanddelen worden in aanmerking genomen bij "
            "de belastingplichtige die daarvoor kiest. Als de belastingplichtige en "
            "zijn fiscale partner samen kiezen, kunnen zij de gemeenschappelijke "
            "inkomensbestanddelen in elke gewenste verhouding aan elkaar toerekenen. "
            "Tot de gemeenschappelijke inkomensbestanddelen behoren onder andere de "
            "belastbare inkomsten uit eigen woning, de persoonsgebonden aftrek en het "
            "belastbare inkomen uit sparen en beleggen."
        ),
    },
    {
        "id": "ib_3_1",
        "source": "Wet IB 2001",
        "article": "Art. 3.1",
        "title": "Belastbaar inkomen uit werk en woning",
        "text": (
            "Belastbaar inkomen uit werk en woning is het gezamenlijke bedrag van: "
            "het belastbare loon, het belastbare resultaat uit overige werkzaamheden, "
            "de belastbare periodieke uitkeringen en verstrekkingen, de belastbare "
            "inkomsten uit eigen woning, de negatieve uitgaven voor inkomensvoorzieningen "
            "en de negatieve persoonsgebonden aftrekposten, verminderd met de "
            "persoonsgebonden aftrek. Het tarief in box 1 is progressief en bedraagt "
            "in 2024 maximaal 49,5% voor inkomen boven € 75.518."
        ),
    },
    {
        "id": "ib_3_14",
        "source": "Wet IB 2001",
        "article": "Art. 3.14",
        "title": "Niet-aftrekbare kosten",
        "text": (
            "Bij het bepalen van de winst komen niet in aftrek: "
            "kosten en lasten die verband houden met geldboeten opgelegd door een "
            "Nederlandse strafrechter of bestuursorgaan; kosten en lasten die verband "
            "houden met misdrijven; steekpenningen; kosten van persoonlijke verzorging "
            "van de belastingplichtige; kosten van kleding, tenzij de kleding nagenoeg "
            "uitsluitend zakelijk wordt gebruikt. Gemengde kosten (kosten met zowel een "
            "zakelijk als privékarakter) zijn slechts aftrekbaar voor zover zij de "
            "wettelijke drempel overschrijden of voor het zakelijk deel."
        ),
    },
    {
        "id": "ib_3_111",
        "source": "Wet IB 2001",
        "article": "Art. 3.111",
        "title": "Eigen woning",
        "text": (
            "Een eigen woning is een gebouw of gedeelte van een gebouw met aanhorigheden, "
            "voor zover dat, anders dan tijdelijk, als hoofdverblijf ter beschikking staat "
            "aan de belastingplichtige op grond van eigendom of op grond van een recht van "
            "vruchtgebruik. Het eigenwoningforfait bedraagt in 2024 0,35% van de WOZ-waarde "
            "voor woningen met een WOZ-waarde tot € 1.200.000. Voor het meerdere bedraagt "
            "het forfait 2,35%. De hypotheekrente is aftrekbaar voor eigenwoningschulden "
            "die zijn aangegaan voor de aankoop, onderhoud of verbetering van de eigen woning."
        ),
    },
    {
        "id": "ib_4_12",
        "source": "Wet IB 2001",
        "article": "Art. 4.12",
        "title": "Aanmerkelijk belang",
        "text": (
            "Er is sprake van een aanmerkelijk belang als de belastingplichtige, alleen of "
            "samen met zijn fiscale partner, direct of indirect ten minste 5% bezit van het "
            "geplaatste kapitaal van een vennootschap met een in aandelen verdeeld kapitaal. "
            "Voordelen uit aanmerkelijk belang worden belast in box 2. Het tarief in box 2 "
            "bedraagt 24,5% voor inkomen tot € 67.000 per persoon en 33% voor het meerdere "
            "(2024). Dividenden en vervreemdingswinsten vallen onder box 2."
        ),
    },
    {
        "id": "ib_5_2",
        "source": "Wet IB 2001",
        "article": "Art. 5.2",
        "title": "Belastbaar inkomen uit sparen en beleggen (box 3)",
        "text": (
            "Het belastbaar inkomen uit sparen en beleggen is het voordeel uit sparen en "
            "beleggen verminderd met de persoonsgebonden aftrek voor zover die niet in "
            "aanmerking is genomen bij het inkomen uit werk en woning of aanmerkelijk belang. "
            "Het voordeel uit sparen en beleggen wordt bepaald op basis van een forfaitair "
            "rendement over de rendementsgrondslag (bezittingen minus schulden). "
            "Het heffingvrij vermogen in 2024 bedraagt € 57.000 per persoon. "
            "Het box 3-tarief bedraagt 36% over het berekende forfaitaire rendement. "
            "Na de Kerstarrest-uitspraak van de Hoge Raad worden belastingplichtigen die "
            "bezwaar hebben gemaakt gecompenseerd op basis van werkelijk rendement."
        ),
    },
    {
        "id": "ib_6_1",
        "source": "Wet IB 2001",
        "article": "Art. 6.1",
        "title": "Persoonsgebonden aftrek",
        "text": (
            "Persoonsgebonden aftrek is het gezamenlijke bedrag van de uitgaven voor "
            "onderhoudsverplichtingen (alimentatie), de weekenduitgaven voor gehandicapten, "
            "specifieke zorgkosten en scholingsuitgaven, giften aan Algemeen Nut Beogende "
            "Instellingen (ANBI's) en steunstichtingen SBBI, en de kosten voor monumentenpanden. "
            "Scholingsuitgaven zijn afgeschaft per 1 januari 2022 en vervangen door het "
            "STAP-budget (dat zelf per 2024 ook is beëindigd)."
        ),
    },

    # ── WET OP DE OMZETBELASTING 1968 (OB/BTW) ───────────────────────────────

    {
        "id": "ob_1",
        "source": "Wet OB 1968",
        "article": "Art. 1",
        "title": "Belastbare feiten omzetbelasting",
        "text": (
            "Omzetbelasting wordt geheven ter zake van: leveringen van goederen en diensten "
            "door ondernemers in het kader van hun onderneming; intracommunautaire verwervingen "
            "van goederen in Nederland; invoer van goederen. "
            "Ondernemer voor de btw is ieder die zelfstandig een economische activiteit verricht, "
            "ongeacht het oogmerk of resultaat. Een eenmanszaak, vof, bv en zelfs een particulier "
            "die regelmatig goederen verkoopt kan ondernemer zijn voor de btw."
        ),
    },
    {
        "id": "ob_9",
        "source": "Wet OB 1968",
        "article": "Art. 9",
        "title": "Tarieven omzetbelasting",
        "text": (
            "De belasting bedraagt 21% (algemeen tarief) van de vergoeding. "
            "Het verlaagde tarief van 9% is van toepassing op leveringen en diensten "
            "opgenomen in tabel I behorende bij de wet, waaronder: voedingsmiddelen, "
            "geneesmiddelen, boeken en tijdschriften (inclusief e-books), schilderijen en "
            "kunstwerken, kappersdiensten, fietsreparaties, en bepaalde agrarische goederen. "
            "Het nultarief (0%) geldt voor intracommunautaire leveringen, export buiten de EU, "
            "en bepaalde specifieke prestaties zoals internationaal personenvervoer."
        ),
    },
    {
        "id": "ob_11",
        "source": "Wet OB 1968",
        "article": "Art. 11",
        "title": "Vrijstellingen omzetbelasting",
        "text": (
            "Van de belasting zijn vrijgesteld: de verhuur van onroerende zaken (tenzij optie "
            "belaste verhuur); de levering van onroerende zaken na meer dan twee jaar na eerste "
            "ingebruikneming; medische diensten verricht door BIG-geregistreerden; "
            "onderwijs door erkende onderwijsinstellingen; bank- en financiële diensten; "
            "verzekeringsdiensten; diensten door componisten, schrijvers en journalisten "
            "voor hun eigen werken; en kansspelen. "
            "Een vrijgestelde ondernemer heeft geen recht op aftrek van voorbelasting."
        ),
    },
    {
        "id": "ob_15",
        "source": "Wet OB 1968",
        "article": "Art. 15",
        "title": "Aftrek van voorbelasting",
        "text": (
            "De in een tijdvak verschuldigde belasting wordt verminderd met de btw die aan "
            "de ondernemer in rekening is gebracht op facturen en die betrekking heeft op "
            "goederen en diensten die de ondernemer gebruikt voor belaste prestaties. "
            "Voorbelasting op gemengd gebruikte goederen en diensten (zowel belaste als "
            "vrijgestelde prestaties) is slechts gedeeltelijk aftrekbaar naar rato van "
            "de belaste omzet (pro rata). Privégebruik van bedrijfsmiddelen leidt tot "
            "een correctie van de aftrek."
        ),
    },
    {
        "id": "ob_25",
        "source": "Wet OB 1968",
        "article": "Art. 25 / KOR",
        "title": "Kleineondernemersregeling (KOR)",
        "text": (
            "De kleineondernemersregeling (KOR) is een vrijstelling van omzetbelasting "
            "voor ondernemers met een omzet van maximaal € 20.000 per kalenderjaar in "
            "Nederland. Bij toepassing van de KOR hoeft geen btw in rekening te worden "
            "gebracht en hoeft geen btw-aangifte te worden gedaan, maar bestaat er ook "
            "geen recht op aftrek van voorbelasting. Deelname is vrijwillig en vereist "
            "aanmelding bij de Belastingdienst. Bij overschrijding van de omzetgrens "
            "vervalt de vrijstelling per direct."
        ),
    },

    # ── WET OP DE VENNOOTSCHAPSBELASTING 1969 (VPB) ──────────────────────────

    {
        "id": "vpb_1",
        "source": "Wet VPB 1969",
        "article": "Art. 1 / 2",
        "title": "Belastingplicht vennootschapsbelasting",
        "text": (
            "Vennootschapsbelasting wordt geheven van: naamloze vennootschappen, "
            "besloten vennootschappen, coöperaties, onderlinge waarborgmaatschappijen, "
            "open commanditaire vennootschappen en andere rechtspersonen die een "
            "onderneming drijven. Buitenlandse lichamen zijn belastingplichtig voor "
            "zover zij Nederlandse bronnen van inkomen hebben. Stichtingen en "
            "verenigingen zijn alleen belastingplichtig als en voor zover zij een "
            "onderneming drijven."
        ),
    },
    {
        "id": "vpb_8",
        "source": "Wet VPB 1969",
        "article": "Art. 8 / 22",
        "title": "Tarieven vennootschapsbelasting",
        "text": (
            "De vennootschapsbelasting bedraagt in 2024: 19% over de eerste € 200.000 "
            "van het belastbare bedrag (laag tarief) en 25,8% over het meerdere "
            "(hoog tarief). Het belastbare bedrag is de winst verminderd met aftrekbare "
            "verliezen van vorige jaren. Verliesverrekening is mogelijk met de winst van "
            "het voorgaande jaar (carry back, maximaal 1 jaar, maximaal € 1 miljoen) en "
            "onbeperkt voorwaarts (carry forward), maar carry forward is boven € 1 miljoen "
            "winst beperkt tot 50% van die winst."
        ),
    },
    {
        "id": "vpb_13",
        "source": "Wet VPB 1969",
        "article": "Art. 13",
        "title": "Deelnemingsvrijstelling",
        "text": (
            "Voordelen uit hoofde van een deelneming zijn vrijgesteld van "
            "vennootschapsbelasting (deelnemingsvrijstelling). Er is sprake van een "
            "deelneming als het belang ten minste 5% bedraagt van het geplaatste kapitaal. "
            "De vrijstelling geldt voor dividenden en vervreemdingswinsten. "
            "De deelnemingsvrijstelling geldt niet voor zogenoemde 'laagbelaste "
            "beleggingsdeelnemingen', waarbij de deelneming hoofdzakelijk passieve "
            "beleggingsactiviteiten verricht en in een land is gevestigd met een "
            "effectieve belastingdruk van minder dan 10%."
        ),
    },
    {
        "id": "vpb_15",
        "source": "Wet VPB 1969",
        "article": "Art. 15",
        "title": "Fiscale eenheid vennootschapsbelasting",
        "text": (
            "Moedermaatschappijen en dochtermaatschappijen kunnen verzoeken als één "
            "belastingplichtige te worden aangemerkt (fiscale eenheid). Vereiste is dat "
            "de moeder direct of indirect ten minste 95% van de aandelen in de dochter "
            "bezit. Voordelen zijn: saldering van winsten en verliezen van verschillende "
            "groepsmaatschappijen, onderlinge transacties zijn fiscaal onzichtbaar. "
            "Nadelen: bepaalde regelingen (zoals de innovatiebox) gelden slechts voor "
            "de fiscale eenheid als geheel."
        ),
    },
    {
        "id": "vpb_20",
        "source": "Wet VPB 1969",
        "article": "Art. 20",
        "title": "Verliesverrekening vennootschapsbelasting",
        "text": (
            "Verliezen zijn te verrekenen met de belastbare winst van het voorgaande "
            "jaar (achterwaartse verliesverrekening, carry back) tot maximaal € 1 miljoen "
            "en onbeperkt met toekomstige winsten (voorwaartse verliesverrekening, "
            "carry forward). Voor carry forward geldt: bij winsten boven € 1 miljoen "
            "kan maximaal 50% van het bedrag boven die drempel worden verrekend. "
            "Bij een aandelenoverdracht van meer dan 30% kan verliesverrekening "
            "beperkt worden door de antimisbruikbepaling van art. 20a Wet VPB."
        ),
    },

    # ── WET OP DE LOONBELASTING 1964 (LB) ────────────────────────────────────

    {
        "id": "lb_1",
        "source": "Wet LB 1964",
        "article": "Art. 1 / 2",
        "title": "Belastingplicht en inhoudingsplichtige",
        "text": (
            "Loonbelasting wordt geheven van werknemers. Inhoudingsplichtig is de "
            "werkgever: degene tot wie een of meer personen in dienstbetrekking staan. "
            "Dienstbetrekking kan een echte (arbeidsovereenkomst), fictieve of "
            "vrijwillige dienstbetrekking zijn. De werkgever houdt loonbelasting in "
            "op het loon van de werknemer en draagt dit af aan de Belastingdienst. "
            "Loonbelasting is een voorheffing op de inkomstenbelasting."
        ),
    },
    {
        "id": "lb_10",
        "source": "Wet LB 1964",
        "article": "Art. 10 / 11",
        "title": "Loon en vrijgestelde aanspraken",
        "text": (
            "Loon is al hetgeen uit een dienstbetrekking of vroegere dienstbetrekking "
            "wordt genoten, waaronder loon in geld, maar ook loon in natura en aanspraken. "
            "Tot het loon behoort niet: de pensioenaanspraak die voldoet aan de wettelijke "
            "voorwaarden; de aanspraak op uitkering bij ziekte en arbeidsongeschiktheid; "
            "de vrijwillige bijdrage in de zorgverzekering. Het loonbegrip is ruimer dan "
            "het arbeidsrechtelijke loonbegrip: ook bonussen, opties en voordelen uit "
            "dienstbetrekking (zoals privégebruik auto) zijn loon."
        ),
    },
    {
        "id": "lb_31",
        "source": "Wet LB 1964",
        "article": "Art. 31 / 31a",
        "title": "Werkkostenregeling (WKR)",
        "text": (
            "De werkkostenregeling (WKR) bepaalt hoe werkgevers vergoedingen en "
            "verstrekkingen aan werknemers kunnen geven. De werkgever mag een vrije "
            "ruimte gebruiken van 1,92% van de fiscale loonsom tot € 400.000 en 1,18% "
            "over het meerdere (2024). Kosten die binnen de vrije ruimte vallen zijn "
            "onbelast. Kosten boven de vrije ruimte worden belast met 80% eindheffing. "
            "Bepaalde vergoedingen zijn 'gerichte vrijstellingen' en tellen niet mee "
            "voor de vrije ruimte, zoals reiskostenvergoeding (max. € 0,23/km), "
            "thuiswerkvergoeding (max. € 2,35/dag), scholingskosten en arbokosten."
        ),
    },
    {
        "id": "lb_20a",
        "source": "Wet LB 1964",
        "article": "Art. 20a",
        "title": "Auto van de zaak en bijtelling",
        "text": (
            "De bijtelling voor privégebruik van een ter beschikking gestelde auto "
            "bedraagt 22% van de catalogusprijs per jaar (2024). Voor volledig elektrische "
            "auto's bedraagt de bijtelling 16% over de eerste € 30.000 van de "
            "catalogusprijs en 22% over het meerdere (2024). Er is geen bijtelling als "
            "de werknemer aantoont dat hij de auto op jaarbasis niet meer dan 500 kilometer "
            "voor privédoeleinden gebruikt, te staven met een sluitende rittenadministratie. "
            "De bijtelling geldt ook voor bestelauto's die niet nagenoeg uitsluitend "
            "zakelijk worden gebruikt."
        ),
    },
    {
        "id": "lb_tarieven",
        "source": "Wet LB 1964",
        "article": "Art. 20 / 20b (Tabel)",
        "title": "Loonbelastingtarieven en heffingskortingen",
        "text": (
            "De loonbelasting kent een progressief tarief dat gelijk loopt met box 1 IB. "
            "In 2024: 36,97% over inkomen tot € 75.518 en 49,5% over het meerdere. "
            "De meest toegepaste heffingskortingen zijn: de algemene heffingskorting "
            "(maximaal € 3.362, afbouwend bij hoger inkomen) en de arbeidskorting "
            "(maximaal € 5.532, afbouwend bij inkomen boven € 37.691). "
            "Voor AOW-gerechtigden gelden aangepaste tarieven en kortingen. "
            "Heffingskortingen verminderen de verschuldigde belasting maar worden "
            "niet uitbetaald als ze de belasting overstijgen (met uitzondering van "
            "de ouderenkorting)."
        ),
    },

    # ── ALGEMEEN / PROCEDURE ─────────────────────────────────────────────────

    {
        "id": "awr_1",
        "source": "Algemene wet inzake rijksbelastingen (AWR)",
        "article": "Art. 16",
        "title": "Navordering",
        "text": (
            "De inspecteur kan een navorderingsaanslag opleggen als te weinig belasting "
            "is geheven. Navordering vereist een 'nieuw feit': een feit dat de inspecteur "
            "niet bekend was of redelijkerwijs niet bekend kon zijn ten tijde van het "
            "vaststellen van de aanslag. Bij kwade trouw van de belastingplichtige is "
            "geen nieuw feit vereist. De navorderingstermijn is vijf jaar na het einde "
            "van het belastingjaar; voor buitenlandse inkomsten geldt een verlengde "
            "termijn van twaalf jaar."
        ),
    },
    {
        "id": "awr_2",
        "source": "Algemene wet inzake rijksbelastingen (AWR)",
        "article": "Art. 67a–67f",
        "title": "Fiscale boetes",
        "text": (
            "De Belastingdienst kan verzuimboetes en vergrijpboetes opleggen. "
            "Een verzuimboete (art. 67a/67b AWR) wordt opgelegd bij niet of te laat "
            "aangifte doen; maximaal € 68 voor particulieren en maximaal € 136 voor "
            "ondernemers per verzuim. Een vergrijpboete (art. 67c–67f AWR) wordt "
            "opgelegd bij opzet of grove schuld: maximaal 100% van de verschuldigde "
            "belasting bij vergrijp in de aangifte, maximaal 300% bij fraude. "
            "Strafverzwaring geldt bij herhaling. Boetes zijn niet aftrekbaar voor "
            "de inkomstenbelasting of vennootschapsbelasting."
        ),
    },
    {
        "id": "transfer_pricing",
        "source": "Wet VPB 1969 / OESO",
        "article": "Art. 8b Wet VPB / OESO-richtlijnen",
        "title": "Transfer pricing en zakelijkheidsbeginsel",
        "text": (
            "Transacties tussen gelieerde partijen moeten plaatsvinden tegen "
            "zakelijke (arm's length) prijzen. Als voorwaarden worden overeengekomen "
            "die afwijken van wat onafhankelijke partijen zouden zijn overeengekomen, "
            "wordt de winst gecorrigeerd. Nederland volgt de OESO Transfer Pricing "
            "Guidelines. Documentatieverplichtingen gelden voor groepen met een omzet "
            "boven € 50 miljoen (local file en master file) en boven € 750 miljoen "
            "(country-by-country reporting). Advance Pricing Agreements (APA's) zijn "
            "mogelijk om zekerheid vooraf te krijgen."
        ),
    },
    {
        "id": "dividendbelasting",
        "source": "Wet op de dividendbelasting 1965",
        "article": "Art. 1 / 4",
        "title": "Dividendbelasting",
        "text": (
            "Dividendbelasting wordt geheven van degenen die gerechtigd zijn tot de "
            "opbrengst van aandelen in en winstbewijzen van in Nederland gevestigde "
            "vennootschappen. Het tarief bedraagt 15%. Dividendbelasting is een "
            "voorheffing en kan worden verrekend met de inkomstenbelasting (box 2) "
            "of vennootschapsbelasting. Voor buitenlandse aandeelhouders kan het "
            "tarief worden verlaagd op basis van belastingverdragen. "
            "Dividendbelasting is in het geval van de deelnemingsvrijstelling "
            "verrekenbaar of terug te vragen."
        ),
    },
    {
        "id": "tonnageregeling",
        "source": "Wet VPB 1969",
        "article": "Art. 8c",
        "title": "Tonnageregeling zeescheepvaart",
        "text": (
            "Rederijen kunnen opteren voor de tonnageregeling, waarbij de winst uit "
            "zeescheepvaart forfaitair wordt vastgesteld op basis van de nettotonnage "
            "van de schepen. De winst per dag bedraagt: € 0,00 per dag per 100 netto "
            "ton voor de eerste 1.000 ton, oplopend naar hogere bedragen voor grotere "
            "schepen. De optie geldt voor een periode van 10 jaar. "
            "De regeling is een fiscale stimuleringsmaatregel voor de Nederlandse "
            "maritieme sector."
        ),
    },
    {
        "id": "innovatiebox",
        "source": "Wet VPB 1969",
        "article": "Art. 12b",
        "title": "Innovatiebox",
        "text": (
            "De innovatiebox biedt een effectief verlaagd vpb-tarief van 9% voor "
            "kwalificerende voordelen uit immateriële activa waarvoor een octrooi of "
            "kwekersrecht is verleend, of waarbij sprake is van door de WBSO "
            "erkende speur- en ontwikkelingswerk. De drempelwinst (winst behaald "
            "met gewone activiteiten) wordt eerst belast tegen het normale tarief. "
            "Het voordeel boven de drempelwinst kwalificeert voor het verlaagde tarief. "
            "Voor grote belastingplichtigen (omzet > € 250 miljoen of voordelen > € 37,5 "
            "miljoen) gelden aanvullende vereisten (nexus approach)."
        ),
    },
    {
        "id": "bpm",
        "source": "Wet op de belasting van personenauto's en motorrijwielen 1992",
        "article": "Art. 1 / 9",
        "title": "BPM (Belasting van personenauto's en motorrijwielen)",
        "text": (
            "BPM wordt geheven ter zake van de registratie van personenauto's, "
            "motorrijwielen en bestelauto's in het kentekenregister. De BPM-grondslag "
            "is de CO2-uitstoot van de auto. Elektrische auto's zijn vrijgesteld van BPM. "
            "Importeurs en particulieren die een gebruikte auto importeren uit het "
            "buitenland zijn BPM verschuldigd, verminderd met een afschrijvingspercentage "
            "op basis van de leeftijd en gebruiksstaat van het voertuig."
        ),
    },
    {
        "id": "erf_en_schenk",
        "source": "Successiewet 1956",
        "article": "Art. 1 / 24",
        "title": "Erfbelasting en schenkbelasting",
        "text": (
            "Erfbelasting wordt geheven over de waarde van wat krachtens erfrecht wordt "
            "verkregen van iemand die in Nederland woonde. Schenkbelasting wordt geheven "
            "over giften van een in Nederland wonende schenker. "
            "Tarieven erfbelasting 2024: voor partners en kinderen 10% over verkrijging "
            "tot € 152.368 en 20% over het meerdere. Voor andere erfgenamen 30% respectievelijk 40%. "
            "Jaarlijkse schenkingsvrijstelling aan kinderen: € 6.633. "
            "Eenmalig verhoogde vrijstelling (jubelton) voor woning is afgeschaft per 2024."
        ),
    },
]


def get_all_chunks() -> list[dict]:
    """Return the full corpus."""
    return CORPUS


def get_chunk_texts() -> list[str]:
    """Return the text of each chunk for embedding."""
    return [
        f"{c['source']} {c['article']} – {c['title']}\n\n{c['text']}"
        for c in CORPUS
    ]


def get_chunk_ids() -> list[str]:
    return [c["id"] for c in CORPUS]
