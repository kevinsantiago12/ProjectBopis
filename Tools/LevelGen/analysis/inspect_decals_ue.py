"""Read-only, headless: exports the Favela wall-decal masks to PNG and lists the decal materials' parameters (parent,
vectors, scalars, textures), to see what each decal is meant to look like. Writes Saved/LevelGen/decals/.

Run: .\\Tools\\AnimAuthoring\\RunUnreal.ps1 .\\Tools\\LevelGen\\analysis\\inspect_decals_ue.py"""
import os

import unreal

OUT = os.path.join(unreal.Paths.project_saved_dir(), "LevelGen", "decals")
os.makedirs(OUT, exist_ok=True)
mel = unreal.MaterialEditingLibrary
D = "/Game/Megapack/Material/Favela/Decals/"


def say(msg):
    unreal.log_warning("[DCL] " + msg)


seen = set()
for name in ("MI_Decal_02", "MI_Decal_05", "MI_Decal_08", "MI_Decal_Dirt_06", "MI_Decal_Dirt_08", "MI_Decal_Dirt_07",
             "MI_Decal_04", "MI_Decal_06", "MI_Decal_07"):
    mi = unreal.load_asset(D + name)
    if not mi:
        say("%s missing" % name)
        continue
    parent = mi.get_editor_property("parent")
    vecs = {str(n): mel.get_material_instance_vector_parameter_value(mi, n) for n in mel.get_vector_parameter_names(mi)}
    scal = {str(n): round(mel.get_material_instance_scalar_parameter_value(mi, n), 3)
            for n in mel.get_scalar_parameter_names(mi)}
    texs = {}
    for n in mel.get_texture_parameter_names(mi):
        t = mel.get_material_instance_texture_parameter_value(mi, n)
        texs[str(n)] = t.get_name() if t else None
        if t and t.get_name() not in seen:
            seen.add(t.get_name())
            task = unreal.AssetExportTask()
            task.object = t
            task.filename = os.path.join(OUT, t.get_name() + ".png")
            task.automated = True
            task.prompt = False
            task.replace_identical = True
            unreal.Exporter.run_asset_export_task(task)
    base = mi.get_base_material()
    say("%s parent=%s domain=%s blend=%s" % (name, parent.get_name() if parent else None,
                                            base.get_editor_property("material_domain"),
                                            base.get_editor_property("blend_mode")))
    say("   vec=%s" % {k: (round(v.r, 2), round(v.g, 2), round(v.b, 2), round(v.a, 2)) for k, v in vecs.items()})
    say("   scal=%s tex=%s" % (scal, texs))
