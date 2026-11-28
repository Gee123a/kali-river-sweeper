#if UNITY_EDITOR
using System;
using System.Collections.Generic;
using UnityEditor;
using UnityEngine;
using KaliRiverSweeper.Core;

namespace KaliRiverSweeper.Editor
{
    public static class KaliNpcBuilder
    {
        private const string VillagerFbxPath = "Assets/_Project/Rigging/SK_VillagerNPC.fbx";
        private const string VillagerBinFbxPath = "Assets/_Project/Rigging/SM_Villager_Bin.fbx";
        private const float ShallowEdgeMarginMapUnits = 14f; // 1.75m from river edge stays out of boat lane
        private const string RiggingDir = "Assets/_Project/Rigging/";
        private const string RodFbxPath = RiggingDir + "SM_Villager_FishingRod.fbx";
        private const string BareFbxPath = RiggingDir + "SK_VillagerNPC_Bare.fbx";
        private const string SarungFbxPath = RiggingDir + "SK_VillagerNPC_Sarung.fbx";
        private const float RodTipLocalZ = 1.75f; // tip of SM_Villager_FishingRod.fbx (grip at origin)
        private const string PakRtGroupId = "npc_pak_rt_spawn";
        // Map points from kali-river-map.json: item_32 Player Spawn, item_33 Dermaga Awal, item_36 Bank Sampah.
        private static readonly Vector2 PlayerSpawnMap = new Vector2(310f, 1210f);
        private static readonly Vector2[] PakRtKeepClearMap = { new Vector2(378f, 1210f), new Vector2(195f, 1185f) };

        public struct NpcGroupSpec
        {
            public string id;
            public string role;
            public float x;
            public float y;
            public int count;
            public float radius;
            public int seed;
        }

        public struct ExpandedNpc
        {
            public string groupId;
            public AmbientNpcRole role;
            public AmbientNpcSubBehavior subBehavior;
            public Vector3 worldPos;
            public float yawDeg;
            public float uniformScale;
            public float phaseOffset;
            public Color clothingTint;
            public bool onJetty;
            public bool hasLaundryProp;
            public Vector3 chaseAxisWorld;
            public float chaseRadius;
            public Vector3 jumpWaterPos;
        }

        private struct JettyInfo
        {
            public Vector3 pos;
            public float yawDeg;
        }

        private static readonly Color[] ClothingTints =
        {
            new Color(1.00f, 1.00f, 1.00f, 1f),
            new Color(0.84f, 0.90f, 1.04f, 1f),
            new Color(1.06f, 0.96f, 0.70f, 1f),
            new Color(0.78f, 0.96f, 0.80f, 1f),
            new Color(0.94f, 0.76f, 0.84f, 1f),
            new Color(0.82f, 0.74f, 0.64f, 1f)
        };

        private struct NamedVillager
        {
            public string name;
            public bool isEsTehSeller;
            public string body;
            public string accessory;
            public string palette;
            public float scale;
        }

        // ponytail: one named villager per group (first spawned member); other members keep the default look.
        private static readonly Dictionary<string, NamedVillager> NamedVillagerByGroup = new Dictionary<string, NamedVillager>
        {
            { "npc_washer_west_mid", new NamedVillager { name = "Bu Siti", body = BareFbxPath, accessory = "SM_Villager_Hat_Kerudung.fbx", palette = "T_Villager_Palette_BuSiti.png", scale = 1.0f } },
            { "npc_fisher_jetty2", new NamedVillager { name = "Pak Darto", body = VillagerFbxPath, accessory = null, palette = "T_Villager_Palette_PakDarto.png", scale = 1.0f } },
            { "npc_kids_west_jetty3", new NamedVillager { name = "Raka", body = BareFbxPath, accessory = "SM_Villager_Hat_Topi.fbx", palette = "T_Villager_Palette_Raka.png", scale = 0.64f } },
            { "npc_chatter_west_warung", new NamedVillager { name = "Mbok Nah", isEsTehSeller = true, body = SarungFbxPath, accessory = "SM_Villager_Hair_Konde.fbx", palette = "T_Villager_Palette_MbokNah.png", scale = 0.97f } },
            { PakRtGroupId, new NamedVillager { name = "Pak RT", body = SarungFbxPath, accessory = "SM_Villager_Hat_Peci.fbx", palette = "T_Villager_Palette_PakRT.png", scale = 1.0f } }
        };

        public static bool IsInBoatLane(Vector3 worldPos)
        {
            if (!RiverMath.IsInRiver(worldPos)) return false;
            float mapX = worldPos.x / RiverMath.MapScale + RiverMath.WorldW * 0.5f;
            float mapY = worldPos.z / RiverMath.MapScale + RiverMath.WorldH * 0.5f;
            float cx = RiverMath.RiverCenterMapX(mapY);
            float hw = RiverMath.RiverHalfWidthMap(mapY);
            float maxOffsetFromCenter = Mathf.Max(0f, hw - ShallowEdgeMarginMapUnits);
            return Mathf.Abs(mapX - cx) < maxOffsetFromCenter;
        }

