import bpy
import json
from mathutils import Vector
from pathlib import Path

# Pfade relativ zum Repo-Ordner, damit das Skript auf jedem Rechner läuft.
# In Blender (Scripting-Tab) zeigt __file__ nicht auf diese Datei, daher über die offene .blend-Datei in blender_files/.
if bpy.data.filepath:
    BASE_DIR = Path(bpy.data.filepath).resolve().parent.parent
else:
    BASE_DIR = Path(__file__).resolve().parent

JSONL_PATH = BASE_DIR / "data" / "raw" / "goal_clip.jsonl"
SETUP_BLEND = BASE_DIR / "blender_files" / "Soccer_Arena_Setup.blend"
OUTPUT_BLEND = BASE_DIR / "blender_files" / "Soccer_Arena_Animated.blend"

# Falls das Skript in VS Code (außerhalb von Blender) gestartet wird: Arena-Datei zuerst öffnen
if "Soccer Ball" not in bpy.data.objects:
    bpy.ops.wm.open_mainfile(filepath=str(SETUP_BLEND))

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
players = {}  # Merkt sich für jede player_id das passende 3D Objekt

# Spieler aus einem früheren Durchlauf löschen, sonst entstehen Duplikate (Player_x.001)
for obj in list(bpy.data.objects):
    if obj.name.startswith("Player_"):
        bpy.data.object.remove(obj)
        
# Hilfsfunktion: Holt einen Spieler oder erstellt ihn beim ersten Mal
def get_player(pid):
    if pid not in players:
        p = player_template.copy()
        p.data = player_template.data.copy()
        p.name = f"Player_{pid}"
        p.hide_viewport = p.hide_render = False
        scene.collection.objects.link(p)
        players[pid] = p
    return players[pid]

# Jeden Frame durchgehen und Positionen als Keyframe speichern
for frame_nr, frame_data in enumerate(frames, start=1):
    
    # Ballbewegung
    ball_data = frame_data.get("ball_data")
    if ball_data and ball_data.get("x") is not None and ball_data.get("y") is not None:
        x = ball_data["x"]
        y = ball_data["y"]
        z = ball_data.get("z") or 0.11  # Falls z fehlt, auf Bodenhöhe (Ballradius 0.11m)
        ball.location = (x, y, max(0.11, z))
        ball.keyframe_insert(data_path="location", frame=frame_nr)

    # Spieler bewegen und drehen
    for p in frame_data.get("player_data", []):
        if p.get("x") is None or p.get("y") is None:
            continue
        
        player_obj = get_player(p["player_id"])
        new_pos = Vector((p["x"], p["y"], 0.0))

        # Laufrichtung = Neue Position - alte position
        move_direction = new_pos - player_obj.location
        if frame_nr > 1 and move_direction.length > 0.01:
            # Dreht die Blickrichtung des Spielers
            rotation = move_direction.to_track_quat("-Y", "Z").to_euler()
            rotation.make_compatible(player_obj.rotation_euler)
            player_obj.rotation_euler = rotation
            player_obj.keyframe_insert("rotation_euler", frame = frame_nr)

        # Neue Position setzen
        player_obj.location = new_pos
        player_obj.keyframe_insert(data_path="location", frame=frame_nr)

# Vorlage am Mittelpunkt ausblenden
player_template.hide_viewport = True

# Wenn aus VS Code / Terminal gestartet: fertige Animation speichern
if bpy.app.background:
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_BLEND))
    print("Gespeichert unter:", OUTPUT_BLEND)

print("Fertig! Frames:", len(frames), "| Spieler:", len(players))
