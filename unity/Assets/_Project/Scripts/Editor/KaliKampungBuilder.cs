#if UNITY_EDITOR
using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text.RegularExpressions;
using UnityEditor;
using UnityEngine;
using KaliRiverSweeper.Core;

namespace KaliRiverSweeper.Editor
{
    public static class KaliKampungBuilder
    {
        public const float BankTopY = 1.40f;

        private const string RumahPrefabPath = "Assets/_Project/Environment/Prefabs/PF_Env_RumahPanggung.prefab";
        private const string WarungPrefabPath = "Assets/_Project/Environment/Prefabs/PF_Env_WarungMadura.prefab";
        private const string BinPrefabPath = "Assets/_Project/Props/Equipment/Prefabs/PF_Prop_TongSampahKampung.prefab";
        private const string SampanPrefabPath = "Assets/_Project/Props/Equipment/Prefabs/PF_Prop_PerahuSampan.prefab";
        private const string RakitPrefabPath = "Assets/_Project/Props/Equipment/Prefabs/PF_Prop_RakitGabus.prefab";
        private const string LanternPrefabPath = "Assets/_Project/Lighting/Prefabs/PF_Lantern_Warung.prefab";
        private const string JettyDeckMatPath = "Assets/_Project/Environment/Materials/M_Env_KayuPapan.mat";
        private const string JettyPilingMatPath = "Assets/_Project/Environment/Materials/M_Env_KayuTiang.mat";