        public static List<ExpandedNpc> ExpandNpcGroups(
            IReadOnlyList<NpcGroupSpec> groups,
            IReadOnlyList<KaliKampungBuilder.ExpandedBuilding> expandedBuildings,
            IReadOnlyList<KaliKampungBuilder.AvoidanceZone> avoidZones,
            IReadOnlyList<KaliKampungBuilder.PathSegment> footpaths)
        {
            var result = new List<ExpandedNpc>();
            if (groups == null || groups.Count == 0) return result;

            var jetties = new List<JettyInfo>();
            if (expandedBuildings != null)
            {
                for (int i = 0; i < expandedBuildings.Count; i++)
                {
                    if (!expandedBuildings[i].hasJetty) continue;
                    jetties.Add(new JettyInfo
                    {
                        pos = expandedBuildings[i].jettyWorldPos,
                        yawDeg = expandedBuildings[i].jettyYawDeg
                    });
                }
            }

            for (int g = 0; g < groups.Count; g++)
            {
                NpcGroupSpec spec = groups[g];
                int targetCount = Mathf.Clamp(spec.count, 1, 12);
                AmbientNpcRole role = ParseRole(spec.role);
                var rng = new System.Random(spec.seed != 0 ? spec.seed : StableHash(spec.id));

                Vector3 centerWorld = RiverMath.ToWorld3D(spec.x, spec.y, 0f);
                Vector2 centerXZ = new Vector2(centerWorld.x, centerWorld.z);
                bool hasJetty = TryFindNearestJetty(centerXZ, jetties, 4.5f, out JettyInfo jetty);

                for (int i = 0; i < targetCount; i++)
                {
                    float tintRoll = (float)rng.NextDouble();
                    float scaleRoll = (float)rng.NextDouble();
                    float jitterA = (float)rng.NextDouble();
                    float jitterB = (float)rng.NextDouble();

                    Color tint = ClothingTints[Mathf.Clamp((int)(tintRoll * ClothingTints.Length), 0, ClothingTints.Length - 1)];
                    float scale = role == AmbientNpcRole.Kids
                        ? Mathf.Lerp(0.60f, 0.68f, scaleRoll)
                        : Mathf.Lerp(0.95f, 1.04f, scaleRoll);
                    float phase = (float)(rng.NextDouble() * 2.5);

                    Vector3 pos;
                    float yawDeg;
                    AmbientNpcSubBehavior subBehavior = AmbientNpcSubBehavior.Standard;
                    bool onJetty = false;
                    bool hasLaundryProp = false;
                    Vector3 chaseAxis = Vector3.forward;
                    float chaseRad = 0.65f;
                    Vector3 jumpTarget = Vector3.zero;

                    if (role == AmbientNpcRole.Fisher && hasJetty)
                    {
                        onJetty = true;
                        Quaternion jRot = Quaternion.Euler(0f, jetty.yawDeg, 0f);
                        bool seated = (i == 0);
                        subBehavior = seated ? AmbientNpcSubBehavior.SeatedFisher : AmbientNpcSubBehavior.StandingFisher;

                        // Local +X on jetty extends toward the river; +Z sits clear of center ladder (-0.45..+0.45) and moored boat (-Z).
                        Vector3 localOffset = seated
                            ? new Vector3(2.22f, 0f, 0.62f)
                            : new Vector3(0.70f - (i - 1) * 0.65f, 0f, -0.52f);
                        pos = jetty.pos + jRot * localOffset;
                        pos.y = 1.46f;

                        Vector3 riverDir = jRot * Vector3.right;
                        float baseRiverYaw = Mathf.Atan2(riverDir.x, riverDir.z) * Mathf.Rad2Deg;
                        yawDeg = baseRiverYaw + (seated ? 14f : -42f + (jitterA - 0.5f) * 10f);
                    }
                    else if (role == AmbientNpcRole.Fisher)
                    {
                        pos = ComputeBankOrShorelinePoint(spec.x, spec.y, i, targetCount, spec.radius, 0f, -11.2f);
                        pos.y = 1.38f;
                        yawDeg = ComputeRiverFacingYawZ(new Vector2(pos.x, pos.z));
                        subBehavior = AmbientNpcSubBehavior.StandingFisher;
                    }
                    else if (role == AmbientNpcRole.Kids && hasJetty)
                    {
                        Quaternion jRot = Quaternion.Euler(0f, jetty.yawDeg, 0f);
                        bool isJumper = (i == 0);
                        if (isJumper)
                        {
                            onJetty = true;
                            subBehavior = AmbientNpcSubBehavior.KidJettyJumper;
                            pos = jetty.pos + jRot * new Vector3(0.75f, 0f, -0.55f);
                            pos.y = 1.46f;

                            Vector3 riverDir = jRot * Vector3.right;
                            yawDeg = Mathf.Atan2(riverDir.x, riverDir.z) * Mathf.Rad2Deg - 32f;

                            // Keep jumper Edit Mode preview grounded cleanly on jetty edge; jump riverward+sideways into shallow edge clear of boat lane.
                            phase = 0.0f;
                            jumpTarget = ClampOutsideBoatLane(jetty.pos + jRot * new Vector3(1.65f, 0f, -1.75f));
                            jumpTarget.y = -0.35f;
                        }
                        else
                        {
                            onJetty = false;
                            subBehavior = AmbientNpcSubBehavior.KidWader;
                            float sideMapY = spec.y + 18f + (i - 1) * 9f;
                            pos = ComputeShorelineSpreadPoint(spec.x, sideMapY, 0, 1, 0f, shallowMapOffset: 2.2f, 0.5f);
                            pos.y = -0.28f;
                            Vector2 toJetty = new Vector2(jetty.pos.x - pos.x, jetty.pos.z - pos.z);
                            yawDeg = toJetty.sqrMagnitude > 0.001f
                                ? Mathf.Atan2(toJetty.x, toJetty.y) * Mathf.Rad2Deg
                                : ComputeRiverFacingYawZ(new Vector2(pos.x, pos.z));
                        }
                    }
                    else if (role == AmbientNpcRole.Kids)
                    {
                        bool isChaser = (i >= 1 && targetCount >= 2);
                        if (isChaser)
                        {
                            pos = ComputeShorelineSpreadPoint(spec.x, spec.y, 1, 3, spec.radius, shallowMapOffset: 2.5f, 0.5f);
                            pos.y = -0.31f;
                            subBehavior = AmbientNpcSubBehavior.KidChaser;
                            chaseAxis = ComputeShorelineTangent(pos.z);
                            chaseRad = Mathf.Clamp(spec.radius * 0.72f, 0.65f, 0.90f);
                            phase = (i == 1) ? 0.0f : 0.75f;
                            yawDeg = Mathf.Atan2(chaseAxis.x, chaseAxis.z) * Mathf.Rad2Deg;
                        }
                        else
                        {
                            pos = ComputeShorelineSpreadPoint(spec.x, spec.y, i, targetCount, spec.radius, shallowMapOffset: 2.4f, jitterA);
                            pos.y = -0.30f;
                            Vector2 pXZ = new Vector2(pos.x, pos.z);
                            yawDeg = ComputeRiverFacingYawZ(pXZ) + (jitterB - 0.5f) * 55f;
                            subBehavior = AmbientNpcSubBehavior.KidWader;
                        }
                    }
                    else if (role == AmbientNpcRole.Washer)
                    {
                        pos = ComputeShorelineSpreadPoint(spec.x, spec.y, i, targetCount, spec.radius, shallowMapOffset: -1.2f, jitterA);
                        pos.y = 0.15f;
                        yawDeg = ComputeRiverFacingYawZ(new Vector2(pos.x, pos.z)) + (jitterB - 0.5f) * 14f;
                        subBehavior = AmbientNpcSubBehavior.CrouchedWasher;
                        hasLaundryProp = (i == 0);
                    }
                    else
                    {
                        // Spread chatters along Z (parallel to riverbank) so both stand level at y = 1.40m.
                        float angle = (i / (float)Mathf.Max(1, targetCount)) * Mathf.PI * 2f + 1.35f;
                        float rad = Mathf.Clamp(spec.radius * 0.72f, 0.42f, 0.65f);
                        pos = new Vector3(
                            centerWorld.x + Mathf.Cos(angle) * rad,
                            KaliKampungBuilder.BankTopY,
                            centerWorld.z + Mathf.Sin(angle) * rad);
                        Vector3 toCenter = (centerWorld - pos);
                        toCenter.y = 0f;
                        yawDeg = toCenter.sqrMagnitude > 0.0001f
                            ? Mathf.Atan2(toCenter.x, toCenter.z) * Mathf.Rad2Deg
                            : 0f;

                        bool carryLaundry = string.Equals(spec.id, "npc_chatter_east_warung", StringComparison.Ordinal) && i == 1;
                        subBehavior = carryLaundry ? AmbientNpcSubBehavior.ChatterBinCarrier : AmbientNpcSubBehavior.Standard;
                    }

                    Vector2 finalXZ = new Vector2(pos.x, pos.z);
                    if (!IsClearOfAvoidZones(finalXZ, avoidZones, 2.0f) ||
                        !IsClearOfFootpaths(finalXZ, footpaths, 0.8f) ||
                        (!onJetty && IsInBoatLane(pos)))
                    {
                        continue;
                    }

                    if (subBehavior == AmbientNpcSubBehavior.KidChaser)
                    {
                        Vector3 pPlus = pos + chaseAxis * chaseRad;
                        Vector3 pMinus = pos - chaseAxis * chaseRad;
                        if (IsInBoatLane(pPlus) || IsInBoatLane(pMinus) ||
                            !IsClearOfAvoidZones(new Vector2(pPlus.x, pPlus.z), avoidZones, 1.5f) ||
                            !IsClearOfAvoidZones(new Vector2(pMinus.x, pMinus.z), avoidZones, 1.5f))
                        {
                            chaseRad = 0.45f;
                        }
                    }

                    result.Add(new ExpandedNpc
                    {
                        groupId = spec.id,
                        role = role,
                        subBehavior = subBehavior,
                        worldPos = pos,
                        yawDeg = yawDeg,
                        uniformScale = scale,
                        phaseOffset = phase,
                        clothingTint = tint,
                        onJetty = onJetty,
                        hasLaundryProp = hasLaundryProp,
                        chaseAxisWorld = chaseAxis,
                        chaseRadius = chaseRad,
                        jumpWaterPos = jumpTarget
                    });
                }
            }

            AddPakRtSpawnNpc(result, avoidZones, footpaths);
            return result;
        }

