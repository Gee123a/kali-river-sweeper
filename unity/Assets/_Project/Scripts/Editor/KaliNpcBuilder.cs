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
            new Color(0.84f, 0.88f, 1.00f, 1f),
            new Color(1.00f, 0.92f, 0.68f, 1f),
            new Color(0.80f, 0.96f, 0.84f, 1f),
            new Color(1.00f, 0.78f, 0.78f, 1f),
            new Color(0.86f, 0.78f, 0.68f, 1f)
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

                        // Local +X on jetty extends toward the river; +Z sits clear of moored boat (-Z side).
                        Vector3 localOffset = seated
                            ? new Vector3(2.35f, 0f, 0.22f)
                            : new Vector3(0.95f - (i - 1) * 0.75f, 0f, -0.32f);
                        pos = jetty.pos + jRot * localOffset;
                        pos.y = 1.46f;

                        Vector3 riverDir = jRot * Vector3.right;
                        yawDeg = Mathf.Atan2(riverDir.x, riverDir.z) * Mathf.Rad2Deg + (seated ? 0f : (jitterA - 0.5f) * 20f);
                    }
                    else if (role == AmbientNpcRole.Fisher)
                    {
                        pos = ComputeBankOrShorelinePoint(spec.x, spec.y, i, targetCount, spec.radius, 0f, -11.0f);
                        pos.y = 1.38f;
                        yawDeg = ComputeRiverFacingYawZ(new Vector2(pos.x, pos.z));
                        subBehavior = AmbientNpcSubBehavior.StandingFisher;
                    }
                    else if (role == AmbientNpcRole.Kids && hasJetty)
                    {
                        onJetty = true;
                        Quaternion jRot = Quaternion.Euler(0f, jetty.yawDeg, 0f);
                        bool isJumper = (i == 0);
                        subBehavior = isJumper ? AmbientNpcSubBehavior.KidJettyJumper : AmbientNpcSubBehavior.KidWader;

                        Vector3 localOffset = isJumper
                            ? new Vector3(2.35f, 0f, -0.18f)
                            : new Vector3(1.05f, 0f, 0.34f);
                        pos = jetty.pos + jRot * localOffset;
                        pos.y = 1.46f;

                        Vector3 riverDir = jRot * Vector3.right;
                        yawDeg = Mathf.Atan2(riverDir.x, riverDir.z) * Mathf.Rad2Deg;

                        if (isJumper)
                        {
                            // Keep jumper Edit Mode preview grounded cleanly on jetty tip.
                            phase = 0.0f;
                            Vector3 jumpLocal = new Vector3(2.75f, 0f, 1.05f);
                            jumpTarget = jetty.pos + jRot * jumpLocal;
                            jumpTarget.y = -0.22f;
                        }
                    }
                    else if (role == AmbientNpcRole.Kids)
                    {
                        pos = ComputeShorelineSpreadPoint(spec.x, spec.y, i, targetCount, spec.radius, shallowMapOffset: 1.4f, jitterA);
                        pos.y = -0.18f;
                        Vector2 pXZ = new Vector2(pos.x, pos.z);
                        yawDeg = ComputeRiverFacingYawZ(pXZ) + (jitterB - 0.5f) * 65f;
                        subBehavior = (i % 2 == 1) ? AmbientNpcSubBehavior.KidChaser : AmbientNpcSubBehavior.KidWader;
                        chaseAxis = ComputeShorelineTangent(pos.z);
                        chaseRad = Mathf.Clamp(spec.radius * 0.55f, 0.45f, 0.85f);
                    }
                    else if (role == AmbientNpcRole.Washer)
                    {
                        pos = ComputeShorelineSpreadPoint(spec.x, spec.y, i, targetCount, spec.radius, shallowMapOffset: -3.2f, jitterA);
                        pos.y = 0.36f;
                        yawDeg = ComputeRiverFacingYawZ(new Vector2(pos.x, pos.z)) + (jitterB - 0.5f) * 16f;
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

            return result;
        }

        internal static int SpawnNpcGroups(
            IReadOnlyList<ExpandedNpc> npcs,
            Transform parent,
            KaliMapBackdropBuilder.SceneAssetCache assetCache)
        {
            if (npcs == null || parent == null) return 0;

            GameObject villagerPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(VillagerFbxPath);
            GameObject binPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(VillagerBinFbxPath);
            LoadVillagerClips(out AnimationClip idleClip, out AnimationClip carryBinClip, out AnimationClip throwTrashClip);

            bool fallbackMode = villagerPrefab == null;
            if (fallbackMode)
            {
                Debug.LogWarning("[KALI] SK_VillagerNPC.fbx not found; spawning low-poly ambient NPC stand-ins.");
            }

            Material rodBambooMat = KaliMapBackdropBuilder.GetSharedTintMaterial(assetCache, new Color(0.55f, 0.43f, 0.22f));
            Material rodLineMat = KaliMapBackdropBuilder.GetSharedTintMaterial(assetCache, new Color(0.14f, 0.14f, 0.16f));
            Material rodBobberMat = KaliMapBackdropBuilder.GetSharedTintMaterial(assetCache, new Color(0.86f, 0.24f, 0.18f));
            Material standInMat = KaliMapBackdropBuilder.GetSharedTintMaterial(assetCache, new Color(0.75f, 0.42f, 0.34f));

            int spawned = 0;
            for (int i = 0; i < npcs.Count; i++)
            {
                ExpandedNpc spec = npcs[i];
                GameObject npcGo = fallbackMode
                    ? CreateStandInVillager(parent, standInMat)
                    : (GameObject)PrefabUtility.InstantiatePrefab(villagerPrefab, parent);

                npcGo.name = $"NPC_{spec.role}_{i + 1:00}_{spec.groupId}";
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

                Transform rodPivot = null;
                if (spec.role == AmbientNpcRole.Fisher)
                {
                    Transform socket = npcGo.transform.Find("VillagerRig/Hips/Spine/Chest/RightShoulder/RightUpperArm/RightLowerArm/RightHand/Socket_RightHand");
                    rodPivot = AttachFishingRod(socket != null ? socket : npcGo.transform, npcGo.transform, socket != null, rodBambooMat, rodLineMat, rodBobberMat);
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
                    Vector3 sideOffset = baseRot * new Vector3(0.55f, 0f, -0.08f);
                    Vector3 binPos = groundedPos + sideOffset;
                    if (TryRaycastSolidGround(binPos, out float binGroundY, out string _))
                    {
                        binPos.y = Mathf.Max(0.05f, binGroundY);
                    }
                    GameObject tub = (GameObject)PrefabUtility.InstantiatePrefab(binPrefab, parent);
                    tub.name = $"NPC_WashTub_{i + 1:00}";
                    tub.transform.SetPositionAndRotation(binPos, baseRot * Quaternion.Euler(0f, 22f, 0f));
                    tub.transform.localScale = new Vector3(0.82f, 0.65f, 0.82f);
                    StripAllColliders(tub);
                    propRoot = tub.transform;
                }

                Vector3 resolvedJumpWater = spec.jumpWaterPos;
                if (spec.subBehavior == AmbientNpcSubBehavior.KidJettyJumper)
                {
                    if (TryRaycastSolidGround(resolvedJumpWater, out float waterBedY, out string _))
                    {
                        resolvedJumpWater.y = Mathf.Clamp(waterBedY, -0.40f, 0.15f);
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
                npc.idleClip = idleClip;
                npc.carryBinClip = carryBinClip;
                npc.throwTrashClip = throwTrashClip;
                npc.rodPivot = rodPivot;
                npc.propRoot = propRoot;
                npc.chaseAxisWorld = spec.chaseAxisWorld;
                npc.chaseRadius = spec.chaseRadius;
                npc.jumpWaterPos = resolvedJumpWater;
                npc.ApplyEditorPreviewPose();

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

        private static Transform AttachFishingRod(
            Transform parent,
            Transform npcRoot,
            bool useSocketTransform,
            Material bambooMat,
            Material lineMat,
            Material bobberMat)
        {
            GameObject pivot = new GameObject("NPC_FishingRod");
            pivot.transform.SetParent(parent, worldPositionStays: false);
            pivot.transform.localPosition = useSocketTransform ? Vector3.zero : new Vector3(0.22f, 0.85f, 0.15f);
            // Align pivot upright with NPC forward (+Z) so local -Y hangs straight down in world space
            // (Socket_RightHand's own rest frame is rolled 90 deg sideways).
            pivot.transform.rotation = npcRoot.rotation * Quaternion.Euler(-16f, 0f, 0f);

            // Bamboo pole pointing forward (+Z) from hand
            const float rodLen = 2.15f;
            GameObject pole = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            pole.name = "Rod_Bamboo";
            pole.transform.SetParent(pivot.transform, worldPositionStays: false);
            pole.transform.localPosition = new Vector3(0f, 0f, rodLen * 0.45f);
            pole.transform.localRotation = Quaternion.Euler(90f, 0f, 0f);
            pole.transform.localScale = new Vector3(0.032f, rodLen * 0.5f, 0.032f);
            pole.GetComponent<Renderer>().sharedMaterial = bambooMat;
            StripAllColliders(pole);

            // Vertical line hanging straight down toward the water from rod tip
            const float lineLen = 1.65f;
            GameObject line = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            line.name = "Rod_Line";
            line.transform.SetParent(pivot.transform, worldPositionStays: false);
            line.transform.localRotation = Quaternion.Euler(16f, 0f, 0f);
            Vector3 tipLocal = new Vector3(0f, 0f, rodLen * 0.94f);
            Vector3 worldDownInPivot = line.transform.localRotation * Vector3.down;
            line.transform.localPosition = tipLocal + worldDownInPivot * (lineLen * 0.5f);
            line.transform.localScale = new Vector3(0.008f, lineLen * 0.5f, 0.008f);
            line.GetComponent<Renderer>().sharedMaterial = lineMat;
            StripAllColliders(line);

            GameObject bobber = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            bobber.name = "Rod_Bobber";
            bobber.transform.SetParent(pivot.transform, worldPositionStays: false);
            bobber.transform.localPosition = tipLocal + worldDownInPivot * lineLen;
            bobber.transform.localScale = new Vector3(0.055f, 0.075f, 0.055f);
            bobber.GetComponent<Renderer>().sharedMaterial = bobberMat;
            StripAllColliders(bobber);

            return pivot.transform;
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

        private static void LoadVillagerClips(out AnimationClip idle, out AnimationClip carryBin, out AnimationClip throwTrash)
        {
            idle = null;
            carryBin = null;
            throwTrash = null;
            UnityEngine.Object[] assets = AssetDatabase.LoadAllAssetsAtPath(VillagerFbxPath);
            if (assets == null) return;

            for (int i = 0; i < assets.Length; i++)
            {
                AnimationClip clip = assets[i] as AnimationClip;
                if (clip == null || clip.name.StartsWith("__preview__", StringComparison.Ordinal)) continue;
                if (string.Equals(clip.name, "Idle", StringComparison.Ordinal)) idle = clip;
                else if (string.Equals(clip.name, "CarryBin", StringComparison.Ordinal)) carryBin = clip;
                else if (string.Equals(clip.name, "ThrowTrash", StringComparison.Ordinal)) throwTrash = clip;
            }
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
