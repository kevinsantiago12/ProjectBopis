"""Read-only, headless: dumps every placed mesh and decal in the reference maps (the packs' demo maps), with
materials, so the building patterns can be analysed offline (analyse_buildings.py). Nothing is saved.

Run: .\\Tools\\AnimAuthoring\\RunUnreal.ps1 .\\Tools\\LevelGen\\analysis\\dump_map_ue.py
Writes Saved/LevelGen/dump_<map>.json and dump_materials.json."""
import json
import os
import traceback

import unreal

MAPS = ["/Game/Megapack/Maps/Favela/Favela", "/Game/AsiaSlum/DemoMap/Demomap_AsiaSlum"]
OUT = os.path.join(unreal.Paths.project_saved_dir(), "LevelGen")
os.makedirs(OUT, exist_ok=True)
mel = unreal.MaterialEditingLibrary
materials = {}


def say(msg):
    unreal.log_warning("[DUMP] " + msg)


def xf(t):
    loc, rot, sc = t.translation, t.rotation.rotator(), t.scale3d
    return [round(loc.x, 1), round(loc.y, 1), round(loc.z, 1), round(rot.pitch, 1), round(rot.yaw, 1), round(rot.roll, 1),
            round(sc.x, 3), round(sc.y, 3), round(sc.z, 3)]


def note_material(m):
    """Records a material's parent chain and texture parameters once; returns its path."""
    if m is None:
        return None
    p = m.get_path_name()
    if p in materials:
        return p
    info = {"parent": None, "textures": {}, "scalars": {}, "blend": None}
    materials[p] = info
    try:
        if isinstance(m, unreal.MaterialInstance):
            parent = m.get_editor_property("parent")
            info["parent"] = note_material(parent)
            for n in mel.get_texture_parameter_names(m):
                t = mel.get_material_instance_texture_parameter_value(m, n)
                info["textures"][str(n)] = t.get_path_name() if t else None
            for n in mel.get_scalar_parameter_names(m):
                info["scalars"][str(n)] = round(mel.get_material_instance_scalar_parameter_value(m, n), 3)
        base = m.get_base_material()
        info["blend"] = str(base.get_editor_property("blend_mode")).split(".")[-1]
        if base == m:
            info["base_textures"] = sorted(set(t.get_path_name() for t in mel.get_used_textures(m)))
    except Exception:
        info["error"] = traceback.format_exc().splitlines()[-1]
    return p


def dump_component(c):
    d = {"comp": c.get_name(), "class": c.get_class().get_name()}
    if isinstance(c, unreal.StaticMeshComponent):
        mesh = c.get_editor_property("static_mesh")
        if mesh is None:
            return None
        b = mesh.get_bounding_box()
        d["mesh"] = mesh.get_path_name().split(".")[0]
        d["bounds"] = [round(b.min.x), round(b.min.y), round(b.min.z), round(b.max.x), round(b.max.y), round(b.max.z)]
        d["xf"] = xf(c.get_world_transform())
        d["mats"] = [note_material(m) for m in c.get_materials()]
        d["overrides"] = [note_material(m) if m else None for m in c.get_editor_property("override_materials")]
        d["coll"] = str(c.get_collision_profile_name())
        if isinstance(c, unreal.InstancedStaticMeshComponent):
            n = c.get_instance_count()
            d["instances"] = [xf(c.get_instance_transform(i, True)) for i in range(n)]
        return d
    if isinstance(c, unreal.DecalComponent):
        s = c.get_editor_property("decal_size")
        d["decal"] = note_material(c.get_decal_material())
        d["size"] = [round(s.x), round(s.y), round(s.z)]
        d["xf"] = xf(c.get_world_transform())
        d["sort"] = c.get_editor_property("sort_order")
        return d
    return None


for path in MAPS:
    name = path.split("/")[-1]
    try:
        say("loading " + path)
        world = unreal.EditorLoadingAndSavingUtils.load_map(path)
        actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
        say("%s: %d actors" % (name, len(actors)))
        rows, errors = [], []
        for a in actors:
            try:
                comps = [d for d in (dump_component(c) for c in a.get_components_by_class(unreal.SceneComponent)) if d]
                if not comps:
                    continue
                rows.append({"actor": a.get_name(), "label": a.get_actor_label(), "class": a.get_class().get_path_name(),
                             "folder": str(a.get_folder_path()), "xf": xf(a.get_actor_transform()), "comps": comps})
            except Exception:
                if len(errors) < 30:
                    errors.append(a.get_name() + ": " + traceback.format_exc().splitlines()[-1])
        with open(os.path.join(OUT, "dump_%s.json" % name), "w") as f:
            json.dump({"map": path, "actors": rows, "errors": errors}, f, separators=(",", ":"))
        say("%s: wrote %d actors with meshes or decals, %d errors" % (name, len(rows), len(errors)))
    except Exception:
        say("FAILED %s: %s" % (path, traceback.format_exc()))

with open(os.path.join(OUT, "dump_materials.json"), "w") as f:
    json.dump(materials, f, indent=0)
say("materials: %d" % len(materials))
