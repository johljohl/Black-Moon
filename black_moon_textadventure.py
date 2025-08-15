import pygame, json, os, sys, time

# --------- Grundinställningar ----------
WIDTH, HEIGHT = 1280, 720
FPS = 60
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")  # lägg scenbilderna här
SAVE_PATH = os.path.join(os.path.dirname(__file__), "savegame.json")

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Black Moon — Textäventyr")
clock = pygame.time.Clock()

# Typsnitt
def load_font(size):
    try:
        return pygame.font.Font(pygame.font.match_font("dejavusans,arial,helvetica"), size)
    except:
        return pygame.font.SysFont(None, size)

FONT_TITLE = load_font(40)
FONT_TEXT  = load_font(28)
FONT_UI    = load_font(22)

# Färger
WHITE = (255,255,255)
BLACK = (0,0,0)
BG    = (12,14,22)
PANEL = (18,20,30)
ACCENT= (200,220,255)

# Hjälpfunktion: Bildladdning (skalar till toppytan)
def load_scene_image(name):
    path = os.path.join(ASSETS_DIR, name)
    if not os.path.exists(path):
        # Skapa en tom fallback-surface
        surf = pygame.Surface((WIDTH, int(HEIGHT*0.52)))
        surf.fill((25,28,40))
        pygame.draw.rect(surf, (60,70,110), surf.get_rect(), width=3, border_radius=12)
        txt = FONT_TEXT.render("Bild saknas: " + name, True, ACCENT)
        surf.blit(txt, (20, 20))
        return surf
    img = pygame.image.load(path).convert()
    max_h = int(HEIGHT*0.52)
    scale = min(WIDTH/img.get_width(), max_h/img.get_height())
    new_s = (int(img.get_width()*scale), int(img.get_height()*scale))
    img = pygame.transform.smoothscale(img, new_s)
    # Lägg på letterbox
    surf = pygame.Surface((WIDTH, max_h))
    surf.fill((10,12,18))
    surf.blit(img, ((WIDTH-new_s[0])//2, (max_h-new_s[1])//2))
    pygame.draw.rect(surf, (40,45,70), surf.get_rect(), width=2)
    return surf

# Hjälpfunktion: Radbryt text till given bredd
def wrap_text(text, font, max_width):
    words = text.split(" ")
    lines, line = [], ""
    for w in words:
        test = (line + " " + w).strip()
        if font.size(test)[0] <= max_width:
            line = test
        else:
            if line: lines.append(line)
            line = w
    if line: lines.append(line)
    return lines

# ---------- Speldata ----------
# Tillståndsflaggor
def new_game_state():
    return {
        "scene": "S1",
        "has_disk": True,
        "disk_hidden": False,
        "trust_nina": None,
        "windom_allies": False,
        "days_left": 3,
        "health": 3,
        "suspicion": 0,
        "solo": False,
        "killed_henchmen": 0,
        "ending": None
    }

# Scenstruktur:
# Varje scen har: title, image, text, options:[{"label":..., "goto":"S#", "effects":[...], "requires":{flag: value}}]
# Effekter: {"op":"set"/"inc", "key":"days_left", "value":-1}
SCENES = {
    "S1": {
        "title": "Uppdraget",
        "image": "scene_01_uppdraget.png",
        "text": (
            "Sam Quint, f.d. tjuv, anlitas av FBI för att stjäla en disk med bevis mot "
            "Lucky Dollar i Las Vegas. Kuppen lyckas – men Marvin Ringer är dig i hälarna."
        ),
        "options": [
            {"label":"Stjäl disken och fly genom öknen.", "goto":"S2"},
            {"label":"Backa ur. Detta är för riskabelt.", "goto":"E_COWARD"}
        ]
    },
    "S2": {
        "title": "Macken i öknen",
        "image": "scene_02_gasstation.png",
        "text": (
            "Vid en enslig mack korsar du Earl Windom som fraktar prototypen Black Moon. "
            "Du behöver gömma disken innan Ringer hinner ifatt."
        ),
        "options": [
            {"label":"Göm disken i Black Moons bakre stötfångare.", 
             "goto":"S3", "effects":[{"op":"set","key":"disk_hidden","value":True}]},
            {"label":"Behåll disken på dig och kör mot Los Angeles.",
             "goto":"S3B"}
        ]
    },
    "S3": {
        "title": "Los Angeles",
        "image": "scene_03_la_mote.png",
        "text": (
            "I L.A. möter du FBI-agent Johnson. Du kräver dubbelt betalt och ett rent pass – "
            "Ringer är ett större problem än utlovat."
        ),
        "options": [
            {"label":"Acceptera hans villkor och fortsätt jobbet.", "goto":"S4"},
            {"label":"Pressa ännu hårdare – det kostar tid.", 
             "goto":"S4", "effects":[{"op":"inc","key":"days_left","value":-1},{"op":"inc","key":"suspicion","value":1}]}
        ]
    },
    "S3B": {
        "title": "Riskabelt val",
        "image": "scene_03_la_mote.png",
        "text": (
            "Du bar kvar disken. Ringer nosar upp spår och du ligger efter i tid."
        ),
        "options": [
            {"label":"Acceptera Johnsons villkor och fortsätt.", 
             "goto":"S4", "effects":[{"op":"inc","key":"suspicion","value":1},{"op":"inc","key":"days_left","value":-1}]}
        ]
    },
    "S4": {
        "title": "Restaurangen",
        "image": "scene_04_restaurang_stold.png",
        "text": (
            "Windom anländer till en fin restaurang. Du spanar – men Nina och hennes bilring "
            "stjäl alla bilar, inklusive Black Moon, direkt från trailern."
        ),
        "options": [
            {"label":"Kasta dig i jakt, följ spåren till ett kontorstorn.", 
             "goto":"S5A", "effects":[{"op":"inc","key":"suspicion","value":1}]},
            {"label":"Spåra metodiskt via kameror och registreringar.", 
             "goto":"S5B"}
        ]
    },
    "S5A": {
        "title": "Garagejakten",
        "image": "scene_05_garage_jakt.png",
        "text": (
            "Du når Ryland Towers men förlorar spåret i garaget. Kameror fångar din siluett."
        ),
        "options": [
            {"label":"Gå vidare.", "goto":"S6"}
        ]
    },
    "S5B": {
        "title": "Metodiskt spår",
        "image": "scene_05_garage_jakt.png",
        "text": (
            "Spaningen pekar mot Ryland Towers – och Ed Rylands stulna-bilsyndikat."
        ),
        "options": [
            {"label":"Gå vidare.", "goto":"S6"}
        ]
    },
    "S6": {
        "title": "Tre dagar",
        "image": "scene_06_stakeout.png",
        "text": (
            "Johnson varnar: utan disk inom 3 dagar faller målet. Windom vill kontakta polis först."
        ),
        "options": [
            {"label":"Be Windom om hjälp – de säger nej (till att börja med).", "goto":"S7"},
            {"label":"Jobba solo och spara tid.", "goto":"S7", "effects":[{"op":"set","key":"solo","value":True}]}
        ]
    },
    "S7": {
        "title": "Nattklubben",
        "image": "scene_07_nattklubb.png",
        "text": (
            "Du följer Nina till en klubb. Ni klickar – men kan du lita på henne?"
        ),
        "options": [
            {"label":"Visa tillit till Nina.", "goto":"S8", "effects":[{"op":"set","key":"trust_nina","value":True}]},
            {"label":"Håll distans – fokus på bilen.", "goto":"S8", "effects":[{"op":"set","key":"trust_nina","value":False}]}
        ]
    },
    "S8": {
        "title": "Bakhåll",
        "image": "scene_08_bakhall.png",
        "text": (
            "Windoms team granskar tornen; en ur teamet dödas av Rylands folk. De vänder sig till dig. "
            "Ringer hittar dig och anfaller."
        ),
        "options": [
            {"label":"Fly över taket (du skadas).", 
             "goto":"S9", "effects":[{"op":"inc","key":"health","value":-1},{"op":"set","key":"windom_allies","value":True}]},
            {"label":"Slå tillbaka (du gör motstånd men blottar dig).", 
             "goto":"S9", "effects":[{"op":"inc","key":"health","value":-1},{"op":"inc","key":"killed_henchmen","value":2},{"op":"set","key":"windom_allies","value":True}]}
        ]
    },
    "S9": {
        "title": "Planen",
        "image": "scene_09_planen.png",
        "text": (
            "Huvudgaraget är ointagligt. Ni bestämmer er för att ta er in via det oavslutade tornet."
        ),
        "options": [
            {"label":"Invänta natt (säkrare).", "goto":"S10"},
            {"label":"Gå direkt (snabbt men riskabelt, kostar tid).", 
             "goto":"S10", "effects":[{"op":"inc","key":"days_left","value":-1}]}
        ]
    },
    "S10": {
        "title": "Ventilationsschaktet",
        "image": "scene_10_schakt.png",
        "text": (
            "Du klättrar ned i schaktet – och hittar Nina inspärrad. Ryland misstänker henne."
        ),
        "options": [
            {"label":"Rädda Nina. Två är bättre än en.", 
             "goto":"S11", "effects":[{"op":"set","key":"trust_nina","value":True}]},
            {"label":"Lämna henne. Tiden är knapp.", "goto":"S11B"}
        ]
    },
    "S11": {
        "title": "Chop shop-kuppen",
        "image": "scene_11_chopshop.png",
        "text": (
            "I stulna uniformer rullar ni ut Black Moon. Windom spränger porten med C-4 men "
            "nödgaller fälls. Ni styr in i last­hissen mot Rylands våningsplan."
        ),
        "options": [
            {"label":"Aktivera turbon – rakt mot fönstret!", "goto":"S12"}
        ]
    },
    "S11B": {
        "title": "Solo i kaoset",
        "image": "scene_11_chopshop.png",
        "text": (
            "Du kör ensam. Utan Ninas hjälp blir reträtten rörigare och du skadas."
        ),
        "options": [
            {"label":"Aktivera turbon – rakt mot fönstret!", 
             "goto":"S12", "effects":[{"op":"inc","key":"health","value":-1}]}
        ]
    },
    "S12": {
        "title": "Genom glaset",
        "image": "scene_11_chopshop.png",
        "text": (
            "Black Moon skjuter fram – Ryland mejas, bilen flyger in i det tomma tornet. Du får ut disken..."
        ),
        "options": [
            {"label":"Möt Ringer: slåss om disken.", "goto":"S13"}
        ]
    },
    "S13": {
        "title": "Final",
        "image": "scene_12_final.png",
        "text": (
            "Ringer dyker upp för att hämta disken. Johnson närmar sig. Allt avgörs nu."
        ),
        "options": [
            {"label":"Ge disken till Johnson och dra dig tillbaka.", "goto":"E_GOOD"},
            {"label":"Behåll disken – sälj den själv.", "goto":"E_GREED"},
        ]
    },
    # ------- Slutscener -------
    "E_COWARD": {
        "title": "Game Over",
        "image": "scene_03_la_mote.png",
        "text": "Du backade ur. Lucky Dollar går fria och Ringer hittar dig förr eller senare.",
        "options": []
    },
    "E_TIME": {
        "title": "För sent",
        "image": "scene_06_stakeout.png",
        "text": "Tre dagar gick. Fallet faller i domstol och Johnson stänger dörren.",
        "options": []
    },
    "E_DEAD": {
        "title": "Skadad till fall",
        "image": "scene_08_bakhall.png",
        "text": "Skadorna blir för svåra. Mörkret tar över L.A:s ljus.",
        "options": []
    },
    "E_GOOD": {
        "title": "Frihet på riktigt",
        "image": "scene_12_final.png",
        "text": "Du lämnar disken till Johnson. Windom räddar sin bil, Nina ler. Pensionen väntar.",
        "options": []
    },
    "E_GREED": {
        "title": "Girighetens pris",
        "image": "scene_12_final.png",
        "text": "Du försöker sälja disken. Ringer och Lucky Dollar jagar dig resten av livet.",
        "options": []
    }
}

# --------- Spelloop & rendering ----------
def apply_effects(state, effects):
    for e in effects or []:
        op, key, val = e.get("op"), e.get("key"), e.get("value")
        if op == "set":
            state[key] = val
        elif op == "inc":
            state[key] = state.get(key, 0) + val
    # Globala konsekvenser
    if state["health"] <= 0:
        state["scene"] = "E_DEAD"
    if state["days_left"] <= 0 and state["scene"] not in ("E_DEAD","E_GOOD","E_GREED"):
        state["scene"] = "E_TIME"
    return state

def draw_status_bar(state):
    bar_h = 34
    rect = pygame.Rect(0, HEIGHT - bar_h, WIDTH, bar_h)
    pygame.draw.rect(screen, PANEL, rect)
    pygame.draw.line(screen, (45,50,70), (0, HEIGHT-bar_h), (WIDTH, HEIGHT-bar_h), 2)
    info = f" HÄLSA: {state['health']}   DYGN KVAR: {state['days_left']}   MISSTANKE: {state['suspicion']}   ALLIERADE: {'Ja' if state['windom_allies'] else 'Nej'} "
    txt = FONT_UI.render(info, True, (220,230,255))
    screen.blit(txt, (12, HEIGHT - bar_h + 7))

def draw_scene(state):
    screen.fill(BG)
    sc = SCENES[state["scene"]]

    # Bild
    img = load_scene_image(sc["image"])
    screen.blit(img, (0,0))

    # Titel
    title_surf = FONT_TITLE.render(sc["title"], True, WHITE)
    screen.blit(title_surf, (24, int(HEIGHT*0.52)+18))

    # Textpanel
    panel_rect = pygame.Rect(20, int(HEIGHT*0.52)+70, WIDTH-40, int(HEIGHT*0.48)-110)
    pygame.draw.rect(screen, PANEL, panel_rect, border_radius=12)
    pygame.draw.rect(screen, (40,45,70), panel_rect, width=2, border_radius=12)

    # Text
    lines = wrap_text(SCENES[state["scene"]]["text"], FONT_TEXT, panel_rect.width-28)
    y = panel_rect.y + 14
    for line in lines:
        surf = FONT_TEXT.render(line, True, (230,235,255))
        screen.blit(surf, (panel_rect.x+14, y))
        y += FONT_TEXT.get_height() + 4

    # Alternativ
    options = sc.get("options", [])
    y += 10
    for idx, opt in enumerate(options, start=1):
        label = f"{idx}. {opt['label']}"
        surf = FONT_TEXT.render(label, True, (255,255,200))
        screen.blit(surf, (panel_rect.x+14, y))
        y += FONT_TEXT.get_height() + 6

    draw_status_bar(state)

def save_game(state):
    try:
        with open(SAVE_PATH, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print("Spara fel:", e)
        return False

def load_game():
    try:
        with open(SAVE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None

def step_scene(state, choice_index):
    sc = SCENES[state["scene"]]
    options = sc.get("options", [])
    if choice_index < 0 or choice_index >= len(options):
        return state
    opt = options[choice_index]
    # dagar tickar vid större steg (utom rena slutscener)
    if state["scene"] in ("S4","S6","S8","S10","S12") and opt.get("goto","").startswith("S"):
        state["days_left"] = max(0, state["days_left"] - 1)
    apply_effects(state, opt.get("effects"))

    # Specifika logiker
    if opt.get("goto") == "E_GOOD" or opt.get("goto") == "E_GREED":
        state["scene"] = opt["goto"]
        return state

    state["scene"] = opt.get("goto", state["scene"])
    return state

def run_game():
    state = new_game_state()
    running = True
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if pygame.K_1 <= event.key <= pygame.K_9:
                    idx = event.key - pygame.K_1
                    state = step_scene(state, idx)
                elif event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_s:
                    save_game(state)
                elif event.key == pygame.K_l:
                    loaded = load_game()
                    if loaded:
                        state = loaded

        # Automatiska avbrott vid slut
        if state["scene"].startswith("E_"):
            # rita slutbild + vänta kort, sen lås val
            draw_scene(state)
            pygame.display.flip()
            # tillåt ESC eller L
        else:
            # Döds- eller tidskontroll
            if state["health"] <= 0:
                state["scene"] = "E_DEAD"
            if state["days_left"] <= 0:
                state["scene"] = "E_TIME"

        draw_scene(state)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    # Kontrollera att assets finns
    if not os.path.isdir(ASSETS_DIR):
        print("Tips: Skapa mappen 'assets' bredvid scriptet och lägg scenbilderna där.")
        print("Du kan ladda ner dem från paketet 'black_moon_assets.zip'.")
    run_game()