        // Pak RT: one extra standing villager 4.5-9 m from the player spawn. First compass candidate that is
        // on land, off footpaths/avoid zones, and away from the spawn->Dermaga and spawn->Bank Sampah lines.
        private static void AddPakRtSpawnNpc(
            List<ExpandedNpc> result,
            IReadOnlyList<KaliKampungBuilder.AvoidanceZone> avoidZones,
            IReadOnlyList<KaliKampungBuilder.PathSegment> footpaths)
        {
            Vector3 spawn = RiverMath.ToWorld3D(PlayerSpawnMap.x, PlayerSpawnMap.y, 0f);
            Vector2 spawnXZ = new Vector2(spawn.x, spawn.z);
            // ponytail: rings 4.5-9 m, 12 bearings: the spawn dock/footpaths reject every 4.5 m candidate.
            for (float radius = 4.5f; radius <= 9f; radius += 1.5f)
            for (int k = 0; k < 12; k++)
            {
                float ang = k * Mathf.PI / 6f;
                Vector3 p = spawn + new Vector3(Mathf.Cos(ang), 0f, Mathf.Sin(ang)) * radius;
                Vector2 xz = new Vector2(p.x, p.z);
                if (RiverMath.IsInRiver(p) || !IsClearOfAvoidZones(xz, avoidZones, 2.0f) || !IsClearOfFootpaths(xz, footpaths, 2.0f))
                {
                    continue;
                }

                bool blocksKeepClear = false;
                for (int m = 0; m < PakRtKeepClearMap.Length; m++)
                {
                    Vector3 keep = RiverMath.ToWorld3D(PakRtKeepClearMap[m].x, PakRtKeepClearMap[m].y, 0f);
                    Vector2 keepXZ = new Vector2(keep.x, keep.z);
                    Vector2 ab = keepXZ - spawnXZ;
                    float t = Mathf.Clamp01(Vector2.Dot(xz - spawnXZ, ab) / ab.sqrMagnitude);
                    if (Vector2.Distance(xz, spawnXZ + t * ab) < 2.5f) blocksKeepClear = true;
                }
                if (blocksKeepClear) continue;

                Vector3 toSpawn = spawn - p;
                result.Add(new ExpandedNpc
                {
                    groupId = PakRtGroupId,
                    role = AmbientNpcRole.Chatter,
                    subBehavior = AmbientNpcSubBehavior.Standard,
                    worldPos = p,
                    yawDeg = Mathf.Atan2(toSpawn.x, toSpawn.z) * Mathf.Rad2Deg,
                    uniformScale = 1f,
                    phaseOffset = 0f,
                    clothingTint = Color.white
                });
                return;
            }
        }

