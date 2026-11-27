# Lighting (JC)

`Editor/KaliLightingBuilder.cs` builds every lighting asset from code (numbers explainable in the Sidang).

1. Export the meshes and atlas first (Blender 5.x, headless):
   `blender -b --factory-startup -P blender/build_all.py -- --only equipment`
   -> `Props/Equipment/Meshes/SM_Prop_{LanternWarung,WarningBeacon,BeaconRotor}.fbx`
   + `Props/Equipment/Textures/T_Equipment_Atlas_{Albedo,Normal,Mask,Emission}.png`.
2. In Unity: **KALI > Lighting > Build All Lighting Assets**. It creates or updates (GUIDs kept):
   - `Profiles/VolumeProfile_GoldenHour.asset`, `Profiles/VolumeProfile_MonsoonStorm.asset`,
     `Profiles/Skybox_GoldenHour.mat`, `Profiles/Skybox_Monsoon.mat`
   - `Props/Equipment/Materials/M_Equipment_Atlas.mat` (URP Lit; the Emission map is white only on the bulb
     and the lens, so the scripts' `_EmissionColor` animates just those parts)
   - `Prefabs/PF_Lantern_Warung.prefab` (lantern mesh + warm point light + `LanternFlicker`)
   - `Prefabs/PF_WarningBeacon_PintuAir.prefab` (beacon mesh + spinning rotor with amber spot light + `WarningBeaconRotator`)
   - `Prefabs/PF_LightingRig.prefab` (sun + Golden Hour / Monsoon volumes + `LightingPresetSwitcher`)
3. Run the map importer again: `MapJsonImporter` loads `PF_LightingRig`, puts `PF_Lantern_Warung` on top of every
   warung and `PF_WarningBeacon_PintuAir` on top of the sluice gate (`AttachOnTopIfPresent`: prefab origin at the
   roof top, bbox max.y + 0.05 m).

Prefab layout: each prefab origin is the mount point, so it stands on the roof. Lantern: foot block and bamboo post
on the origin, arm and bulb 0.28 m forward (+Z), point light at the bulb (0, 0.315, 0.28). Beacon: plate on the
origin, rotor at y 0.085, beam at the reflector centre (rotor-local y 0.055).

If a mesh or the atlas is missing, the builder logs a warning and uses primitives / flat materials with the same layout.

`LightingPresetSwitcher` follows `RiverGameManager.Instance.isMonsoonStorm` (read-only) and blends sun, volumes,
fog and skybox over `transitionSeconds`.
