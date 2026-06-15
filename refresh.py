#!/usr/bin/env python3
"""
Oren CI refresh — runs on GitHub Actions.
Fetches new RASFF alerts and patches index.html in-place.
No pandas / CSV needed — lookup is pre-built in lookup.json.
"""
import urllib.request, ssl, json, re
from pathlib import Path
from datetime import datetime

BASE = "https://webgate.ec.europa.eu/rasff-window/backend/public"
H    = {"User-Agent": "Mozilla/5.0 Chrome/120", "Accept": "application/json",
        "Content-Type": "application/json",
        "Referer": "https://webgate.ec.europa.eu/rasff-window/screen/search"}
CTX  = ssl._create_unverified_context()
HERE = Path(__file__).parent

CAT_HE = {
    "poultry meat and poultry meat products": "עוף ומוצריו",
    "meat and meat products (other than poultry)": "בשר ומוצריו",
    "fish and fish products": "דגים ומוצריהם",
    "milk and milk products": "חלב ומוצריו",
    "eggs and egg products": "ביצים ומוצריהן",
    "cereals and bakery products": "דגנים ומאפים",
    "fruits and vegetables": "פירות וירקות",
    "nuts, nut products and seeds": "אגוזים, גרעינים וזרעים",
    "herbs and spices": "עשבי תבלין ותבלינים",
    "cocoa and cocoa preparations": "קקאו ומוצריו",
    "honey and royal jelly and other apiculture products": "דבש וג'לי מלכות",
    "dietetic foods, food supplements, fortified foods": "תוספי תזונה ומזון מועשר",
    "soups, broths, sauces and condiments": "מרקים, רטבים ותבלינים",
    "confectionery": "ממתקים ושוקולד",
    "bivalve molluscs and products thereof": "רכיכות דו-צדפיות",
    "crustaceans and products thereof": "סרטנים ושרימפס",
    "cephalopods and products thereof": "ראש-רגליים (תמנון/דיונון)",
    "algae and products thereof": "אצות ומוצריהן",
    "feed materials": "מזון לבעלי חיים",
    "water and beverages": "מים ומשקאות",
    "alcoholic beverages": "משקאות אלכוהוליים",
    "food contact materials": "חומרים במגע עם מזון",
    "other food product / mixed": "מוצרי מזון שונים",
    "animals": "בעלי חיים",
    "compound feed": "תערובת מזון לבעלי חיים",
    "fats and oils": "שמנים ושומנים",
    "prepared dishes and snacks": "מנות מוכנות וחטיפים",
    "non-alcoholic beverages": "משקאות ללא אלכוהול",
    "pulses": "קטניות",
}
RISK_HE = {
    "serious": "חמור", "not serious": "לא חמור",
    "potential risk": "סיכון פוטנציאלי", "potentially serious": "עלול להיות חמור",
    "no risk": "ללא סיכון",
}
TYPE_HE = {
    "alert notification": "אזהרה",
    "border rejection notification": "דחייה בגבול",
    "information notification for attention": "מידע לתשומת לב",
    "information notification for follow-up": "מידע למעקב",
    "news": "חדשות",
}
CAT_HS4 = {
    "poultry meat and poultry meat products":           ["0207","0210","1601","1602"],
    "meat and meat products (other than poultry)":      ["0201","0202","0203","0204","0206","0210","1601","1602"],
    "fish and fish products":                           ["0301","0302","0303","0304","0305","1604"],
    "milk and milk products":                           ["0401","0402","0403","0404","0405","0406"],
    "eggs and egg products":                            ["0407","0408"],
    "fruits and vegetables":                            ["0701","0702","0703","0704","0705","0706","0707","0708","0709",
                                                         "0710","0711","0712","0713","0801","0802","0803","0804","0805",
                                                         "0806","0807","0808","0809","0810","0811","0812","0813","0814",
                                                         "2001","2002","2003","2004","2005","2006","2007","2008"],
    "nuts, nut products and seeds":                     ["0801","0802","1202","1203","1204","1205","1206","1207","1208","2008"],
    "herbs and spices":                                 ["0904","0905","0906","0907","0908","0909","0910","1211"],
    "cereals and bakery products":                      ["1001","1002","1003","1004","1005","1006","1007","1008",
                                                         "1101","1102","1103","1104","1901","1904","1905"],
    "cocoa and cocoa preparations":                     ["1801","1802","1803","1804","1805","1806"],
    "honey and royal jelly and other apiculture products": ["0409","0410"],
    "dietetic foods, food supplements, fortified foods":["2106","2101","2102"],
    "soups, broths, sauces and condiments":             ["2103","2104"],
    "confectionery":                                    ["1701","1702","1703","1704","1806"],
    "bivalve molluscs and products thereof":            ["030711","030712","030719","030721","030729",
                                                         "030731","030739","030761","030769","030771",
                                                         "030779","030781","030789","160551","160556","160557","160558"],
    "crustaceans and products thereof":                 ["030611","030612","030619","030621","030622",
                                                         "030629","030631","030632","030639","030641",
                                                         "030642","030649","030651","030652","030659",
                                                         "030691","030692","030699","160521","160529","160530","160540"],
    "cephalopods and products thereof":                 ["030741","030742","030749","030751","030759",
                                                         "030791","030799","160554","160555"],
    "algae and products thereof":                       ["1212"],
    "feed materials":                                   ["2301","2302","2303","2304","2305","2306","2308","2309"],
    "alcoholic beverages":                              ["2203","2204","2205","2206","2208"],
    "water and beverages":                              ["2201","2202"],
    "non-alcoholic beverages":                          ["2201","2202"],
    "fats and oils":                                    ["1501","1502","1503","1504","1505","1507","1508","1509","1510",
                                                         "1511","1512","1513","1514","1515","1516","1517","1518","1520","1521"],
    "prepared dishes and snacks":                       ["1601","1602","1603","1604","1605","2001","2002","2003",
                                                         "2004","2005","2006","2007","2008","2104","2105","2106"],
    "pulses":                                           ["0713"],
    "food contact materials":                           ["3923","4819","7010","7607"],
}


