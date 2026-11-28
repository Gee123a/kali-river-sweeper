# Lighting

Two builders live here:

- `Editor/KaliLightingBuilder.cs` (Ivan): **KALI > Lighting > Build Sky & Lighting Rig** builds the procedural sky
  (`M_KaliSky`), `VolumeProfiles/VP_KaliSky.asset` and `Prefabs/PF_LightingRig.prefab` (sun + global volume +
  `KaliDayNightCycle`).
- `Editor/KaliLightingPropsBuilder.cs` (JC): **KALI > Lighting > Build Lantern & Beacon Prefabs** builds the two
  lighting props the map importer attaches to buildings.

## Lantern & beacon (JC)

1. Export the meshes and atlas first (Blender 5.x, headless):
   `blender -b --factory-startup -P blender/build_all.py -- --only equipment`
   -> `Props/Equipment/Meshes/SM_Prop_{LanternWarung,WarningBeacon,BeaconRotor}.fbx`
   + `Props/Equipment/Textures/T_Equipment_Atlas_{Albedo,Normal,Mask,Emission}.png`.
2. In Unity: **KALI > Lighting > Build Lantern & Beacon Prefabs**. It creates or updates (GUIDs kept):
   - `Props/Equipment/Materials/M_Equipment_Atlas.mat` (URP Lit; the Emission map is white only on the bulb
     and the lens, so the scripts' `_EmissionColor` animates just those parts)
   - `Prefabs/PF_Lantern_Warung.prefab` (lantern mesh + warm point light + `LanternFlicker`)
   - `Prefabs/PF_WarningBeacon_PintuAir.prefab` (beacon mesh + spinning rotor with amber spot light + `WarningBeaconRotator`)
3. Run the map importer again: `MapJsonImporter` puts `PF_Lantern_Warung` on top of every warung and
   `PF_WarningBeacon_PintuAir` on top of the sluice gate (`AttachOnTopIfPresent`: prefab origin at the roof top,
   bbox max.y + 0.05 m).

Prefab layout: each prefab origin is the mount point, so it stands on the roof. Lantern: foot block and bamboo post
on the origin, arm and bulb 0.28 m forward (+Z), point light at the bulb (0, 0.315, 0.28). Beacon: plate on the
origin, rotor at y 0.085, beam at the reflector centre (rotor-local y 0.055).

If a mesh or the atlas is missing, the builder logs a warning and uses primitives / flat materials with the same layout.
