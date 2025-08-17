import pygame, json, os, sys

# =========================
# Config
# =========================
WIDTH, HEIGHT = 1280, 720
FPS = 60
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
SAVE_PATH = os.path.join(os.path.dirname(__file__), "savegame.json")

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Black Moon — The Pixel Adventure")
clock = pygame.time.Clock()

# =========================
# Fonts & Colors
# =========================
def load_font(size):
    try:
        return pygame.font.Font(pygame.font.match_font("dejavusans,arial,helvetica"), size)
    except:
        return pygame.font.SysFont(None, size)

FONT_TITLE = load_font(40)
FONT_TEXT  = load_font(28)
FONT_UI    = load_font(22)

WHITE = (255,255,255)
BG    = (12,14,22)
PANEL = (18,20,30)

# =========================
# Language & UI strings
# =========================
LANG = "sv"  # "sv" or "en"

UI_STR = {
    "sv": {
        "language_title": "Välj språk / Choose language",
        "svenska": "1. Svenska",
        "engelska": "2. English",
        "status_health": "HÄLSA",
        "status_days": "DYGN KVAR",
        "status_susp": "MISSTANKE",
        "status_allies": "ALLIERADE",
        "yes": "Ja",
        "no": "Nej",
        "restart_prompt": "Tryck valfri tangent för att starta om",
    },
    "en": {
        "language_title": "Choose Language / Välj språk",
        "svenska": "1. Svenska",
        "engelska": "2. English",
        "status_health": "HEALTH",
        "status_days": "DAYS LEFT",
        "status_susp": "SUSPICION",
        "status_allies": "ALLIES",
        "yes": "Yes",
        "no": "No",
        "restart_prompt": "Press any key to restart",
    }
}

def tr(key):
    return UI_STR[LANG][key]