        private static readonly Vector2 QaSwimLaneCenterXZ = new Vector2(-45f, 1.5f);
        private static readonly Regex PointPairRegex = new Regex(
            @"""x""\s*:\s*(-?\d+(?:\.\d+)?)\s*,\s*""y""\s*:\s*(-?\d+(?:\.\d+)?)",
            RegexOptions.Compiled);

        public struct KampungRowSpec
        {
            public string id;
            public string name;
            public float x1, y1, x2, y2;
            public float spacing;
            public int seed;
            public int depth;
            public float rumahWeight;
            public float warungWeight;
        }

        public struct AvoidanceZone
        {
            public string name;
            public Vector3 worldCenter;
            public Vector2 halfExtentsXZ;
            public float minClearanceM;
        }

        public struct PathSegment
        {
            public Vector2 a;
            public Vector2 b;
            public float halfWidthM;
        }

        public struct ExpandedBuilding
        {
            public string rowId;
            public string buildingType;
            public Vector3 worldPos;
            public float yawDeg;
            public int depthIndex;
            public bool isEastBank;
            public bool hasJetty;
            public Vector3 jettyWorldPos;
            public float jettyYawDeg;
        }

        public struct KampungSpawnStats
        {
            public int totalBuildings;
            public int rumahCount;
            public int warungCount;
            public int westCount;
            public int eastCount;
            public int jettyCount;
            public int binCount;
            public int boatCount;
            public int lanternCount;
            public int rearTreeCount;
        }

        public static List<PathSegment> ParseFootpathsFromJson(string rawJson)
        {
            var segments = new List<PathSegment>();
            if (string.IsNullOrEmpty(rawJson)) return segments;

            int fpIdx = rawJson.IndexOf("\"footpaths\"", StringComparison.Ordinal);
            if (fpIdx < 0) return segments;
            int outerStart = rawJson.IndexOf('[', fpIdx);
            if (outerStart < 0) return segments;

            int depth = 0;
            int innerStart = -1;
            for (int i = outerStart; i < rawJson.Length; i++)
            {
                char c = rawJson[i];
                if (c == '[')
                {
                    depth++;
                    if (depth == 2) innerStart = i;
                }
                else if (c == ']')
                {
                    if (depth == 2 && innerStart >= 0)
                    {
                        string polyStr = rawJson.Substring(innerStart, i - innerStart + 1);
                        MatchCollection matches = PointPairRegex.Matches(polyStr);
                        Vector2? prev = null;
                        for (int m = 0; m < matches.Count; m++)
                        {
                            float mx = float.Parse(matches[m].Groups[1].Value, CultureInfo.InvariantCulture);
                            float my = float.Parse(matches[m].Groups[2].Value, CultureInfo.InvariantCulture);
                            Vector3 w = RiverMath.ToWorld3D(mx, my, 0f);
                            Vector2 cur = new Vector2(w.x, w.z);
                            if (prev.HasValue && Vector2.Distance(prev.Value, cur) > 0.05f)
                            {
                                segments.Add(new PathSegment { a = prev.Value, b = cur, halfWidthM = 2.0f });
                            }
                            prev = cur;
                        }
                        innerStart = -1;
                    }
                    depth--;
                    if (depth == 0) break;
                }
            }

            return segments;
        }

        public static List<ExpandedBuilding> ExpandKampungRows(
            IReadOnlyList<KampungRowSpec> rows,
            IReadOnlyList<AvoidanceZone> avoidZones,
            IReadOnlyList<PathSegment> footpaths)
        {
            var result = new List<ExpandedBuilding>();
            RejectCounts.Clear();
            if (rows == null) return result;

            int waterfrontIndex = 0;

            for (int r = 0; r < rows.Count; r++)
            {
                KampungRowSpec row = rows[r];
                var rng = new System.Random(row.seed != 0 ? row.seed : StableHash(row.id));

                Vector3 w1 = RiverMath.ToWorld3D(row.x1, row.y1, 0f);
                Vector3 w2 = RiverMath.ToWorld3D(row.x2, row.y2, 0f);
                Vector2 p1 = new Vector2(w1.x, w1.z);
                Vector2 p2 = new Vector2(w2.x, w2.z);

                float lenM = Vector2.Distance(p1, p2);
                float spacing = Mathf.Clamp(row.spacing > 0.1f ? row.spacing : 5.5f, 3.8f, 14f);
                int depth = Mathf.Clamp(row.depth > 0 ? row.depth : 1, 1, 3);

                float midMapX = (row.x1 + row.x2) * 0.5f;
                float midMapY = (row.y1 + row.y2) * 0.5f;
                bool isEastBank = midMapX > RiverMath.RiverCenterMapX(midMapY);
                float inlandDirX = isEastBank ? 1f : -1f;

                for (int d = 0; d < depth; d++)
                {
                    float startOffset = (d % 2 == 1) ? 0.5f * spacing : 0f;
                    int count = lenM >= startOffset ? Mathf.FloorToInt((lenM - startOffset) / spacing) + 1 : 0;

                    for (int i = 0; i < count; i++)
                    {
                        // Consume all candidate RNG draws up front so rejections never shift sequence
                        float jx = (float)(rng.NextDouble() * 1.2 - 0.6);
                        float jz = (float)(rng.NextDouble() * 1.2 - 0.6);
                        float jyaw = (float)(rng.NextDouble() * 16.0 - 8.0);
                        double typeRoll = rng.NextDouble();

                        float t = Mathf.Clamp01((startOffset + i * spacing) / Mathf.Max(0.01f, lenM));
                        Vector2 p = Vector2.Lerp(p1, p2, t);

                        float curMapY = p.y / RiverMath.MapScale + RiverMath.WorldH * 0.5f;
                        float cxW = (RiverMath.RiverCenterMapX(curMapY) - 520f) * 0.125f;
                        float hwW = RiverMath.RiverHalfWidthMap(curMapY) * 0.125f;
                        float riverEdgeX = isEastBank ? (cxW + hwW) : (cxW - hwW);

                        float frontX = p.x;
                        if ((frontX - riverEdgeX) * inlandDirX < 6.6f)
                        {
                            frontX = riverEdgeX + inlandDirX * 6.8f;
                        }
                        float baseX = frontX + d * 9.5f * inlandDirX;

                        Vector3 worldPos = new Vector3(baseX + jx, BankTopY, p.y + jz);
                        Vector2 posXZ = new Vector2(worldPos.x, worldPos.z);

                        if (worldPos.x < -49.5f || worldPos.x > 45.5f || worldPos.z < -80f || worldPos.z > 80f)
                        {
                            CountReject(row.id, "bounds");
                            continue;
                        }

                        if (Vector2.Distance(posXZ, QaSwimLaneCenterXZ) < 5.5f)
                        {
                            CountReject(row.id, "swimlane");
                            continue;
                        }

                        float baseYaw = ComputeRiverFacingYaw(posXZ, curMapY);
                        float finalYaw = baseYaw + jyaw;
                        Vector3 riverFacingDir = new Vector3(
                            Mathf.Cos(baseYaw * Mathf.Deg2Rad),
                            0f,
                            -Mathf.Sin(baseYaw * Mathf.Deg2Rad));

                        if (RiverMath.IsInRiver(worldPos) ||
                            RiverMath.IsInRiver(worldPos + riverFacingDir * 4.2f) ||
                            RiverMath.IsInRiver(worldPos + riverFacingDir * 2.0f))
                        {
                            CountReject(row.id, "river");
                            continue;
                        }

                        float totalW = Mathf.Max(0.001f, row.rumahWeight + row.warungWeight);
                        float warungProb = row.warungWeight / totalW;
                        string bType = (typeRoll < warungProb) ? "warung_madura" : "rumah";

                        // Real XZ footprint of this house at its yaw, checked bounds-to-bounds against avoid zones.
                        ComputeHouseFootprintXZ(bType, worldPos, finalYaw, out Vector2 houseCenterXZ, out Vector2 houseHalfXZ);
                        string zoneBlocker = FirstBlockingZone(houseCenterXZ, avoidZones, houseHalfXZ);
                        if (zoneBlocker != null)
                        {
                            CountReject(row.id, "zone:" + zoneBlocker);
                            continue;
                        }
                        if (!IsClearOfFootpaths(posXZ, footpaths, 1.8f))
                        {
                            CountReject(row.id, "footpath");
                            continue;
                        }
                        if (IsOverlappingExistingBuilding(posXZ, result, 4.4f))
                        {
                            CountReject(row.id, "overlap");
                            continue;
                        }

                        bool hasJetty = false;
                        Vector3 jettyPos = Vector3.zero;
                        if (d == 0 && Mathf.Abs(worldPos.x - riverEdgeX) <= 11.5f)
                        {
                            waterfrontIndex++;
                            if (waterfrontIndex % 4 == 1)
                            {
                                Vector3 candidateJetty = new Vector3(riverEdgeX + (isEastBank ? -0.4f : 0.4f), 0f, worldPos.z);
                                Vector2 candidateJettyXZ = new Vector2(candidateJetty.x, candidateJetty.z);
                                if (candidateJetty.z >= -78f && candidateJetty.z <= 78f &&
                                    IsJettyClearOfInfra(candidateJettyXZ, avoidZones) &&
                                    IsJettyClearOfExistingJetties(candidateJettyXZ, result, 5.0f))
                                {
                                    hasJetty = true;
                                    jettyPos = candidateJetty;
                                }
                            }
                        }

                        result.Add(new ExpandedBuilding
                        {
                            rowId = row.id,
                            buildingType = bType,
                            worldPos = worldPos,
                            yawDeg = finalYaw,
                            depthIndex = d,
                            isEastBank = isEastBank,
                            hasJetty = hasJetty,
                            jettyWorldPos = jettyPos,
                            jettyYawDeg = baseYaw
                        });
                    }
                }
            }

            var sbReject = new System.Text.StringBuilder("[KALI] kampung reject breakdown (row|reason=count): ");
            foreach (var kv in RejectCounts) sbReject.Append(kv.Key).Append('=').Append(kv.Value).Append("; ");
            sbReject.Append("accepted=").Append(result.Count);
            Debug.Log(sbReject.ToString());
            return result;
        }

        internal static KampungSpawnStats SpawnKampungAndClutter(
            IReadOnlyList<ExpandedBuilding> buildings,
            Transform buildingsGroup,
            Transform clutterGroup,
            Transform treesGroup,
            KaliMapBackdropBuilder.SceneAssetCache cache,
            IReadOnlyList<AvoidanceZone> avoidZones,
            IReadOnlyList<PathSegment> footpaths,
            int clutterSeed = 4042)
        {
            var stats = new KampungSpawnStats();
            if (buildings == null) return stats;

            GameObject rumahPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(RumahPrefabPath);
            GameObject warungPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(WarungPrefabPath);
            GameObject binPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(BinPrefabPath);
            GameObject sampanPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(SampanPrefabPath);
            GameObject rakitPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(RakitPrefabPath);
            GameObject lanternPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(LanternPrefabPath);

            Material deckMat = AssetDatabase.LoadAssetAtPath<Material>(JettyDeckMatPath)
                ?? KaliMapBackdropBuilder.GetSharedTintMaterial(cache, new Color(0.46f, 0.33f, 0.20f));
            Material pilingMat = AssetDatabase.LoadAssetAtPath<Material>(JettyPilingMatPath)
                ?? KaliMapBackdropBuilder.GetSharedTintMaterial(cache, new Color(0.32f, 0.22f, 0.14f));

            Mesh jettyDeckMesh = BuildJettyDeckMesh();
            Mesh jettyPilingMesh = BuildJettyPilingMesh();

            var clutterRng = new System.Random(clutterSeed);
            var treeRng = new System.Random(clutterSeed + 777);

            for (int i = 0; i < buildings.Count; i++)
            {
                ExpandedBuilding b = buildings[i];
                bool isWarung = string.Equals(b.buildingType, "warung_madura", StringComparison.OrdinalIgnoreCase);
                GameObject prefab = isWarung ? warungPrefab : rumahPrefab;

                GameObject inst = SpawnBuildingInstance(prefab, b, i, buildingsGroup);
                if (inst != null)
                {
                    KaliMapBackdropBuilder.MarkStaticDecor(inst, includeOccluder: true);
                    if (isWarung && lanternPrefab != null && AttachWarungLantern(inst.transform, lanternPrefab))
                    {
                        stats.lanternCount++;
                    }
                }

                stats.totalBuildings++;
                if (isWarung) stats.warungCount++;
                else stats.rumahCount++;
                if (b.isEastBank) stats.eastCount++;
                else stats.westCount++;

                if (b.hasJetty && clutterGroup != null)
                {
                    stats.jettyCount++;
                    GameObject jettyGo = CreateJettyObject(
                        clutterGroup,
                        stats.jettyCount,
                        b.jettyWorldPos,
                        b.jettyYawDeg,
                        jettyDeckMesh,
                        jettyPilingMesh,
                        deckMat,
                        pilingMat);
                    KaliMapBackdropBuilder.MarkStaticDecor(jettyGo, includeOccluder: false);

                    if (clutterRng.NextDouble() < 0.85)
                    {
                        bool useSampan = clutterRng.NextDouble() < 0.60;
                        GameObject boatPrefab = useSampan ? sampanPrefab : rakitPrefab;
                        if (boatPrefab != null)
                        {
                            float sideSign = (clutterRng.NextDouble() < 0.5) ? -1f : 1f;
                            float yawJitter = (float)(clutterRng.NextDouble() * 20.0 - 10.0);
                            Quaternion jRot = Quaternion.Euler(0f, b.jettyYawDeg, 0f);
                            Vector3 boatPos = b.jettyWorldPos + jRot * new Vector3(1.65f, 0.05f, sideSign * 1.65f);
                            float boatYaw = b.jettyYawDeg + sideSign * 90f + yawJitter;

                            GameObject boat = (GameObject)PrefabUtility.InstantiatePrefab(boatPrefab, clutterGroup);
                            boat.name = $"Kampung_MooredBoat_{stats.boatCount + 1:00}";
                            boat.transform.SetPositionAndRotation(boatPos, Quaternion.Euler(0f, boatYaw, 0f));
                            EnsureFittedBoxCollider(boat);
                            KaliMapBackdropBuilder.MarkStaticDecor(boat, includeOccluder: false);
                            stats.boatCount++;
                        }
                    }
                }

                if (binPrefab != null && clutterGroup != null && clutterRng.NextDouble() < 0.42)
                {
                    float side = (clutterRng.NextDouble() < 0.5) ? -1f : 1f;
                    float alongJitter = (float)(clutterRng.NextDouble() * 0.7 - 0.35);
                    float inOutJitter = (float)(clutterRng.NextDouble() * 0.7 - 0.35);
                    Vector3 binOffset = Quaternion.Euler(0f, b.yawDeg, 0f) * new Vector3(3.6f + inOutJitter, 0f, side * 2.6f + alongJitter);
                    Vector3 binPos = new Vector3(
                        b.worldPos.x + binOffset.x,
                        BankTopY,
                        b.worldPos.z + binOffset.z);
                    Vector2 binXZ = new Vector2(binPos.x, binPos.z);

                    bool clearOfBuildings = true;
                    for (int bi = 0; bi < buildings.Count; bi++)
                    {
                        Vector3 bwp = buildings[bi].worldPos;
                        float dx = binXZ.x - bwp.x;
                        float dz = binXZ.y - bwp.z;
                        if (dx * dx + dz * dz < 2.2f * 2.2f)
                        {
                            clearOfBuildings = false;
                            break;
                        }
                    }

                    if (binPos.x >= -49.5f && binPos.x <= 45.5f && binPos.z >= -80f && binPos.z <= 80f &&
                        !RiverMath.IsInRiver(binPos) &&
                        IsClearOfAvoidZones(binXZ, avoidZones, 3.0f, Vector2.zero) &&
                        IsClearOfFootpaths(binXZ, footpaths, 0.5f) &&
                        clearOfBuildings)
                    {
                        GameObject bin = (GameObject)PrefabUtility.InstantiatePrefab(binPrefab, clutterGroup);
                        bin.name = $"Kampung_Bin_{stats.binCount + 1:00}";
                        bin.transform.SetPositionAndRotation(
                            binPos,
                            Quaternion.Euler(0f, (float)(clutterRng.NextDouble() * 360.0), 0f));
                        EnsureFittedBoxCollider(bin);
                        KaliMapBackdropBuilder.MarkStaticDecor(bin, includeOccluder: false);
                        stats.binCount++;
                    }
                }
            }

            if (treesGroup != null)
            {
                stats.rearTreeCount = SpawnRearTreeClusters(
                    buildings,
                    treesGroup,
                    cache,
                    avoidZones,
                    footpaths,
                    treeRng);
            }

            return stats;
        }

        private static int SpawnRearTreeClusters(
            IReadOnlyList<ExpandedBuilding> buildings,
            Transform treesGroup,
            KaliMapBackdropBuilder.SceneAssetCache cache,
            IReadOnlyList<AvoidanceZone> avoidZones,
            IReadOnlyList<PathSegment> footpaths,
            System.Random rng)
        {
            var placedTreesXZ = new List<Vector2>();
            int treeCount = 0;

            for (int sideIdx = 0; sideIdx < 2; sideIdx++)
            {
                bool isEast = sideIdx == 1;
                float z = -64f;
                while (z <= 78f)
                {
                    float clusterZ = z + (float)(rng.NextDouble() * 4.0 - 2.0);
                    float furthestX = FindFurthestBuildingXNearZ(buildings, isEast, clusterZ, 10f);

                    float baseX;
                    if (isEast)
                    {
                        float minEast = furthestX > 0f ? Mathf.Max(26f, furthestX + 5.5f) : 26f;
                        float maxEast = 57f;
                        baseX = minEast <= maxEast
                            ? Mathf.Lerp(minEast, maxEast, (float)rng.NextDouble())
                            : 54f;
                    }
                    else
                    {
                        float maxWest = furthestX < 0f ? Mathf.Min(-26f, furthestX - 5.5f) : -26f;
                        float minWest = -57f;
                        baseX = minWest <= maxWest
                            ? Mathf.Lerp(minWest, maxWest, (float)rng.NextDouble())
                            : -54f;
                    }

                    int treesInCluster = rng.Next(4, 7);
                    for (int t = 0; t < treesInCluster; t++)
                    {
                        double angle = rng.NextDouble() * Math.PI * 2.0;
                        float rad = (float)(2.0 + rng.NextDouble() * 3.5);
                        float tx = baseX + (float)Math.Cos(angle) * rad;
                        float tz = clusterZ + (float)Math.Sin(angle) * rad;
                        float yaw = (float)(rng.NextDouble() * 360.0);
                        float scale = (float)(0.85 + rng.NextDouble() * 0.45);
                        float tilt = (float)(rng.NextDouble() * 8.0 - 4.0);
                        bool useAltGreen = rng.NextDouble() < 0.45;

                        if (tx < -58f || tx > 58f || tz < -82f || tz > 82f)
                            continue;

                        Vector3 treePos = new Vector3(tx, BankTopY, tz);
                        Vector2 treeXZ = new Vector2(tx, tz);

                        if (RiverMath.IsInRiver(treePos))
                            continue;

                        if (Vector2.Distance(treeXZ, QaSwimLaneCenterXZ) < 5.5f)
                            continue;

                        if (IsOverlappingExistingBuilding(treeXZ, buildings, 4.2f))
                            continue;

                        if (!IsClearOfAvoidZones(treeXZ, avoidZones, 4.5f, Vector2.zero))
                            continue;

                        if (!IsClearOfFootpaths(treeXZ, footpaths, 0.8f))
                            continue;

                        bool tooCloseToTree = false;
                        for (int k = 0; k < placedTreesXZ.Count; k++)
                        {
                            if ((placedTreesXZ[k] - treeXZ).sqrMagnitude < 6.76f)
                            {
                                tooCloseToTree = true;
                                break;
                            }
                        }
                        if (tooCloseToTree) continue;

                        treeCount++;
                        placedTreesXZ.Add(treeXZ);
                        KaliMapBackdropBuilder.CreateLowPolyTree(
                            treesGroup,
                            cache,
                            treePos,
                            yaw,
                            scale,
                            tilt,
                            $"Kampung_RearTree_{treeCount:00}",
                            useAltGreen,
                            addCollider: true,
                            isStatic: true);
                    }

                    z += (float)(9.0 + rng.NextDouble() * 3.0);
                }
            }

            return treeCount;
        }

        private static float FindFurthestBuildingXNearZ(
            IReadOnlyList<ExpandedBuilding> buildings,
            bool isEast,
            float z,
            float zWindow)
        {
            float best = 0f;
            bool found = false;
            for (int i = 0; i < buildings.Count; i++)
            {
                ExpandedBuilding b = buildings[i];
                if (b.isEastBank != isEast) continue;
                if (Mathf.Abs(b.worldPos.z - z) > zWindow) continue;
                if (!found || (isEast ? b.worldPos.x > best : b.worldPos.x < best))
                {
                    best = b.worldPos.x;
                    found = true;
                }
            }
            return found ? best : 0f;
        }

        private static GameObject SpawnBuildingInstance(GameObject prefab, ExpandedBuilding b, int index, Transform parent)
        {
            if (prefab == null || parent == null) return null;
            GameObject inst = (GameObject)PrefabUtility.InstantiatePrefab(prefab, parent);
            inst.name = $"{b.rowId}_{b.buildingType}_{index + 1:00}";
            inst.transform.SetPositionAndRotation(b.worldPos, Quaternion.Euler(0f, b.yawDeg, 0f));
            EnsureFittedBoxCollider(inst);
            return inst;
        }

        private static bool AttachWarungLantern(Transform warungTransform, GameObject lanternPrefab)
        {
            bool hasBounds = TryGetLocalBounds(warungTransform.gameObject, out Bounds b);
            GameObject lantern = (GameObject)PrefabUtility.InstantiatePrefab(lanternPrefab, warungTransform);
            lantern.name = "Warung_Lantern";
            lantern.transform.localPosition = hasBounds
                ? new Vector3(b.max.x - 0.15f, Mathf.Max(1.8f, b.max.y - 0.35f), b.center.z)
                : new Vector3(1.6f, 2.3f, 0f);
            lantern.transform.localRotation = Quaternion.identity;
            return true;
        }

        private static GameObject CreateJettyObject(
            Transform parent,
            int jettyNumber,
            Vector3 worldPos,
            float yawDeg,
            Mesh deckMesh,
            Mesh pilingMesh,
            Material deckMat,
            Material pilingMat)
        {
            GameObject root = new GameObject($"Kampung_Jetty_{jettyNumber:00}");
            root.transform.SetParent(parent, worldPositionStays: false);
            root.transform.SetPositionAndRotation(worldPos, Quaternion.Euler(0f, yawDeg, 0f));

            GameObject deckGo = new GameObject("Jetty_Deck");
            deckGo.transform.SetParent(root.transform, worldPositionStays: false);
            deckGo.AddComponent<MeshFilter>().sharedMesh = deckMesh;
            deckGo.AddComponent<MeshRenderer>().sharedMaterial = deckMat;
            BoxCollider col = deckGo.AddComponent<BoxCollider>();
            col.center = new Vector3(0.7f, 1.40f, 0f);
            col.size = new Vector3(3.8f, 0.25f, 1.6f);

            GameObject pilingsGo = new GameObject("Jetty_Pilings");
            pilingsGo.transform.SetParent(root.transform, worldPositionStays: false);
            pilingsGo.AddComponent<MeshFilter>().sharedMesh = pilingMesh;
            pilingsGo.AddComponent<MeshRenderer>().sharedMaterial = pilingMat;

            return root;
        }

        private static Mesh BuildJettyDeckMesh()
        {
            var mesh = new Mesh { name = "Kampung_JettyDeckMesh" };
            var verts = new List<Vector3>();
            var norms = new List<Vector3>();
            var uvs = new List<Vector2>();
            var tris = new List<int>();

            // Main plank deck extending 3.8m from bank (-1.2m to +2.6m along +X river direction)
            for (int p = 0; p < 7; p++)
            {
                float xMin = -1.2f + p * 0.54f;
                float xMax = xMin + 0.48f;
                AddBox(verts, norms, uvs, tris, new Vector3((xMin + xMax) * 0.5f, 1.40f, 0f), new Vector3(0.48f, 0.12f, 1.6f));
            }

            // Two ladder side stringers at jetty tip (x = +2.6m) going down to water
            AddBox(verts, norms, uvs, tris, new Vector3(2.65f, 0.80f, -0.45f), new Vector3(0.10f, 1.20f, 0.08f));
            AddBox(verts, norms, uvs, tris, new Vector3(2.65f, 0.80f, 0.45f), new Vector3(0.10f, 1.20f, 0.08f));

            // 3 wooden step-down ladder rungs down to Y = 0.25m
            AddBox(verts, norms, uvs, tris, new Vector3(2.68f, 1.02f, 0f), new Vector3(0.12f, 0.06f, 0.92f));
            AddBox(verts, norms, uvs, tris, new Vector3(2.68f, 0.64f, 0f), new Vector3(0.12f, 0.06f, 0.92f));
            AddBox(verts, norms, uvs, tris, new Vector3(2.68f, 0.26f, 0f), new Vector3(0.12f, 0.06f, 0.92f));

            mesh.SetVertices(verts);
            mesh.SetNormals(norms);
            mesh.SetUVs(0, uvs);
            mesh.SetTriangles(tris, 0);
            mesh.RecalculateBounds();
            return mesh;
        }

        private static Mesh BuildJettyPilingMesh()
        {
            var mesh = new Mesh { name = "Kampung_JettyPilingMesh" };
            var verts = new List<Vector3>();
            var norms = new List<Vector3>();
            var uvs = new List<Vector2>();
            var tris = new List<int>();

            // 4 vertical wooden stilt posts from Y = -1.5m to Y = +1.55m
            Vector3 size = new Vector3(0.16f, 3.05f, 0.16f);
            float centerY = 0.025f;
            AddBox(verts, norms, uvs, tris, new Vector3(-0.8f, centerY, -0.68f), size);
            AddBox(verts, norms, uvs, tris, new Vector3(-0.8f, centerY, 0.68f), size);
            AddBox(verts, norms, uvs, tris, new Vector3(2.2f, centerY, -0.68f), size);
            AddBox(verts, norms, uvs, tris, new Vector3(2.2f, centerY, 0.68f), size);

            mesh.SetVertices(verts);
            mesh.SetNormals(norms);
            mesh.SetUVs(0, uvs);
            mesh.SetTriangles(tris, 0);
            mesh.RecalculateBounds();
            return mesh;
        }

        private static void AddBox(
            List<Vector3> verts,
            List<Vector3> norms,
            List<Vector2> uvs,
            List<int> tris,
            Vector3 center,
            Vector3 size)
        {
            Vector3 h = size * 0.5f;
            Vector3[] faceNormals =
            {
                Vector3.up, Vector3.down, Vector3.forward, Vector3.back, Vector3.right, Vector3.left
            };
            Vector3[][] faceCorners =
            {
                new[] { new Vector3(-h.x, h.y, -h.z), new Vector3(-h.x, h.y, h.z), new Vector3(h.x, h.y, h.z), new Vector3(h.x, h.y, -h.z) },
                new[] { new Vector3(-h.x, -h.y, h.z), new Vector3(-h.x, -h.y, -h.z), new Vector3(h.x, -h.y, -h.z), new Vector3(h.x, -h.y, h.z) },
                new[] { new Vector3(h.x, -h.y, h.z), new Vector3(h.x, h.y, h.z), new Vector3(-h.x, h.y, h.z), new Vector3(-h.x, -h.y, h.z) },
                new[] { new Vector3(-h.x, -h.y, -h.z), new Vector3(-h.x, h.y, -h.z), new Vector3(h.x, h.y, -h.z), new Vector3(h.x, -h.y, -h.z) },
                new[] { new Vector3(h.x, -h.y, -h.z), new Vector3(h.x, h.y, -h.z), new Vector3(h.x, h.y, h.z), new Vector3(h.x, -h.y, h.z) },
                new[] { new Vector3(-h.x, -h.y, h.z), new Vector3(-h.x, h.y, h.z), new Vector3(-h.x, h.y, -h.z), new Vector3(-h.x, -h.y, -h.z) }
            };

            for (int f = 0; f < 6; f++)
            {
                int baseIdx = verts.Count;
                for (int c = 0; c < 4; c++)
                {
                    verts.Add(center + faceCorners[f][c]);
                    norms.Add(faceNormals[f]);
                }
                uvs.Add(new Vector2(0f, 0f));
                uvs.Add(new Vector2(0f, 1f));
                uvs.Add(new Vector2(1f, 1f));
                uvs.Add(new Vector2(1f, 0f));

                tris.Add(baseIdx);
                tris.Add(baseIdx + 1);
                tris.Add(baseIdx + 2);
                tris.Add(baseIdx);
                tris.Add(baseIdx + 2);
                tris.Add(baseIdx + 3);
            }
        }

        private static float ComputeRiverFacingYaw(Vector2 posXZ, float curMapY)
        {
            float yMin = Mathf.Max(110f, curMapY - 120f);
            float yMax = Mathf.Min(RiverMath.WorldH, curMapY + 120f);
            Vector2 nearestCenterXZ = posXZ;
            float bestSqrDist = float.MaxValue;

            for (float sy = yMin; sy <= yMax; sy += 4f)
            {
                Vector3 c3 = RiverMath.ToWorld3D(RiverMath.RiverCenterMapX(sy), sy, 0f);
                Vector2 c2 = new Vector2(c3.x, c3.z);
                float sqr = (c2 - posXZ).sqrMagnitude;
                if (sqr < bestSqrDist)
                {
                    bestSqrDist = sqr;
                    nearestCenterXZ = c2;
                }
            }

            Vector2 toRiver = nearestCenterXZ - posXZ;
            return Mathf.Atan2(-toRiver.y, toRiver.x) * Mathf.Rad2Deg;
        }

        private static readonly Dictionary<string, Vector4> HouseLocalFootprintCache = new Dictionary<string, Vector4>();

        // Local XZ footprint of a house prefab: center in xy, half-extents in zw. Measured once per prefab.
        private static Vector4 GetHouseLocalFootprint(string prefabPath)
        {
            if (HouseLocalFootprintCache.TryGetValue(prefabPath, out Vector4 cached)) return cached;

            // Fallback is the conservative max house footprint if the prefab cannot be measured.
            Vector4 fp = new Vector4(0f, 0f, 5.8f, 4.7f);
            GameObject prefab = AssetDatabase.LoadAssetAtPath<GameObject>(prefabPath);
            if (prefab != null)
            {
                GameObject tmp = (GameObject)PrefabUtility.InstantiatePrefab(prefab);
                if (TryGetLocalBounds(tmp, out Bounds lb))
                {
                    fp = new Vector4(lb.center.x, lb.center.z, lb.extents.x, lb.extents.z);
                }
                UnityEngine.Object.DestroyImmediate(tmp);
            }

            HouseLocalFootprintCache[prefabPath] = fp;
            return fp;
        }

        // World XZ AABB of a house placed at worldPos with yaw: rotated local footprint.
        private static void ComputeHouseFootprintXZ(string bType, Vector3 worldPos, float yawDeg, out Vector2 center, out Vector2 half)
        {
            string path = bType == "warung_madura" ? WarungPrefabPath : RumahPrefabPath;
            Vector4 lf = GetHouseLocalFootprint(path);
            Vector3 rc = Quaternion.Euler(0f, yawDeg, 0f) * new Vector3(lf.x, 0f, lf.y);
            center = new Vector2(worldPos.x + rc.x, worldPos.z + rc.z);

            float rad = yawDeg * Mathf.Deg2Rad;
            float c = Mathf.Abs(Mathf.Cos(rad));
            float s = Mathf.Abs(Mathf.Sin(rad));
            float hx = lf.z;
            float hz = lf.w;
            half = new Vector2(c * hx + s * hz, s * hx + c * hz);
        }

        private static readonly Dictionary<string, int> RejectCounts = new Dictionary<string, int>();

        private static void CountReject(string rowId, string reason)
        {
            string key = rowId + "|" + reason;
            RejectCounts[key] = RejectCounts.TryGetValue(key, out int v) ? v + 1 : 1;
        }

        // Name of the first avoid zone the candidate footprint violates, or null when clear.
        private static string FirstBlockingZone(Vector2 posXZ, IReadOnlyList<AvoidanceZone> avoidZones, Vector2 candidateHalfXZ)
        {
            if (avoidZones == null) return null;
            for (int i = 0; i < avoidZones.Count; i++)
            {
                AvoidanceZone z = avoidZones[i];
                if (DistanceToBoxXZ(posXZ, z.worldCenter, z.halfExtentsXZ + candidateHalfXZ) < z.minClearanceM)
                {
                    return z.name;
                }
            }
            return null;
        }

        private static bool IsClearOfAvoidZones(Vector2 posXZ, IReadOnlyList<AvoidanceZone> avoidZones, float overrideMinClearance, Vector2 candidateHalfXZ)
        {
            if (avoidZones == null) return true;
            for (int i = 0; i < avoidZones.Count; i++)
            {
                AvoidanceZone z = avoidZones[i];
                float req = Mathf.Max(z.minClearanceM, overrideMinClearance);
                // Bounds-to-bounds: fold the candidate's half-extent into the zone's box.
                if (DistanceToBoxXZ(posXZ, z.worldCenter, z.halfExtentsXZ + candidateHalfXZ) < req)
                {
                    return false;
                }
            }
            return true;
        }

        private static bool IsJettyClearOfInfra(Vector2 jettyXZ, IReadOnlyList<AvoidanceZone> avoidZones)
        {
            if (avoidZones == null) return true;
            for (int i = 0; i < avoidZones.Count; i++)
            {
                AvoidanceZone z = avoidZones[i];
                string n = z.name ?? string.Empty;
                if (n.IndexOf("Dermaga", StringComparison.OrdinalIgnoreCase) >= 0 ||
                    n.IndexOf("Jembatan", StringComparison.OrdinalIgnoreCase) >= 0 ||
                    n.IndexOf("Pintu Air", StringComparison.OrdinalIgnoreCase) >= 0 ||
                    n.IndexOf("Trash Boom", StringComparison.OrdinalIgnoreCase) >= 0 ||
                    n.IndexOf("Gunung", StringComparison.OrdinalIgnoreCase) >= 0)
                {
                    if (DistanceToBoxXZ(jettyXZ, z.worldCenter, z.halfExtentsXZ) < 7.5f)
                        return false;
                }
            }
            return true;
        }

        private static bool IsJettyClearOfExistingJetties(
            Vector2 jettyXZ,
            IReadOnlyList<ExpandedBuilding> buildings,
            float minDist)
        {
            float minSqr = minDist * minDist;
            for (int i = 0; i < buildings.Count; i++)
            {
                if (!buildings[i].hasJetty) continue;
                Vector3 jp = buildings[i].jettyWorldPos;
                float dx = jettyXZ.x - jp.x;
                float dz = jettyXZ.y - jp.z;
                if (dx * dx + dz * dz < minSqr) return false;
            }
            return true;
        }

        private static bool IsClearOfFootpaths(Vector2 posXZ, IReadOnlyList<PathSegment> footpaths, float extraClearance)
        {
            if (footpaths == null) return true;
            for (int i = 0; i < footpaths.Count; i++)
            {
                PathSegment seg = footpaths[i];
                if (DistanceToSegmentXZ(posXZ, seg.a, seg.b) < seg.halfWidthM + extraClearance)
                {
                    return false;
                }
            }
            return true;
        }

        private static bool IsOverlappingExistingBuilding(
            Vector2 posXZ,
            IReadOnlyList<ExpandedBuilding> buildings,
            float minDist)
        {
            if (buildings == null) return false;
            float minSqr = minDist * minDist;
            for (int i = 0; i < buildings.Count; i++)
            {
                Vector3 wp = buildings[i].worldPos;
                float dx = posXZ.x - wp.x;
                float dz = posXZ.y - wp.z;
                if (dx * dx + dz * dz < minSqr) return true;
            }
            return false;
        }

        private static float DistanceToBoxXZ(Vector2 p, Vector3 boxCenter, Vector2 halfExtents)
        {
            float dx = Mathf.Max(0f, Mathf.Abs(p.x - boxCenter.x) - halfExtents.x);
            float dz = Mathf.Max(0f, Mathf.Abs(p.y - boxCenter.z) - halfExtents.y);
            return Mathf.Sqrt(dx * dx + dz * dz);
        }

        private static float DistanceToSegmentXZ(Vector2 p, Vector2 a, Vector2 b)
        {
            Vector2 ab = b - a;
            float abSqr = ab.sqrMagnitude;
            if (abSqr < 1e-6f) return Vector2.Distance(p, a);
            float t = Mathf.Clamp01(Vector2.Dot(p - a, ab) / abSqr);
            return Vector2.Distance(p, a + t * ab);
        }

        private static int StableHash(string s)
        {
            if (string.IsNullOrEmpty(s)) return 1337;
            unchecked
            {
                int hash = 23;
                for (int i = 0; i < s.Length; i++)
                {
                    hash = hash * 31 + s[i];
                }
                return hash == 0 ? 1337 : hash;
            }
        }

        private static void EnsureFittedBoxCollider(GameObject go)
        {
            if (go == null || go.GetComponentInChildren<Collider>(true) != null) return;
            BoxCollider box = go.AddComponent<BoxCollider>();
            if (TryGetLocalBounds(go, out Bounds localBounds))
            {
                box.center = localBounds.center;
                box.size = localBounds.size;
            }
        }

        // The 6x6 m "CahayaTanah" ground-glow quads (M_Env_LightPool, EnvNightLamp) are painted light on the
        // ground, not building. Counting them inflated every house/hub footprint by up to ~3 m after the lamp pass.
        internal static bool IsGroundLightPool(Renderer r)
        {
            return r != null && r.sharedMaterial != null && r.sharedMaterial.name.StartsWith("M_Env_LightPool");
        }

        private static bool TryGetLocalBounds(GameObject root, out Bounds localBounds)
        {
            localBounds = new Bounds();
            bool any = false;
            Matrix4x4 worldToLocal = root.transform.worldToLocalMatrix;

            foreach (MeshFilter mf in root.GetComponentsInChildren<MeshFilter>(true))
            {
                if (mf.sharedMesh == null) continue;
                if (IsGroundLightPool(mf.GetComponent<Renderer>())) continue;
                Bounds mb = mf.sharedMesh.bounds;
                Matrix4x4 m = worldToLocal * mf.transform.localToWorldMatrix;
                for (int cx = -1; cx <= 1; cx += 2)
                for (int cy = -1; cy <= 1; cy += 2)
                for (int cz = -1; cz <= 1; cz += 2)
                {
                    Vector3 corner = m.MultiplyPoint3x4(mb.center + Vector3.Scale(mb.extents, new Vector3(cx, cy, cz)));
                    if (!any)
                    {
                        localBounds = new Bounds(corner, Vector3.zero);
                        any = true;
                    }
                    else
                    {
                        localBounds.Encapsulate(corner);
                    }
                }
            }
            return any;
        }
    }
}
#endif