        internal static int SpawnNpcGroups(
            IReadOnlyList<ExpandedNpc> npcs,
            Transform parent,
            KaliMapBackdropBuilder.SceneAssetCache assetCache)
        {
            if (npcs == null || parent == null) return 0;

            EnsureHumanoid(BareFbxPath);
            EnsureHumanoid(SarungFbxPath);
            GameObject villagerPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(VillagerFbxPath);
            GameObject binPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(VillagerBinFbxPath);
            GameObject rodPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(RodFbxPath);
            Dictionary<string, AnimationClip> clips = LoadVillagerClips();

            bool fallbackMode = villagerPrefab == null;
            if (fallbackMode)
            {
                Debug.LogWarning("[KALI] SK_VillagerNPC.fbx not found; spawning low-poly ambient NPC stand-ins.");
            }

            var namedGroups = new HashSet<string>();
            Material rodLineMat = KaliMapBackdropBuilder.GetSharedTintMaterial(assetCache, new Color(0.14f, 0.14f, 0.16f));
            Material rodBobberMat = KaliMapBackdropBuilder.GetSharedTintMaterial(assetCache, new Color(0.86f, 0.24f, 0.18f));
            Material standInMat = KaliMapBackdropBuilder.GetSharedTintMaterial(assetCache, new Color(0.75f, 0.42f, 0.34f));

            float initialWaterY = RiverGameManager.BaseWaterLevelY + 4 * RiverGameManager.WaterRisePerPiledUnit;

            int spawned = 0;
            for (int i = 0; i < npcs.Count; i++)
            {
                ExpandedNpc spec = npcs[i];
                bool named = NamedVillagerByGroup.TryGetValue(spec.groupId, out NamedVillager look) && namedGroups.Add(spec.groupId);
                GameObject bodyPrefab = named ? (AssetDatabase.LoadAssetAtPath<GameObject>(look.body) ?? villagerPrefab) : villagerPrefab;
                GameObject npcGo = fallbackMode
                    ? CreateStandInVillager(parent, standInMat)
                    : (GameObject)PrefabUtility.InstantiatePrefab(bodyPrefab, parent);

                npcGo.name = $"NPC_{spec.role}_{i + 1:00}_{spec.groupId}";
                Texture2D palette = null;
                if (named)
                {
                    spec.uniformScale = look.scale;
                    spec.clothingTint = Color.white; // palette texture carries the colours
                    if (!fallbackMode) palette = ApplyNamedLook(npcGo, look);
                }
                StripAllColliders(npcGo);

                Vector3 groundedPos = ResolveGroundedPosition(spec);
                Quaternion baseRot = Quaternion.Euler(0f, spec.yawDeg, 0f);
                npcGo.transform.SetPositionAndRotation(groundedPos, baseRot);
                npcGo.transform.localScale = new Vector3(spec.uniformScale, spec.uniformScale, spec.uniformScale);

                Animator anim = npcGo.GetComponent<Animator>();
                if (anim == null && !fallbackMode)
                {
                    anim = npcGo.AddComponent<Animator>();
                }
                if (anim != null)
                {
                    anim.cullingMode = AnimatorCullingMode.CullUpdateTransforms;
                    anim.applyRootMotion = false;
                }

                Transform propRoot = null;
                if (spec.subBehavior == AmbientNpcSubBehavior.ChatterBinCarrier && binPrefab != null)
                {
                    Transform carrySocket = npcGo.transform.Find("VillagerRig/Hips/Spine/Chest/Socket_Carry");
                    if (carrySocket != null)
                    {
                        GameObject bin = (GameObject)PrefabUtility.InstantiatePrefab(binPrefab, carrySocket);
                        bin.name = "NPC_CarryBin";
                        bin.transform.localPosition = Vector3.zero;
                        bin.transform.localRotation = Quaternion.identity;
                        StripAllColliders(bin);
                        propRoot = bin.transform;
                    }
                }
                else if (spec.role == AmbientNpcRole.Washer && spec.hasLaundryProp && binPrefab != null)
                {
                    Vector3 sideOffset = baseRot * new Vector3(0.42f, 0f, 0.14f);
                    Vector3 binPos = groundedPos + sideOffset;
                    if (TryRaycastSolidGround(binPos, out float binGroundY, out string _))
                    {
                        binPos.y = Mathf.Max(-0.10f, binGroundY - 0.045f);
                    }
                    GameObject tub = (GameObject)PrefabUtility.InstantiatePrefab(binPrefab, parent);
                    tub.name = $"NPC_WashTub_{i + 1:00}";
                    tub.transform.SetPositionAndRotation(binPos, baseRot * Quaternion.Euler(0f, 22f, 0f));
                    tub.transform.localScale = new Vector3(1.05f, 0.82f, 1.05f);
                    StripAllColliders(tub);
                    propRoot = tub.transform;
                }

                Vector3 resolvedJumpWater = spec.jumpWaterPos;
                if (spec.subBehavior == AmbientNpcSubBehavior.KidJettyJumper)
                {
                    if (TryRaycastSolidGround(resolvedJumpWater, out float waterBedY, out string _))
                    {
                        resolvedJumpWater.y = Mathf.Clamp(waterBedY, -0.45f, 0.05f);
                    }
                }

                KaliAmbientNpc npc = npcGo.AddComponent<KaliAmbientNpc>();
                npc.groupId = spec.groupId;
                npc.role = spec.role;
                npc.subBehavior = spec.subBehavior;
                npc.anchorWorldPos = groundedPos;
                npc.anchorWorldRot = baseRot;
                npc.baseUniformScale = spec.uniformScale;
                npc.phaseOffset = spec.phaseOffset;
                npc.clothingTint = spec.clothingTint;
                npc.idleClip = ClipNamed(clips, "Idle");
                npc.carryBinClip = ClipNamed(clips, "CarryBin");
                npc.throwTrashClip = ClipNamed(clips, "ThrowTrash");
                npc.poseClip = PoseClipFor(spec.subBehavior, clips);
                npc.talkClip = spec.subBehavior == AmbientNpcSubBehavior.Standard ? ClipNamed(clips, "Talk_Gesture") : null;
                npc.paletteTexture = palette;
                npc.propRoot = propRoot;
                npc.chaseAxisWorld = spec.chaseAxisWorld;
                npc.chaseRadius = spec.chaseRadius;
                npc.jumpWaterPos = resolvedJumpWater;
                // Bare/Sarung bodies sink under base-rig clips: lift washers and standing chatter so soles meet the ground.
                if (spec.subBehavior == AmbientNpcSubBehavior.CrouchedWasher || spec.subBehavior == AmbientNpcSubBehavior.Standard)
                {
                    npc.SettleFeetToGround(npc.poseClip);
                }
                npc.ApplyEditorPreviewPose();

                KaliNpcInteractable talk = npcGo.AddComponent<KaliNpcInteractable>();
                if (named)
                {
                    talk.npcName = look.name;
                    talk.isEsTehSeller = look.isEsTehSeller;
                }

                if (spec.role == AmbientNpcRole.Fisher && rodPrefab != null)
                {
                    Transform socket = npcGo.transform.Find("VillagerRig/Hips/Spine/Chest/RightShoulder/RightUpperArm/RightLowerArm/RightHand/Socket_RightHand");
                    AttachFishingRod(
                        socket != null ? socket : npcGo.transform,
                        npcGo.transform,
                        socket != null,
                        initialWaterY,
                        rodPrefab,
                        rodLineMat,
                        rodBobberMat,
                        out Transform rodPivot,
                        out Transform rodTip,
                        out Transform rodLine,
                        out Transform rodBobber);
                    npc.rodPivot = rodPivot;
                    npc.rodTip = rodTip;
                    npc.rodLine = rodLine;
                    npc.rodBobber = rodBobber;
                    npc.ApplyEditorPreviewPose();
                }

                spawned++;
            }

            return spawned;
        }

