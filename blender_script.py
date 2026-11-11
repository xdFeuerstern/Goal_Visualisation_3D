import bpy
import json

# Pfade
JSONL_PATH = r"C:/Uni/Semester_3/Visual-Analytics/Shaqiri-project/goal_clip.jsonl"
SETUP_BLEND = r"C:/Uni/Semester_3/Visual-Analytics/Shaqiri-project/Blender_files/Soccer_Arena_Setup.blend"
OUTPUT_BLEND = r"C:/Uni/Semester_3/Visual-Analytics/Shaqiri-project/Blender_files/Soccer_Arena_Animated.blend"

# Falls das Skript in VS Code (außerhalb von Blender) gestartet wird: Arena-Datei zuerst öffnen
if "Soccer Ball" not in bpy.data.objects:
    bpy.ops.wm.open_mainfile(filepath=SETUP_BLEND)

# Datei Zeile für Zeile einlesen (1 Zeile = 1 Frame)
frames = []
with open(JSONL_PATH, "r", encoding="utf-8") as file:
    for line in file:
        if line.strip():  # leere Zeilen überspringen
            frame_data = json.loads(line)
            frames.append(frame_data)

# Blender-Timeline einstellen
scene = bpy.context.scene
scene.render.fps = 10
scene.frame_start = 1
scene.frame_end = len(frames)

# Ball und Spieler-Vorlage holen
ball = bpy.data.objects["Soccer Ball"]
player_template = bpy.data.objects["Base Male Mesh"]
players = {}  # Merkt sich für jede player_id das passende 3D-Objekt

# Jeden Frame durchgehen und Positionen als Keyframe speichern
for frame_nr, frame_data in enumerate(frames, start=1):
    # Ballpositionen
    ball_data = frame_data.get("ball_data")
    if ball_data and ball_data.get("x") is not None and ball_data.get("y") is not None:
        x = ball_data["x"]
        y = ball_data["y"]
        z = ball_data.get("z") or 0.11  # Falls z fehlt, auf Bodenhöhe (Ballradius 0.11m)
        ball.location = (x, y, max(0.11, z))
        ball.keyframe_insert(data_path="location", frame=frame_nr)

    # Spielerpositionen
    for p in frame_data.get("player_data", []):
        if p.get("x") is None or p.get("y") is None:
            continue
        pid = p["player_id"]

        # Spieler beim ersten Mal aus der Vorlage kopieren
        if pid not in players:
            new_player = player_template.copy()
            new_player.data = player_template.data.copy()
            new_player.name = f"Player_{pid}"
            scene.collection.objects.link(new_player)
            players[pid] = new_player

        # Spieler an Position setzen & Keyframe speichern
        player_obj = players[pid]
        player_obj.location = (p["x"], p["y"], 0.0)
        player_obj.keyframe_insert(data_path="location", frame=frame_nr)

# Vorlage am Mittelpunkt ausblenden
player_template.hide_viewport = True
player_template.hide_render = True

# Wenn aus VS Code / Terminal gestartet: fertige Animation speichern
if bpy.app.background:
    bpy.ops.wm.save_as_mainfile(filepath=OUTPUT_BLEND)
    print("Gespeichert unter:", OUTPUT_BLEND)

print("Fertig! Frames:", len(frames), "| Spieler:", len(players))