# =========================
# Start screen (no bottom text)
# =========================
def show_start_screen(screen, clock, img_path, title="BLACK MOON – THE PIXEL ADVENTURE"):
    WIDTH0, HEIGHT0 = screen.get_size()
    try:
        img = pygame.image.load(img_path).convert()
        scale = min(WIDTH0 / img.get_width(), HEIGHT0 / img.get_height())
        new_size = (int(img.get_width()*scale), int(img.get_height()*scale))
        img = pygame.transform.smoothscale(img, new_size)
    except Exception:
        img = None

    font_big = load_font(48)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                return

        screen.fill((0,0,0))
        if img:
            screen.blit(img, ((WIDTH0 - img.get_width())//2, (HEIGHT0 - img.get_height())//2))
        else:
            t = font_big.render(title, True, (230,230,255))
            screen.blit(t, ((WIDTH0 - t.get_width())//2, HEIGHT0//3))

        pygame.display.flip()
        clock.tick(60)

# =========================
# Language chooser
# =========================
def choose_language(screen, clock):
    global LANG
    font_big = load_font(48)
    font_small = load_font(28)
    choosing = True
    while choosing:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    LANG = "sv"; choosing = False
                elif event.key == pygame.K_2:
                    LANG = "en"; choosing = False

        screen.fill((0,0,0))
        t = font_big.render(UI_STR["en"]["language_title"], True, WHITE)  # bilingual title looks nicer in EN
        screen.blit(t, ((WIDTH-t.get_width())//2, HEIGHT//3))
        opt1 = font_small.render(UI_STR["sv"]["svenska"], True, (200,220,255))
        opt2 = font_small.render(UI_STR["en"]["engelska"], True, (200,220,255))
        screen.blit(opt1, (WIDTH//2 - opt1.get_width()//2, HEIGHT//2))
        screen.blit(opt2, (WIDTH//2 - opt2.get_width()//2, HEIGHT//2+50))

        pygame.display.flip()
        clock.tick(FPS)

# =========================
# Helpers
# =========================
def load_scene_image(name):
    path = os.path.join(ASSETS_DIR, name)
    max_h = int(HEIGHT*0.52)

    if not os.path.exists(path):
        surf = pygame.Surface((WIDTH, max_h))
        surf.fill((25,28,40))
        pygame.draw.rect(surf, (60,70,110), surf.get_rect(), width=3, border_radius=12)
        txt = FONT_TEXT.render(("Missing image: " if LANG=="en" else "Bild saknas: ") + name, True, (220,230,255))
        surf.blit(txt, (20, 20))
        return surf

    img = pygame.image.load(path).convert()
    scale = min(WIDTH/img.get_width(), max_h/img.get_height())
    new_s = (int(img.get_width()*scale), int(img.get_height()*scale))
    img = pygame.transform.smoothscale(img, new_s)

    surf = pygame.Surface((WIDTH, max_h))
    surf.fill((10,12,18))
    surf.blit(img, ((WIDTH-new_s[0])//2, (max_h-new_s[1])//2))
    pygame.draw.rect(surf, (40,45,70), surf.get_rect(), width=2)
    return surf

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

# =========================
# Game state
# =========================
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

# =========================
# Scenes (bilingual)
# =========================
SCENES = {
    "S1": {
        "title": {"sv": "Uppdraget", "en": "The Mission"},
        "image": "scene_01.png",
        "text": {
            "sv": "Sam Quint, f.d. tjuv, anlitas av FBI för att stjäla en disk med bevis mot Lucky Dollar i Las Vegas. Kuppen lyckas – men Marvin Ringer är dig i hälarna.",
            "en": "Sam Quint, a former thief, is hired by the FBI to steal a disk containing evidence against Lucky Dollar in Las Vegas. The heist succeeds—yet Marvin Ringer is right behind you."
        },
        "options": [
            {"label":{"sv":"Stjäl disken och fly genom öknen.","en":"Steal the disk and escape into the desert."}, "goto":"S2"},
            {"label":{"sv":"Backa ur. Detta är för riskabelt.","en":"Back out. This is too risky."}, "goto":"E_COWARD"}
        ]
    },
    "S2": {
        "title": {"sv":"Macken i öknen", "en":"Desert Gas Station"},
        "image": "scene_02.png",
        "text": {
            "sv": "Vid en enslig mack korsar du Earl Windom som fraktar prototypen Black Moon. Du behöver gömma disken innan Ringer hinner ifatt.",
            "en": "At a lonely gas station you cross paths with Earl Windom hauling the Black Moon prototype. You need to hide the disk before Ringer catches up."
        },
        "options": [
            {"label":{"sv":"Göm disken i Black Moons bakre stötfångare.","en":"Hide the disk in Black Moon’s rear bumper."},
             "goto":"S3", "effects":[{"op":"set","key":"disk_hidden","value":True}]},
            {"label":{"sv":"Behåll disken på dig och kör mot Los Angeles.","en":"Keep the disk and drive toward Los Angeles."},
             "goto":"S3B"}
        ]
    },
    "S3": {
        "title": {"sv":"Los Angeles", "en":"Los Angeles"},
        "image": "scene_03.png",
        "text": {
            "sv": "I L.A. möter du FBI-agent Johnson. Du kräver dubbelt betalt och ett rent pass – Ringer är ett större problem än utlovat.",
            "en": "In L.A., you meet FBI agent Johnson. You demand double pay and a clean passport—Ringer is a bigger problem than promised."
        },
        "options": [
            {"label":{"sv":"Acceptera hans villkor och fortsätt jobbet.","en":"Accept his terms and continue."}, "goto":"S4"},
            {"label":{"sv":"Pressa ännu hårdare – det kostar tid.","en":"Push for more—at the cost of time and heat."},
             "goto":"S4", "effects":[{"op":"inc","key":"days_left","value":-1},{"op":"inc","key":"suspicion","value":1}]}
        ]
    },
    "S3B": {
        "title": {"sv":"Riskabelt val","en":"Risky Choice"},
        "image": "scene_03.png",
        "text": {
            "sv":"Du bar kvar disken. Ringer nosar upp spår och du ligger efter i tid.",
            "en":"You kept the disk. Ringer picks up your trail and you lose time."
        },
        "options": [
            {"label":{"sv":"Acceptera Johnsons villkor och fortsätt.","en":"Accept Johnson’s terms and proceed."},
             "goto":"S4", "effects":[{"op":"inc","key":"suspicion","value":1},{"op":"inc","key":"days_left","value":-1}]}
        ]
    },
    "S4": {
        "title": {"sv":"Restaurangen","en":"The Restaurant"},
        "image": "scene_04.png",
        "text": {
            "sv":"Windom anländer till en fin restaurang. Du spanar – men Nina och hennes liga stjäl bilarna, inklusive Black Moon, direkt från trailern.",
            "en":"Windom arrives at a plush restaurant. You stake it out—but Nina’s crew steals every car, including Black Moon right off the trailer."
        },
        "options": [
            {"label":{"sv":"Kasta dig i jakt, följ spåren till ett kontorstorn.","en":"Dive into a chase, follow the trail to an office tower."},
             "goto":"S5A", "effects":[{"op":"inc","key":"suspicion","value":1}]},
            {"label":{"sv":"Spåra metodiskt via kameror och register.","en":"Track methodically via cameras and records."},
             "goto":"S5B"}
        ]
    },
    "S5A": {
        "title": {"sv":"Garagejakten","en":"The Garage Chase"},
        "image": "scene_05.png",
        "text": {
            "sv":"Du når Ryland Towers men förlorar spåret i garaget. Kameror fångar din siluett.",
            "en":"You reach Ryland Towers but lose the trail in the garage. Cameras catch your silhouette."
        },
        "options": [{"label":{"sv":"Gå vidare.","en":"Continue."}, "goto":"S6"}]
    },
    "S5B": {
        "title": {"sv":"Metodiskt spår","en":"Careful Trail"},
        "image": "scene_05.png",
        "text": {
            "sv":"Spaningen pekar mot Ryland Towers – och Ed Rylands stulna-bilsyndikat.",
            "en":"The trail points to Ryland Towers—and Ed Ryland’s stolen car syndicate."
        },
        "options": [{"label":{"sv":"Gå vidare.","en":"Continue."}, "goto":"S6"}]
    },
    "S6": {
        "title": {"sv":"Tre dagar","en":"Three Days"},
        "image": "scene_06.png",
        "text": {
            "sv":"Johnson varnar: utan disk inom 3 dagar faller målet. Windom vill kontakta polis först.",
            "en":"Johnson warns: without the disk in 3 days, the case collapses. Windom wants to go to the police first."
        },
        "options": [
            {"label":{"sv":"Be Windom om hjälp – de säger nej (till att börja med).","en":"Ask Windom for help—they refuse at first."}, "goto":"S7"},
            {"label":{"sv":"Jobba solo och spara tid.","en":"Work solo to save time."}, "goto":"S7", "effects":[{"op":"set","key":"solo","value":True}]}
        ]
    },
    "S7": {
        "title": {"sv":"Nattklubben","en":"The Nightclub"},
        "image": "scene_07.png",
        "text": {
            "sv":"Du följer Nina till en klubb. Ni klickar – men kan du lita på henne?",
            "en":"You follow Nina to a club. You connect—but can you trust her?"
        },
        "options": [
            {"label":{"sv":"Visa tillit till Nina.","en":"Trust Nina."}, "goto":"S8", "effects":[{"op":"set","key":"trust_nina","value":True}]},
            {"label":{"sv":"Håll distans – fokus på bilen.","en":"Keep your distance—focus on the car."}, "goto":"S8", "effects":[{"op":"set","key":"trust_nina","value":False}]}
        ]
    },
    "S8": {
        "title": {"sv":"Bakhåll","en":"Ambush"},
        "image": "scene_08.png",
        "text": {
            "sv":"Windoms team granskar tornen; en i teamet dödas av Rylands folk. De vänder sig till dig. Ringer hittar dig och anfaller.",
            "en":"Windom’s team checks the towers; one is killed by Ryland’s men. They turn to you. Ringer finds you and attacks."
        },
        "options": [
            {"label":{"sv":"Fly över taket (du skadas).","en":"Flee over the rooftop (you’re hurt)."},
             "goto":"S9", "effects":[{"op":"inc","key":"health","value":-1},{"op":"set","key":"windom_allies","value":True}]},
            {"label":{"sv":"Slå tillbaka (du gör motstånd men blottar dig).","en":"Fight back (you resist but expose yourself)."},
             "goto":"S9", "effects":[{"op":"inc","key":"health","value":-1},{"op":"inc","key":"killed_henchmen","value":2},{"op":"set","key":"windom_allies","value":True}]}
        ]
    },
    "S9": {
        "title": {"sv":"Planen","en":"The Plan"},
        "image": "scene_09.png",
        "text": {
            "sv":"Huvudgaraget är ointagligt. Ni bestämmer er för att ta er in via det oavslutade tornet.",
            "en":"The main garage is impenetrable. You decide to enter via the unfinished tower."
        },
        "options": [
            {"label":{"sv":"Invänta natt (säkrare).","en":"Wait for night (safer)."},
             "goto":"S10", "effects":[{"op":"inc","key":"days_left","value":-1}]},
            {"label":{"sv":"Gå direkt (snabbt men riskabelt, kostar tid).","en":"Go now (fast but risky, still costs time)."},
             "goto":"S10", "effects":[{"op":"inc","key":"days_left","value":-1}]}
        ]
    },
    "S10": {
        "title": {"sv":"Ventilationsschaktet","en":"The Vent Shaft"},
        "image": "scene_10.png",
        "text": {
            "sv":"Du klättrar ned i schaktet – och hittar Nina inspärrad. Ryland misstänker henne.",
            "en":"You climb down the shaft—and find Nina locked up. Ryland suspects her."
        },
        "options": [
            {"label":{"sv":"Rädda Nina. Två är bättre än en.","en":"Rescue Nina. Two are better than one."},
             "goto":"S11", "effects":[{"op":"set","key":"trust_nina","value":True}]},
            {"label":{"sv":"Lämna henne. Tiden är knapp.","en":"Leave her. Time is critical."}, "goto":"S11B"}
        ]
    },
    "S11": {
        "title": {"sv":"Chop shop-kuppen","en":"Chop Shop Heist"},
        "image": "scene_11.png",
        "text": {
            "sv":"I stulna uniformer rullar ni ut Black Moon. Windom spränger porten men nödgaller faller. Ni kör in i lasthissen mot Rylands våningsplan.",
            "en":"In stolen uniforms you roll out Black Moon. Windom blows the door but emergency bars drop. You drive into the freight elevator toward Ryland’s floor."
        },
        "options": [{"label":{"sv":"Aktivera turbon – rakt mot fönstret!","en":"Hit turbo—straight at the window!"}, "goto":"S12"}]
    },
    "S11B": {
        "title": {"sv":"Solo i kaoset","en":"Solo in the Chaos"},
        "image": "scene_11.png",
        "text": {
            "sv":"Du kör ensam. Utan Ninas hjälp blir reträtten rörigare och du skadas.",
            "en":"You drive solo. Without Nina’s help the retreat is messier and you’re hurt."
        },
        "options": [{"label":{"sv":"Aktivera turbon – rakt mot fönstret!","en":"Hit turbo—straight at the window!"},
                     "goto":"S12", "effects":[{"op":"inc","key":"health","value":-1}]}]
    },
    "S12": {
        "title": {"sv":"Genom glaset","en":"Through the Glass"},
        "image": "scene_11.png",
        "text": {
            "sv":"Black Moon skjuter fram – Ryland mejas, bilen flyger in i det tomma tornet. Du får ut disken...",
            "en":"Black Moon surges—Ryland is struck, the car leaps into the empty tower. You retrieve the disk..."
        },
        "options": [{"label":{"sv":"Möt Ringer: slåss om disken.","en":"Face Ringer: fight for the disk."}, "goto":"S13"}]
    },
    "S13": {
        "title": {"sv":"Final","en":"Finale"},
        "image": "scene_12.png",
        "text": {
            "sv":"Ringer dyker upp för att hämta disken. Johnson närmar sig. Allt avgörs nu.",
            "en":"Ringer arrives to seize the disk. Johnson closes in. Everything is decided now."
        },
        "options": [
            {"label":{"sv":"Ge disken till Johnson och dra dig tillbaka.","en":"Give the disk to Johnson and walk away."}, "goto":"E_GOOD"},
            {"label":{"sv":"Behåll disken – sälj den själv.","en":"Keep the disk—sell it yourself."}, "goto":"E_GREED"},
        ]
    },

    # Endings
    "E_COWARD": {
        "title":{"sv":"Game Over","en":"Game Over"},
        "image":"scene_03.png",
        "text":{"sv":"Du backade ur. Lucky Dollar går fria.","en":"You backed out. Lucky Dollar walks free."},
        "options":[]
    },
    "E_TIME": {
        "title":{"sv":"För sent","en":"Too Late"},
        "image":"scene_06.png",
        "text":{"sv":"Tre dagar gick. Fallet faller i domstol.","en":"Three days passed. The case collapses in court."},
        "options":[]
    },
    "E_DEAD": {
        "title":{"sv":"Skadad till fall","en":"Down and Out"},
        "image":"scene_08.png",
        "text":{"sv":"Skadorna blir för svåra.","en":"Your injuries are too severe."},
        "options":[]
    },
    "E_GOOD": {
        "title":{"sv":"You Win!","en":"You Win!"},
        "image":"scene_12.png",
        "text":{"sv":"Du lämnar disken till Johnson. Pensionen väntar.","en":"You hand the disk to Johnson. Retirement awaits."},
        "options":[]
    },
    "E_GREED": {
        "title":{"sv":"Girighetens pris","en":"Price of Greed"},
        "image":"scene_12.png",
        "text":{"sv":"Du försöker sälja disken. Ringer jagar dig för evigt.","en":"You try to sell the disk. Ringer hunts you forever."},
        "options":[]
    }
}

# =========================
# Rendering & state updates
# =========================
def apply_effects(state, effects):
    for e in effects or []:
        op, key, val = e.get("op"), e.get("key"), e.get("value")
        if op == "set":
            state[key] = val
        elif op == "inc":
            state[key] = state.get(key, 0) + val
    if state["health"] <= 0:
        state["scene"] = "E_DEAD"
    if state["days_left"] <= 0 and not state["scene"].startswith("E_"):
        state["scene"] = "E_TIME"
    return state

def draw_status_bar(state):
    bar_h = 34
    rect = pygame.Rect(0, HEIGHT - bar_h, WIDTH, bar_h)
    pygame.draw.rect(screen, PANEL, rect)
    pygame.draw.line(screen, (45,50,70), (0, HEIGHT-bar_h), (WIDTH, HEIGHT-bar_h), 2)
    info = f" {tr('status_health')}: {state['health']}   {tr('status_days')}: {state['days_left']}   {tr('status_susp')}: {state['suspicion']}   {tr('status_allies')}: {tr('yes') if state['windom_allies'] else tr('no')} "
    txt = FONT_UI.render(info, True, (220,230,255))
    screen.blit(txt, (12, HEIGHT - bar_h + 7))

def draw_scene(state):
    screen.fill(BG)
    sc = SCENES[state["scene"]]
    title = sc["title"][LANG]
    text  = sc["text"][LANG]
    img = load_scene_image(sc["image"])
    screen.blit(img, (0,0))

    title_surf = FONT_TITLE.render(title, True, WHITE)
    screen.blit(title_surf, (24, int(HEIGHT*0.52)+18))

    panel_rect = pygame.Rect(20, int(HEIGHT*0.52)+70, WIDTH-40, int(HEIGHT*0.48)-110)
    pygame.draw.rect(screen, PANEL, panel_rect, border_radius=12)
    pygame.draw.rect(screen, (40,45,70), panel_rect, width=2, border_radius=12)

    lines = wrap_text(text, FONT_TEXT, panel_rect.width-28)
    y = panel_rect.y + 14
    for line in lines:
        surf = FONT_TEXT.render(line, True, (230,235,255))
        screen.blit(surf, (panel_rect.x+14, y))
        y += FONT_TEXT.get_height() + 4

    options = sc.get("options", [])
    y += 10
    for idx, opt in enumerate(options, start=1):
        label = f"{idx}. {opt['label'][LANG]}"
        surf = FONT_TEXT.render(label, True, (255,255,200))
        screen.blit(surf, (panel_rect.x+14, y))
        y += FONT_TEXT.get_height() + 6

    draw_status_bar(state)

def show_end_and_wait_for_restart(state):
    overlay_font = load_font(40)
    sub_font = load_font(22)
    prompt = tr("restart_prompt")

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                waiting = False

        draw_scene(state)
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 140))
        screen.blit(s, (0, 0))

        title = SCENES[state["scene"]]["title"][LANG]
        t_surf = overlay_font.render(title, True, (255, 230, 140))
        screen.blit(t_surf, ((WIDTH - t_surf.get_width())//2, int(HEIGHT*0.30)))

        p_surf = sub_font.render(prompt, True, (255, 200, 120))
        screen.blit(p_surf, ((WIDTH - p_surf.get_width())//2, int(HEIGHT*0.62)))

        pygame.display.flip()
        clock.tick(FPS)

# =========================
# Save / Load
# =========================
def save_game(state):
    try:
        with open(SAVE_PATH, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print("Save error:", e)
        return False

def load_game():
    try:
        with open(SAVE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None

# =========================
# Scene stepping
# =========================
def step_scene(state, choice_index):
    sc = SCENES[state["scene"]]
    options = sc.get("options", [])
    if choice_index < 0 or choice_index >= len(options):
        return state
    opt = options[choice_index]

    # No automatic day loss; only explicit effects
    apply_effects(state, opt.get("effects"))

    goto = opt.get("goto", state["scene"])
    if goto in ("E_GOOD","E_GREED","E_COWARD","E_TIME","E_DEAD"):
        state["scene"] = goto
        return state

    state["scene"] = goto
    return state

# =========================
# Game loop
# =========================
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

        # Endings: show overlay, then back to start (keep chosen language)
        if state["scene"].startswith("E_"):
            show_end_and_wait_for_restart(state)
            start_img_path = os.path.join(ASSETS_DIR, "start_screen.png")
            show_start_screen(screen, clock, start_img_path)
            state = new_game_state()
            continue

        # Safety checks
        if state["health"] <= 0:
            state["scene"] = "E_DEAD"
        if state["days_left"] <= 0 and not state["scene"].startswith("E_"):
            state["scene"] = "E_TIME"

        draw_scene(state)
        pygame.display.flip()

    pygame.quit()

# =========================
# Main
# =========================
if __name__ == "__main__":
    if not os.path.isdir(ASSETS_DIR):
        print("Tip: Create an 'assets' folder next to this script and place your images there.")
    # Choose language once, then show start screen in that language
    choose_language(screen, clock)
    start_img_path = os.path.join(ASSETS_DIR, "start_screen.png")
    show_start_screen(screen, clock, start_img_path)
    run_game()