        private static Vector3 ResolveGroundedPosition(ExpandedNpc spec)
        {
            Vector3 p = spec.worldPos;
            if (!TryRaycastSolidGround(p, out float groundY, out string colliderName))
            {
                return p;
            }

            // Jetty_Deck collider top sits at 1.525m while visual plank surface is 1.46m.
            if (string.Equals(colliderName, "Jetty_Deck", StringComparison.Ordinal))
            {
                p.y = 1.46f;
                return p;
            }

            p.y = groundY;
            return p;
        }

        private static bool TryRaycastSolidGround(Vector3 xzPos, out float groundY, out string colliderName)
        {
            Vector3 origin = new Vector3(xzPos.x, 12f, xzPos.z);
            if (Physics.Raycast(origin, Vector3.down, out RaycastHit hit, 25f, ~0, QueryTriggerInteraction.Ignore))
            {
                groundY = hit.point.y;
                colliderName = hit.collider != null ? hit.collider.name : string.Empty;
                return true;
            }
            groundY = xzPos.y;
            colliderName = string.Empty;
            return false;
        }

        private static void AttachFishingRod(
            Transform parent,
            Transform npcRoot,
            bool useSocketTransform,
            float waterTargetY,
            GameObject rodPrefab,
            Material lineMat,
            Material bobberMat,
            out Transform rodPivot,
            out Transform rodTip,
            out Transform rodLine,
            out Transform rodBobber)
        {
            GameObject pivot = new GameObject("NPC_FishingRod");
            pivot.transform.SetParent(parent, worldPositionStays: false);
            pivot.transform.localPosition = useSocketTransform ? Vector3.zero : new Vector3(0.22f, 0.85f, 0.15f);
            // Align pivot gently angled forward over water with NPC forward (+Z).
            pivot.transform.rotation = npcRoot.rotation * Quaternion.Euler(-8f, 0f, 0f);

            // Rod FBX is built for Socket_RightHand: grip at origin, tip at local +Z. Zero local transform under the pivot.
            GameObject pole = (GameObject)PrefabUtility.InstantiatePrefab(rodPrefab, pivot.transform);
            pole.name = "Rod_Bamboo";
            pole.transform.localPosition = Vector3.zero;
            pole.transform.localRotation = Quaternion.identity;
            StripAllColliders(pole);

            GameObject tipGo = new GameObject("Rod_Tip");
            tipGo.transform.SetParent(pivot.transform, worldPositionStays: false);
            tipGo.transform.localPosition = new Vector3(0f, 0f, RodTipLocalZ);

            Vector3 tipWorld = tipGo.transform.position;
            float clampedBobberY = Mathf.Min(waterTargetY, tipWorld.y - 0.35f);
            Vector3 bobberWorld = new Vector3(tipWorld.x, clampedBobberY, tipWorld.z);
            float lineLen = Mathf.Max(0.25f, tipWorld.y - bobberWorld.y);
            float npcScale = Mathf.Max(0.25f, npcRoot.localScale.y);

            // Vertical line hanging straight down toward the water from rod tip
            GameObject line = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            line.name = "Rod_Line";
            line.transform.SetParent(pivot.transform, worldPositionStays: false);
            line.transform.position = (tipWorld + bobberWorld) * 0.5f;
            line.transform.rotation = Quaternion.identity;
            line.transform.localScale = new Vector3(0.008f, (lineLen / npcScale) * 0.5f, 0.008f);
            line.GetComponent<Renderer>().sharedMaterial = lineMat;
            StripAllColliders(line);

            GameObject bobber = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            bobber.name = "Rod_Bobber";
            bobber.transform.SetParent(pivot.transform, worldPositionStays: false);
            bobber.transform.position = bobberWorld;
            bobber.transform.rotation = Quaternion.identity;
            bobber.transform.localScale = new Vector3(0.055f, 0.075f, 0.055f);
            bobber.GetComponent<Renderer>().sharedMaterial = bobberMat;
            StripAllColliders(bobber);

            rodPivot = pivot.transform;
            rodTip = tipGo.transform;
            rodLine = line.transform;
            rodBobber = bobber.transform;
        }