def fetch_rasff():
    payload = {
        "parameters": {"pageNumber": 1, "itemsPerPage": 100},
        "notificationReference": None, "subject": None,
        "notifyingCountry": None, "originCountry": None,
        "distributionCountry": None, "notificationType": None,
        "notificationStatus": None, "notificationClassification": None,
        "notificationBasis": None, "productCategory": None,
        "actionTaken": None, "hazardCategory": None, "riskDecision": None,
    }
    data = json.dumps(payload).encode()
    req  = urllib.request.Request(f"{BASE}/notification/search/consolidated/en/",
                                  data=data, headers=H, method="POST")
    with urllib.request.urlopen(req, timeout=20, context=CTX) as r:
        resp = json.loads(r.read())
    total  = resp.get("totalElements", 0)
    alerts = resp.get("notifications", [])
    print(f"  fetched {len(alerts)} alerts, total: {total:,}")
    return alerts, total


def check_entry(origin_codes, cat_key, lookup):
    hs_list = CAT_HS4.get(cat_key.lower(), [])
    for cc in origin_codes:
        cc_hs = lookup.get(cc.upper(), [])
        for pfx in hs_list:
            if any(hs6.startswith(pfx) for hs6 in cc_hs):
                return True
    return False


def build_cards(alerts, lookup):
    cards = []
    for n in alerts:
        cat_raw  = (n.get("productCategory") or {}).get("description", "")
        risk_raw = (n.get("riskDecision")    or {}).get("description", "")
        type_raw = (n.get("notificationClassification") or {}).get("description", "")
        origins  = n.get("originCountries", [])
        origin_codes = [o.get("isoCode","") for o in origins]
        origin_names = [o.get("organizationName","") for o in origins]
        cards.append({
            "notif_id":     n.get("notifId",""),
            "ref":          n.get("reference",""),
            "subject":      (n.get("subject") or "").strip(),
            "cat_he":       CAT_HE.get(cat_raw.lower(), cat_raw),
            "cat_en":       cat_raw,
            "risk_he":      RISK_HE.get(risk_raw.lower(), risk_raw),
            "risk_raw":     risk_raw.lower(),
            "type_he":      TYPE_HE.get(type_raw.lower(), type_raw),
            "type_raw":     type_raw.lower(),
            "origin_codes": origin_codes,
            "origin_names": origin_names,
            "date":         (n.get("ecValidationDate") or "")[:10],
            "entered_il":   check_entry(origin_codes, cat_raw, lookup),
        })
    return cards


def patch_html(cards, fetch_time, total_rasff):
    html = (HERE / "index.html").read_text(encoding="utf-8")

    # Replace CARDS_INIT data
    html = re.sub(
        r'const CARDS_INIT = \[.*?\];',
        f'const CARDS_INIT = {json.dumps(cards, ensure_ascii=False)};',
        html, flags=re.DOTALL
    )
    # Replace fetch timestamp shown in header
    html = re.sub(
        r'עודכן \d{2}/\d{2}/\d{4} \d{2}:\d{2}',
        f'עודכן {fetch_time}',
        html
    )
    (HERE / "index.html").write_text(html, encoding="utf-8")
    entered = sum(1 for c in cards if c["entered_il"])
    print(f"  index.html patched — {len(cards)} cards, {entered} entered IL")


def main():
    lookup        = json.loads((HERE / "lookup.json").read_text())
    alerts, total = fetch_rasff()
    cards         = build_cards(alerts, lookup)
    fetch_time    = datetime.utcnow().strftime("%d/%m/%Y %H:%M")
    patch_html(cards, fetch_time, total)
    print("Done.")


if __name__ == "__main__":
    main()
