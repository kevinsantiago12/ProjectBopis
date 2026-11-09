# Pass `arena_cover`, run by gen_level.py in the level's shared namespace (see levels/*.py for the order).
# Arena only: cover, stand-ins and the kiosk (off), and the invisible floor collision slab.
# Split out of the one-file arena generator on 2026-11-08; the code is unchanged.
_mark = len(items)
# --- Cover, stand-ins, kiosk -------------------------------------------------------------------------------------------
def box(label, c, h, folder):
    X1, Y0 = ue(c["x0"], c["y0"])
    X0, Y1 = ue(c["x1"], c["y1"])
    put(label, CUBE, X0, Y0, 0.0, 0, ((X1 - X0) / 100.0, (Y1 - Y0) / 100.0, h / 100.0), folder=folder)


COV = "BackAlleys/Cover"
for c in L["cover"]:
    cxm, cym = ue((c["x0"] + c["x1"]) / 2, (c["y0"] + c["y1"]) / 2)
    if c["id"] == "jeepney":
        box("STANDIN_Jeepney", c, 260, "BackAlleys/StandIns")
    elif c["id"] == "tricycle":
        box("STANDIN_Tricycle", c, 150, "BackAlleys/StandIns")
    elif c["id"].startswith("barrier"):
        long_x = (c["x1"] - c["x0"]) > (c["y1"] - c["y0"])   # SM_Concrete_Block_01's 2.44 m runs along local Y
        put("Cover_" + c["id"], ME + "MiddleEast/SM_Concrete_Block_01", cxm, cym, 2.0, 0 if long_x else 90, folder=COV)
    elif c["id"].startswith("drums"):
        for k, (ox, oy, mesh) in enumerate([(-30, -25, "SM_Barrel_01"), (30, -20, "SM_Barrel_02"), (0, 35, "SM_Barrel_01")]):
            put("Cover_%s_%d" % (c["id"], k), PM + "Barrels_Set_01/" + mesh, cxm + ox, cym + oy, 0.0, k * 47, folder=COV)
    elif c["id"] == "kiosk":   # one storey, shop front facing north (its south side backs onto B19)
        K = "BackAlleys/Kiosk"
        kxf, kyw = ue(c["x0"], c["y0"])
        kxb, kye = ue(c["x1"], c["y1"])
        put("Kiosk_Front", AS + "SM_Shop_A_001", kxf, kye, 0, -90, (320 / 300.0, 1, 1), folder=K)
        put("Kiosk_Back", AS + "SM_HouseWall_A_001", kxb, kyw, 0, 90, (320 / 300.0, 1, 1), folder=K)
        put("Kiosk_West", AS + "SM_HouseWall_A_001_HalfA", kxf, kyw, 0, 180, (240 / 150.0, 1, 1), folder=K)
        put("Kiosk_East", AS + "SM_HouseWall_A_001_HalfA", kxb, kye, 0, 0, (240 / 150.0, 1, 1), folder=K)
        put("Kiosk_Roof", AS + "SM_MetalPlate_C_001", kxb - 20, kyw - 20, 400, 0, (280 / 200.0, 360 / 300.0, 1), folder=K)
        put("Kiosk_Core", CUBE, kxb + 20, kyw + 20, 0, 0, (1.4, 2.8, 3.9), folder=K, mat="interior")
        put("Kiosk_Awning", AS + "SM_Roof_A_002", kxf, kye, 330, -90, folder=K, nocoll=True)

if not COVER:
    del items[_mark:]
# --- Ground: invisible collision slab (the template floor's collision is smaller than it looks) -----------------------
put("Floor_Collision", CUBE, -2700, -3000, -50.0, 0, (54.0, 60.0, 0.495), folder="BackAlleys/Lids", mat="hidden")