        private static Vector3 ClampOutsideBoatLane(Vector3 worldPos)
        {
            if (!IsInBoatLane(worldPos)) return worldPos;
            float mapX = worldPos.x / RiverMath.MapScale + RiverMath.WorldW * 0.5f;
            float mapY = worldPos.z / RiverMath.MapScale + RiverMath.WorldH * 0.5f;
            float cx = RiverMath.RiverCenterMapX(mapY);
            float hw = RiverMath.RiverHalfWidthMap(mapY);
            float safeOffset = Mathf.Max(2f, hw - ShallowEdgeMarginMapUnits + 2.5f);
            float clampedMapX = mapX >= cx ? (cx + safeOffset) : (cx - safeOffset);
            return RiverMath.ToWorld3D(clampedMapX, mapY, worldPos.y);
        }

        // Variant bodies carry no animation takes, so they must be Humanoid to retarget the SK_VillagerNPC clips.
        private static void EnsureHumanoid(string path)
        {
            ModelImporter importer = AssetImporter.GetAtPath(path) as ModelImporter;
            if (importer == null || importer.animationType == ModelImporterAnimationType.Human) return;
            importer.animationType = ModelImporterAnimationType.Human;
            importer.avatarSetup = ModelImporterAvatarSetup.CreateFromThisModel;
            importer.SaveAndReimport();
        }

        // Accessory spawn only; the palette is applied per renderer by KaliAmbientNpc (MaterialPropertyBlock).
        private static Texture2D ApplyNamedLook(GameObject npcGo, NamedVillager look)
        {
            if (look.accessory != null)
            {
                GameObject accPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(RiggingDir + look.accessory);
                Transform head = npcGo.transform.Find("VillagerRig/Hips/Spine/Chest/Neck/Head");
                if (accPrefab != null && head != null)
                {
                    GameObject acc = (GameObject)PrefabUtility.InstantiatePrefab(accPrefab, head);
                    acc.transform.localPosition = Vector3.zero;
                    acc.transform.localRotation = Quaternion.identity;
                    acc.transform.localScale = Vector3.one;
                }
            }

            return AssetDatabase.LoadAssetAtPath<Texture2D>(RiggingDir + "Textures/" + look.palette);
        }

        private static AnimationClip ClipNamed(Dictionary<string, AnimationClip> clips, string name)
        {
            return clips.TryGetValue(name, out AnimationClip clip) ? clip : null;
        }

        // Role clip per sub-behaviour (README "Ambient NPC clips"); null keeps the procedural fallback.
        private static AnimationClip PoseClipFor(AmbientNpcSubBehavior sub, Dictionary<string, AnimationClip> clips)
        {
            switch (sub)
            {
                case AmbientNpcSubBehavior.SeatedFisher: return ClipNamed(clips, "Anim_Fisher_SittingCast");
                case AmbientNpcSubBehavior.StandingFisher: return ClipNamed(clips, "Anim_Fisher_StandingIdle");
                case AmbientNpcSubBehavior.CrouchedWasher: return ClipNamed(clips, "Anim_Washer_CrouchedScrub");
                case AmbientNpcSubBehavior.KidWader: return ClipNamed(clips, "Anim_Kid_WadeShallow");
                case AmbientNpcSubBehavior.KidChaser: return ClipNamed(clips, "Anim_Kid_Splash");
                case AmbientNpcSubBehavior.KidJettyJumper: return ClipNamed(clips, "Anim_Kid_JettyJump");
                case AmbientNpcSubBehavior.ChatterBinCarrier: return ClipNamed(clips, "CarryBin");
                default: return ClipNamed(clips, "Anim_Chatter_TalkingIdle");
            }
        }

        private static GameObject CreateStandInVillager(Transform parent, Material mat)
        {
            GameObject root = new GameObject("StandInVillager");
            root.transform.SetParent(parent, worldPositionStays: false);

            GameObject body = GameObject.CreatePrimitive(PrimitiveType.Capsule);
            body.name = "Body";
            body.transform.SetParent(root.transform, worldPositionStays: false);
            body.transform.localPosition = new Vector3(0f, 0.72f, 0f);
            body.transform.localScale = new Vector3(0.42f, 0.58f, 0.34f);
            body.GetComponent<Renderer>().sharedMaterial = mat;
            StripAllColliders(body);

            GameObject head = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            head.name = "Head";
            head.transform.SetParent(root.transform, worldPositionStays: false);
            head.transform.localPosition = new Vector3(0f, 1.38f, 0f);
            head.transform.localScale = new Vector3(0.28f, 0.30f, 0.28f);
            head.GetComponent<Renderer>().sharedMaterial = mat;
            StripAllColliders(head);

            return root;
        }

        private static void StripAllColliders(GameObject go)
        {
            if (go == null) return;
            Collider[] cols = go.GetComponentsInChildren<Collider>(true);
            for (int i = 0; i < cols.Length; i++)
            {
                if (cols[i] != null) UnityEngine.Object.DestroyImmediate(cols[i]);
            }
        }

        private static Dictionary<string, AnimationClip> LoadVillagerClips()
        {
            var clips = new Dictionary<string, AnimationClip>(StringComparer.Ordinal);
            UnityEngine.Object[] assets = AssetDatabase.LoadAllAssetsAtPath(VillagerFbxPath);
            if (assets == null) return clips;

            for (int i = 0; i < assets.Length; i++)
            {
                AnimationClip clip = assets[i] as AnimationClip;
                if (clip == null || clip.name.StartsWith("__preview__", StringComparison.Ordinal)) continue;
                clips[clip.name] = clip;
            }
            return clips;
        }

        private static AmbientNpcRole ParseRole(string raw)
        {
            if (string.Equals(raw, "kids", StringComparison.OrdinalIgnoreCase)) return AmbientNpcRole.Kids;
            if (string.Equals(raw, "fisher", StringComparison.OrdinalIgnoreCase)) return AmbientNpcRole.Fisher;
            if (string.Equals(raw, "washer", StringComparison.OrdinalIgnoreCase)) return AmbientNpcRole.Washer;
            return AmbientNpcRole.Chatter;
        }

        private static bool TryFindNearestJetty(Vector2 xz, List<JettyInfo> jetties, float maxDist, out JettyInfo match)
        {
            match = default;
            float bestSqr = maxDist * maxDist;
            bool found = false;
            for (int i = 0; i < jetties.Count; i++)
            {
                float dx = xz.x - jetties[i].pos.x;
                float dz = xz.y - jetties[i].pos.z;
                float sqr = dx * dx + dz * dz;
                if (sqr <= bestSqr)
                {
                    bestSqr = sqr;
                    match = jetties[i];
                    found = true;
                }
            }
            return found;
        }

        private static Vector3 ComputeShorelineSpreadPoint(
            float mapX,
            float mapY,
            int index,
            int count,
            float radiusM,
            float shallowMapOffset,
            float jitterRoll)
        {
            float spanZ = Mathf.Max(0.8f, radiusM * 1.4f);
            float t = count <= 1 ? 0f : (index / (float)(count - 1)) - 0.5f;
            float zOffset = t * spanZ * 2f + (jitterRoll - 0.5f) * 0.35f;

            float worldZ = (mapY - RiverMath.WorldH * 0.5f) * RiverMath.MapScale + zOffset;
            float sampleMapY = worldZ / RiverMath.MapScale + RiverMath.WorldH * 0.5f;
            float cx = RiverMath.RiverCenterMapX(sampleMapY);
            float hw = RiverMath.RiverHalfWidthMap(sampleMapY);
            bool isEast = mapX >= cx;

            // shallowMapOffset > 0 pushes slightly into shallow water edge; < 0 pushes onto bank slope
            float targetMapX = isEast
                ? (cx + hw - shallowMapOffset)
                : (cx - hw + shallowMapOffset);

            return RiverMath.ToWorld3D(targetMapX, sampleMapY, 0f);
        }

        private static Vector3 ComputeBankOrShorelinePoint(
            float mapX,
            float mapY,
            int index,
            int count,
            float radiusM,
            float jitterA,
            float shallowMapOffset)
        {
            return ComputeShorelineSpreadPoint(mapX, mapY, index, count, radiusM, shallowMapOffset, jitterA);
        }

        private static Vector3 ComputeShorelineTangent(float worldZ)
        {
            float mapY = worldZ / RiverMath.MapScale + RiverMath.WorldH * 0.5f;
            float cx1 = (RiverMath.RiverCenterMapX(mapY - 8f) - RiverMath.WorldW * 0.5f) * RiverMath.MapScale;
            float cx2 = (RiverMath.RiverCenterMapX(mapY + 8f) - RiverMath.WorldW * 0.5f) * RiverMath.MapScale;
            Vector3 tan = new Vector3(cx2 - cx1, 0f, 2f);
            return tan.normalized;
        }

        private static float ComputeRiverFacingYawZ(Vector2 posXZ)
        {
            float mapY = posXZ.y / RiverMath.MapScale + RiverMath.WorldH * 0.5f;
            float cxWorld = (RiverMath.RiverCenterMapX(mapY) - RiverMath.WorldW * 0.5f) * RiverMath.MapScale;
            Vector2 toRiver = new Vector2(cxWorld - posXZ.x, 0f);
            if (toRiver.sqrMagnitude < 0.0001f) return 0f;
            return Mathf.Atan2(toRiver.x, toRiver.y) * Mathf.Rad2Deg;
        }

        private static bool IsClearOfAvoidZones(Vector2 posXZ, IReadOnlyList<KaliKampungBuilder.AvoidanceZone> zones, float extraClearance)
        {
            if (zones == null) return true;
            for (int i = 0; i < zones.Count; i++)
            {
                KaliKampungBuilder.AvoidanceZone z = zones[i];
                float dx = Mathf.Max(0f, Mathf.Abs(posXZ.x - z.worldCenter.x) - z.halfExtentsXZ.x);
                float dz = Mathf.Max(0f, Mathf.Abs(posXZ.y - z.worldCenter.z) - z.halfExtentsXZ.y);
                float dist = Mathf.Sqrt(dx * dx + dz * dz);
                if (dist < Mathf.Max(extraClearance, 2.0f))
                {
                    return false;
                }
            }
            return true;
        }

        private static bool IsClearOfFootpaths(Vector2 posXZ, IReadOnlyList<KaliKampungBuilder.PathSegment> footpaths, float extraClearance)
        {
            if (footpaths == null) return true;
            for (int i = 0; i < footpaths.Count; i++)
            {
                KaliKampungBuilder.PathSegment seg = footpaths[i];
                Vector2 ab = seg.b - seg.a;
                float abSqr = ab.sqrMagnitude;
                float dist = abSqr < 1e-6f
                    ? Vector2.Distance(posXZ, seg.a)
                    : Vector2.Distance(posXZ, seg.a + Mathf.Clamp01(Vector2.Dot(posXZ - seg.a, ab) / abSqr) * ab);
                if (dist < seg.halfWidthM + extraClearance)
                {
                    return false;
                }
            }
            return true;
        }

        private static int StableHash(string s)
        {
            if (string.IsNullOrEmpty(s)) return 500;
            unchecked
            {
                int hash = 23;
                for (int i = 0; i < s.Length; i++) hash = hash * 31 + s[i];
                return hash == 0 ? 500 : hash;
            }
        }
    }
}
#endif
