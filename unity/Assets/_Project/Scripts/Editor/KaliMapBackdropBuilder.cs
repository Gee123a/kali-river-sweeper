#if UNITY_EDITOR
using System;
using System.Collections.Generic;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using KaliRiverSweeper.Core;

namespace KaliRiverSweeper.Editor
{
    internal static class KaliMapBackdropBuilder
    {
        private const float PlayHalfX = 65f;
        private const float PlayHalfZ = 90f;
        private const float OverlapInward = 0.5f;
        private const float OuterExtent = 420f;
        private const float BankLipY = 1.38f;
        private const float RiverbedCarveY = -2.2f;

        private const string TrunkMatPath = "Assets/_Project/Environment/Materials/M_Env_KayuTiang.mat";
        private const string TerrainMatPath = "Assets/_Project/Environment/Materials/M_Env_TanahBantaran.mat";

        internal sealed class SceneAssetCache
        {
            public Mesh TreeTrunkMesh;
            public Mesh TreeCrownMesh;
            public Mesh HouseSilhouetteMesh;
            public Material TreeTrunkMat;
            public Material TreeCrownMatA;
            public Material TreeCrownMatB;
            public Material SilhouetteWallMat;
            public Material SilhouetteRoofMat;
            public readonly Dictionary<Color32, Material> TintCache = new Dictionary<Color32, Material>();

            public SceneAssetCache()
            {
                EnsureCacheAssets(this);
            }
        }

        internal static Material GetSharedTintMaterial(SceneAssetCache cache, Color col)
        {
            if (cache == null)
            {
                cache = new SceneAssetCache();
            }

            Color32 key = (Color32)col;
            if (cache.TintCache.TryGetValue(key, out Material existing) && existing != null)
            {
                return existing;
            }

            Material mat = CreateLitMaterial(
                $"M_SharedTint_{key.r:X2}{key.g:X2}{key.b:X2}",
                col,
                0.22f);
            cache.TintCache[key] = mat;
            return mat;
        }

        internal static void MarkStaticDecor(GameObject go, bool includeOccluder = false)
        {
            if (go == null) return;

            StaticEditorFlags flags = StaticEditorFlags.BatchingStatic | StaticEditorFlags.OccludeeStatic;
            if (includeOccluder)
            {
                flags |= StaticEditorFlags.OccluderStatic;
            }

            Transform[] transforms = go.GetComponentsInChildren<Transform>(true);
            for (int i = 0; i < transforms.Length; i++)
            {
                GameObjectUtility.SetStaticEditorFlags(transforms[i].gameObject, flags);
            }
        }

        internal static GameObject CreateLowPolyTree(
            Transform parent,
            SceneAssetCache cache,
            Vector3 worldPos,
            float yawDeg,
            float scale,
            float tiltDeg,
            string name,
            bool useAltGreen,
            bool addCollider,
            bool isStatic = true)
        {
            if (cache == null)
            {
                cache = new SceneAssetCache();
            }
            else
            {
                EnsureCacheAssets(cache);
            }

            GameObject root = new GameObject(string.IsNullOrEmpty(name) ? "Tree_LowPoly" : name);
            if (parent != null)
            {
                root.transform.SetParent(parent, false);
            }
            root.transform.position = worldPos;
            root.transform.rotation = Quaternion.Euler(tiltDeg, yawDeg, tiltDeg * 0.5f);
            root.transform.localScale = Vector3.one * scale;

            GameObject trunk = new GameObject("Trunk");
            trunk.transform.SetParent(root.transform, false);
            MeshFilter trunkMf = trunk.AddComponent<MeshFilter>();
            trunkMf.sharedMesh = cache.TreeTrunkMesh;
            MeshRenderer trunkMr = trunk.AddComponent<MeshRenderer>();
            trunkMr.sharedMaterial = cache.TreeTrunkMat;
            trunkMr.shadowCastingMode = ShadowCastingMode.On;
            trunkMr.receiveShadows = true;

            GameObject crown = new GameObject("Crown");
            crown.transform.SetParent(root.transform, false);
            MeshFilter crownMf = crown.AddComponent<MeshFilter>();
            crownMf.sharedMesh = cache.TreeCrownMesh;
            MeshRenderer crownMr = crown.AddComponent<MeshRenderer>();
            crownMr.sharedMaterial = useAltGreen ? cache.TreeCrownMatB : cache.TreeCrownMatA;
            crownMr.shadowCastingMode = ShadowCastingMode.On;
            crownMr.receiveShadows = true;

            if (addCollider)
            {
                CapsuleCollider col = root.AddComponent<CapsuleCollider>();
                col.radius = 0.25f;
                col.height = 3.2f;
                col.center = new Vector3(0f, 1.6f, 0f);
            }

            if (isStatic)
            {
                MarkStaticDecor(root);
            }

            return root;
        }

        internal static float SampleBackdropHeight(float wx, float wz)
        {
            float dx = Mathf.Max(0f, Mathf.Abs(wx) - PlayHalfX);
            float dz = Mathf.Max(0f, Mathf.Abs(wz) - PlayHalfZ);
            float edgeDist = Mathf.Sqrt(dx * dx + dz * dz);

            float blend = SmoothStep(0f, 55f, edgeDist);

            // Multi-octave deterministic rolling tropical hills
            bool inContinuationZ = wz < -(PlayHalfZ - OverlapInward) || wz > (PlayHalfZ - OverlapInward);
            float extCx = 0f;
            float extHw = 0f;
            float distFromRiver = 0f;
            float ridgeAtten = 1f;
            if (inContinuationZ)
            {
                extCx = ExtendedRiverCenterX(wz);
                extHw = ExtendedRiverHalfWidth(wz);
                distFromRiver = Mathf.Abs(wx - extCx);
                ridgeAtten = SmoothStep(extHw, extHw + 48f, distFromRiver);
            }

            float ridgeN = Mathf.Max(0f, -(wz + PlayHalfZ) / 330f) * ridgeAtten; // taller scenic ridge behind Gunung Sampah (-Z)
            float hillA = Mathf.Sin(wx * 0.011f + 0.4f) * Mathf.Cos(wz * 0.010f - 0.3f) * 9.5f;
            float hillB = Mathf.Sin((wx + wz) * 0.019f + 1.1f) * 5.2f;
            float hillC = Mathf.Cos(wx * 0.031f - wz * 0.027f) * 2.4f;
            float distRise = SmoothStep(20f, 340f, edgeDist) * 16.0f + ridgeN * 14.0f;

            float rawHills = 2.0f + distRise + hillA + hillB + hillC;
            float clampedHills = Mathf.Max(1.6f, rawHills);
            float height = Mathf.Lerp(BankLipY, clampedHills, blend);

            // Carve upstream (-Z) and downstream (+Z) river channel continuation with gentle valley slope
            if (inContinuationZ)
            {
                float bankOuter = extHw + 28f;

                if (distFromRiver < bankOuter)
                {
                    float bankT = SmoothStep(extHw, bankOuter, distFromRiver);
                    height = Mathf.Lerp(RiverbedCarveY, height, bankT);
                }
            }

            return height;
        }

        internal static void BuildBackdropAndBoundary(
            Transform worldRoot,
            SceneAssetCache cache,
            Material waterMat,
            out int backdropObjectCount,
            out int boundaryWallCount)
        {
            if (cache == null)
            {
                cache = new SceneAssetCache();
            }
            else
            {
                EnsureCacheAssets(cache);
            }

            backdropObjectCount = 0;

            GameObject backdropRing = new GameObject("Backdrop_Ring");
            if (worldRoot != null)
            {
                backdropRing.transform.SetParent(worldRoot, false);
            }

            // A.1 Rolling hills terrain ring
            Material terrainMat = AssetDatabase.LoadAssetAtPath<Material>(TerrainMatPath);
            if (terrainMat == null)
            {
                terrainMat = GetSharedTintMaterial(cache, new Color(0.24f, 0.34f, 0.21f));
            }

            GameObject hillsGo = new GameObject("Backdrop_RollingHills");
            hillsGo.transform.SetParent(backdropRing.transform, false);
            MeshFilter hillsMf = hillsGo.AddComponent<MeshFilter>();
            hillsMf.sharedMesh = BuildBackdropHillsMesh();
            MeshRenderer hillsMr = hillsGo.AddComponent<MeshRenderer>();
            hillsMr.sharedMaterial = terrainMat;
            hillsMr.shadowCastingMode = ShadowCastingMode.Off;
            hillsMr.receiveShadows = true;
            MarkStaticDecor(hillsGo);
            backdropObjectCount++;

            // A.2 River water continuation ribbons (non-static so RiverWaterSurfaceFollower can track Y)
            Material resolvedWaterMat = waterMat != null
                ? waterMat
                : GetSharedTintMaterial(cache, new Color(0.24f, 0.20f, 0.14f, 0.85f));

            CreateRiverContinuationRibbon(
                backdropRing.transform,
                "Backdrop_RiverUpstream",
                -(PlayHalfZ - OverlapInward),
                -OuterExtent,
                resolvedWaterMat);
            backdropObjectCount++;

            CreateRiverContinuationRibbon(
                backdropRing.transform,
                "Backdrop_RiverDownstream",
                PlayHalfZ - OverlapInward,
                OuterExtent,
                resolvedWaterMat);
            backdropObjectCount++;

            // A.3 Distant house and tree silhouettes
            GameObject silhouettesRoot = new GameObject("Backdrop_Silhouettes");
            silhouettesRoot.transform.SetParent(backdropRing.transform, false);

            var rng = new System.Random(9042);
            List<Vector2> placedPositions = new List<Vector2>(68);

            // ~24 distant kampung house silhouettes
            int houseCount = 0;
            int attempts = 0;
            while (houseCount < 24 && attempts < 400)
            {
                attempts++;
                if (!TrySampleScatterPoint(rng, 14f, 165f, 14f, placedPositions, out float x, out float z))
                {
                    continue;
                }

                float groundY = SampleBackdropHeight(x, z);
                GameObject house = new GameObject($"Backdrop_House_{houseCount:00}");
                house.transform.SetParent(silhouettesRoot.transform, false);
                house.transform.position = new Vector3(x, groundY - 0.15f, z);

                float riverCx = ExtendedRiverCenterX(z);
                Vector3 toRiver = new Vector3(riverCx - x, 0f, 0f);
                float baseYaw = toRiver.sqrMagnitude > 0.01f
                    ? Quaternion.LookRotation(toRiver.normalized, Vector3.up).eulerAngles.y
                    : 0f;
                float yawJitter = (float)(rng.NextDouble() * 44.0 - 22.0);
                house.transform.rotation = Quaternion.Euler(0f, baseYaw + yawJitter, 0f);

                float houseScale = 0.9f + (float)rng.NextDouble() * 0.25f;
                house.transform.localScale = Vector3.one * houseScale;

                MeshFilter mf = house.AddComponent<MeshFilter>();
                mf.sharedMesh = cache.HouseSilhouetteMesh;
                MeshRenderer mr = house.AddComponent<MeshRenderer>();
                mr.sharedMaterials = new Material[] { cache.SilhouetteWallMat, cache.SilhouetteRoofMat };
                mr.shadowCastingMode = ShadowCastingMode.On;
                mr.receiveShadows = true;

                MarkStaticDecor(house);
                placedPositions.Add(new Vector2(x, z));
                houseCount++;
                backdropObjectCount++;
            }

            // ~42 distant tree/palm silhouettes
            int treeCount = 0;
            attempts = 0;
            while (treeCount < 42 && attempts < 600)
            {
                attempts++;
                if (!TrySampleScatterPoint(rng, 12f, 195f, 9f, placedPositions, out float x, out float z))
                {
                    continue;
                }

                float groundY = SampleBackdropHeight(x, z);
                float yaw = (float)(rng.NextDouble() * 360.0);
                float scale = 1.2f + (float)rng.NextDouble() * 1.0f;
                float tilt = (float)(rng.NextDouble() * 6.0 - 3.0);

                CreateLowPolyTree(
                    silhouettesRoot.transform,
                    cache,
                    new Vector3(x, groundY, z),
                    yaw,
                    scale,
                    tilt,
                    $"Backdrop_Tree_{treeCount:00}",
                    (treeCount & 1) == 1,
                    addCollider: false,
                    isStatic: true);

                placedPositions.Add(new Vector2(x, z));
                treeCount++;
                backdropObjectCount++;
            }

            // B. Invisible Play Boundary
            GameObject playBoundary = new GameObject("PlayBoundary");
            if (worldRoot != null)
            {
                playBoundary.transform.SetParent(worldRoot, false);
            }

            CreateBoundaryWall(playBoundary.transform, "PlayBoundary_West", new Vector3(-54f, 10f, 0f), new Vector3(4f, 30f, 176f));
            CreateBoundaryWall(playBoundary.transform, "PlayBoundary_East", new Vector3(50f, 10f, 0f), new Vector3(4f, 30f, 176f));
            CreateBoundaryWall(playBoundary.transform, "PlayBoundary_North", new Vector3(0f, 10f, -86f), new Vector3(108f, 30f, 4f));
            CreateBoundaryWall(playBoundary.transform, "PlayBoundary_South", new Vector3(0f, 10f, 86f), new Vector3(108f, 30f, 4f));

            MarkStaticDecor(playBoundary);
            boundaryWallCount = 4;
        }

        private static bool TrySampleScatterPoint(
            System.Random rng,
            float minEdgeDist,
            float maxEdgeDist,
            float minSpacing,
            List<Vector2> existing,
            out float x,
            out float z)
        {
            double angle = rng.NextDouble() * Math.PI * 2.0;
            float dist = minEdgeDist + (float)rng.NextDouble() * (maxEdgeDist - minEdgeDist);

            // Sample around the play box perimeter + hills
            x = Mathf.Cos((float)angle) * (PlayHalfX + dist * 0.85f);
            z = Mathf.Sin((float)angle) * (PlayHalfZ + dist * 0.85f);

            // Keep strictly outside [-68, +68] x [-93, +93] and inside ±360m
            if (Mathf.Abs(x) <= 68f && Mathf.Abs(z) <= 93f) return false;
            if (Mathf.Abs(x) > 360f || Mathf.Abs(z) > 360f) return false;

            // Keep clear of extended river channel
            float riverCx = ExtendedRiverCenterX(z);
            float riverHw = ExtendedRiverHalfWidth(z);
            if (Mathf.Abs(x - riverCx) < riverHw + 12f) return false;

            float minSpacingSq = minSpacing * minSpacing;
            for (int i = 0; i < existing.Count; i++)
            {
                float ddx = existing[i].x - x;
                float ddz = existing[i].y - z;
                if (ddx * ddx + ddz * ddz < minSpacingSq) return false;
            }

            return true;
        }

        private static void CreateBoundaryWall(Transform parent, string name, Vector3 center, Vector3 size)
        {
            GameObject wall = new GameObject(name);
            wall.transform.SetParent(parent, false);
            BoxCollider box = wall.AddComponent<BoxCollider>();
            box.isTrigger = false;
            box.center = center;
            box.size = size;
        }

        private static void CreateRiverContinuationRibbon(
            Transform parent,
            string name,
            float zStart,
            float zEnd,
            Material waterMat)
        {
            const int segments = 24;
            Vector3[] verts = new Vector3[(segments + 1) * 2];
            Vector2[] uvs = new Vector2[(segments + 1) * 2];
            int[] tris = new int[segments * 6];

            bool reverseWinding = zEnd < zStart;

            for (int i = 0; i <= segments; i++)
            {
                float t = (float)i / segments;
                float z = Mathf.Lerp(zStart, zEnd, t);
                float cx = ExtendedRiverCenterX(z);
                float hw = ExtendedRiverHalfWidth(z) + 6f;

                int vIdx = i * 2;
                verts[vIdx] = new Vector3(cx - hw, 0f, z);
                verts[vIdx + 1] = new Vector3(cx + hw, 0f, z);

                uvs[vIdx] = new Vector2(0f, z * 0.05f);
                uvs[vIdx + 1] = new Vector2(1f, z * 0.05f);

                if (i < segments)
                {
                    int tIdx = i * 6;
                    int a = vIdx;
                    int b = vIdx + 1;
                    int c = vIdx + 2;
                    int d = vIdx + 3;

                    if (!reverseWinding)
                    {
                        tris[tIdx] = a;
                        tris[tIdx + 1] = c;
                        tris[tIdx + 2] = b;
                        tris[tIdx + 3] = b;
                        tris[tIdx + 4] = c;
                        tris[tIdx + 5] = d;
                    }
                    else
                    {
                        tris[tIdx] = a;
                        tris[tIdx + 1] = b;
                        tris[tIdx + 2] = c;
                        tris[tIdx + 3] = b;
                        tris[tIdx + 4] = d;
                        tris[tIdx + 5] = c;
                    }
                }
            }

            Mesh mesh = new Mesh { name = $"{name}_Mesh" };
            mesh.vertices = verts;
            mesh.uv = uvs;
            mesh.triangles = tris;
            mesh.RecalculateNormals();
            mesh.RecalculateBounds();

            GameObject go = new GameObject(name);
            go.transform.SetParent(parent, false);
            MeshFilter mf = go.AddComponent<MeshFilter>();
            mf.sharedMesh = mesh;
            MeshRenderer mr = go.AddComponent<MeshRenderer>();
            mr.sharedMaterial = waterMat;
            mr.shadowCastingMode = ShadowCastingMode.Off;
            mr.receiveShadows = true;
            go.AddComponent<RiverWaterSurfaceFollower>();
        }

        private static Mesh BuildBackdropHillsMesh()
        {
            float[] xs = BuildAxisSamples(PlayHalfX - OverlapInward, OuterExtent, includeInnerFine: true);
            float[] zs = BuildAxisSamples(PlayHalfZ - OverlapInward, OuterExtent, includeInnerFine: false);

            int nx = xs.Length;
            int nz = zs.Length;

            float holeX = PlayHalfX - OverlapInward;
            float holeZ = PlayHalfZ - OverlapInward;

            int[,] vertRemap = new int[nx, nz];
            for (int ix = 0; ix < nx; ix++)
            {
                for (int iz = 0; iz < nz; iz++)
                {
                    vertRemap[ix, iz] = -1;
                }
            }

            List<Vector3> verts = new List<Vector3>(1800);
            List<Vector2> uvs = new List<Vector2>(1800);
            List<int> tris = new List<int>(9000);

            int GetOrAddVertex(int ix, int iz)
            {
                int existing = vertRemap[ix, iz];
                if (existing >= 0) return existing;

                float wx = xs[ix];
                float wz = zs[iz];
                float wy = SampleBackdropHeight(wx, wz);

                int idx = verts.Count;
                verts.Add(new Vector3(wx, wy, wz));
                uvs.Add(new Vector2(wx * 0.08f, wz * 0.08f));
                vertRemap[ix, iz] = idx;
                return idx;
            }

            for (int iz = 0; iz < nz - 1; iz++)
            {
                float zc = 0.5f * (zs[iz] + zs[iz + 1]);
                for (int ix = 0; ix < nx - 1; ix++)
                {
                    float xc = 0.5f * (xs[ix] + xs[ix + 1]);
                    if (Mathf.Abs(xc) < holeX && Mathf.Abs(zc) < holeZ)
                    {
                        continue;
                    }

                    int bl = GetOrAddVertex(ix, iz);
                    int br = GetOrAddVertex(ix + 1, iz);
                    int tl = GetOrAddVertex(ix, iz + 1);
                    int tr = GetOrAddVertex(ix + 1, iz + 1);

                    tris.Add(bl);
                    tris.Add(tl);
                    tris.Add(br);
                    tris.Add(br);
                    tris.Add(tl);
                    tris.Add(tr);
                }
            }

            Mesh mesh = new Mesh { name = "Backdrop_RollingHills_Mesh" };
            mesh.SetVertices(verts);
            mesh.SetUVs(0, uvs);
            mesh.SetTriangles(tris, 0);
            mesh.RecalculateNormals();
            mesh.RecalculateBounds();
            return mesh;
        }

        private static float[] BuildAxisSamples(float holeHalf, float outerMax, bool includeInnerFine)
        {
            // Non-uniform spacing: finer near play edge (~10-15m), coarser far out (~35-45m)
            float[] outerOffsets = new float[]
            {
                0f, 10f, 22f, 36f, 54f, 76f, 104f, 138f, 178f, 224f, 276f, outerMax - holeHalf
            };

            List<float> samples = new List<float>(40);

            for (int i = outerOffsets.Length - 1; i >= 0; i--)
            {
                samples.Add(-(holeHalf + outerOffsets[i]));
            }

            if (includeInnerFine)
            {
                // Finer X samples across inner span so upstream/downstream river carving stays smooth
                float[] innerX = new float[] { -52f, -38f, -26f, -16f, -8f, 0f, 8f, 16f, 26f, 38f, 52f };
                samples.AddRange(innerX);
            }
            else
            {
                const int innerSteps = 14;
                for (int i = 1; i < innerSteps; i++)
                {
                    float t = (float)i / innerSteps;
                    samples.Add(Mathf.Lerp(-holeHalf, holeHalf, t));
                }
            }

            for (int i = 0; i < outerOffsets.Length; i++)
            {
                samples.Add(holeHalf + outerOffsets[i]);
            }

            return samples.ToArray();
        }

        private static float ExtendedRiverCenterX(float wz)
        {
            if (wz < -PlayHalfZ)
            {
                float dz = wz + PlayHalfZ; // negative
                float cx0 = (RiverMath.RiverCenterMapX(0f) - RiverMath.WorldW * 0.5f) * RiverMath.MapScale;
                float slope0 = 58f * Mathf.PI * 1.6f / RiverMath.WorldH;
                return cx0 + Mathf.Sin(dz * 0.012f) * (slope0 / 0.012f);
            }

            if (wz > PlayHalfZ)
            {
                float dz = wz - PlayHalfZ; // positive
                float cx1 = (RiverMath.RiverCenterMapX(RiverMath.WorldH) - RiverMath.WorldW * 0.5f) * RiverMath.MapScale;
                float slope1 = 58f * Mathf.PI * 1.6f / RiverMath.WorldH * Mathf.Cos(Mathf.PI * 1.6f);
                return cx1 + Mathf.Sin(dz * 0.011f) * (slope1 / 0.011f) + (1f - Mathf.Cos(dz * 0.008f)) * 10f;
            }

            float mapY = wz / RiverMath.MapScale + RiverMath.WorldH * 0.5f;
            return (RiverMath.RiverCenterMapX(mapY) - RiverMath.WorldW * 0.5f) * RiverMath.MapScale;
        }

        private static float ExtendedRiverHalfWidth(float wz)
        {
            if (wz < -PlayHalfZ)
            {
                float hw0 = RiverMath.RiverHalfWidthMap(0f) * RiverMath.MapScale;
                float t = SmoothStep(0f, 180f, -PlayHalfZ - wz);
                return Mathf.Lerp(hw0, 15f, t);
            }

            if (wz > PlayHalfZ)
            {
                float hw1 = RiverMath.RiverHalfWidthMap(RiverMath.WorldH) * RiverMath.MapScale;
                float t = SmoothStep(0f, 180f, wz - PlayHalfZ);
                return Mathf.Lerp(hw1, 15f, t);
            }

            float mapY = wz / RiverMath.MapScale + RiverMath.WorldH * 0.5f;
            return RiverMath.RiverHalfWidthMap(mapY) * RiverMath.MapScale;
        }

        private static float SmoothStep(float edge0, float edge1, float x)
        {
            if (Mathf.Approximately(edge0, edge1)) return x >= edge1 ? 1f : 0f;
            float t = Mathf.Clamp01((x - edge0) / (edge1 - edge0));
            return t * t * (3f - 2f * t);
        }

        private static void EnsureCacheAssets(SceneAssetCache cache)
        {
            if (cache.TreeTrunkMesh == null) cache.TreeTrunkMesh = BuildTreeTrunkMesh();
            if (cache.TreeCrownMesh == null) cache.TreeCrownMesh = BuildTreeCrownMesh();
            if (cache.HouseSilhouetteMesh == null) cache.HouseSilhouetteMesh = BuildHouseSilhouetteMesh();

            if (cache.TreeTrunkMat == null)
            {
                Material loadedTrunk = AssetDatabase.LoadAssetAtPath<Material>(TrunkMatPath);
                cache.TreeTrunkMat = loadedTrunk != null
                    ? loadedTrunk
                    : CreateLitMaterial("M_Shared_TreeTrunk", new Color(0.38f, 0.25f, 0.16f), 0.12f);
            }

            if (cache.TreeCrownMatA == null)
            {
                cache.TreeCrownMatA = CreateLitMaterial("M_Shared_TreeCrownA", new Color32(0x3B, 0x63, 0x36, 0xFF), 0.12f);
            }
            if (cache.TreeCrownMatB == null)
            {
                cache.TreeCrownMatB = CreateLitMaterial("M_Shared_TreeCrownB", new Color32(0x4D, 0x77, 0x40, 0xFF), 0.12f);
            }
            if (cache.SilhouetteWallMat == null)
            {
                cache.SilhouetteWallMat = CreateLitMaterial("M_Shared_SilhouetteWall", new Color32(0x9E, 0x8D, 0x78, 0xFF), 0.10f);
            }
            if (cache.SilhouetteRoofMat == null)
            {
                cache.SilhouetteRoofMat = CreateLitMaterial("M_Shared_SilhouetteRoof", new Color32(0x7D, 0x4B, 0x37, 0xFF), 0.15f);
            }
        }

        private static Material CreateLitMaterial(string name, Color color, float smoothness)
        {
            Shader sh = Shader.Find("Universal Render Pipeline/Lit");
            if (sh == null) sh = Shader.Find("Standard");

            Material mat = new Material(sh)
            {
                name = name,
                enableInstancing = true
            };

            if (mat.HasProperty("_BaseColor")) mat.SetColor("_BaseColor", color);
            if (mat.HasProperty("_Color")) mat.SetColor("_Color", color);
            if (mat.HasProperty("_Smoothness")) mat.SetFloat("_Smoothness", smoothness);
            else if (mat.HasProperty("_Glossiness")) mat.SetFloat("_Glossiness", smoothness);

            return mat;
        }

        private static Mesh BuildTreeTrunkMesh()
        {
            const int sides = 7;
            const float radiusBottom = 0.22f;
            const float radiusTop = 0.11f;
            const float yBottom = -0.1f;
            const float yTop = 3.0f; // total height = 3.1f

            List<Vector3> verts = new List<Vector3>(sides * 6);
            List<int> tris = new List<int>(sides * 9);

            Vector3 topCenter = new Vector3(0f, yTop, 0f);

            for (int i = 0; i < sides; i++)
            {
                float a0 = (i / (float)sides) * Mathf.PI * 2f;
                float a1 = ((i + 1) / (float)sides) * Mathf.PI * 2f;

                Vector3 b0 = new Vector3(Mathf.Cos(a0) * radiusBottom, yBottom, Mathf.Sin(a0) * radiusBottom);
                Vector3 b1 = new Vector3(Mathf.Cos(a1) * radiusBottom, yBottom, Mathf.Sin(a1) * radiusBottom);
                Vector3 t0 = new Vector3(Mathf.Cos(a0) * radiusTop, yTop, Mathf.Sin(a0) * radiusTop);
                Vector3 t1 = new Vector3(Mathf.Cos(a1) * radiusTop, yTop, Mathf.Sin(a1) * radiusTop);

                // Side quad (2 flat-shaded triangles, outward winding)
                int baseIdx = verts.Count;
                verts.Add(b0);
                verts.Add(b1);
                verts.Add(t0);
                verts.Add(t1);

                tris.Add(baseIdx);
                tris.Add(baseIdx + 2);
                tris.Add(baseIdx + 1);
                tris.Add(baseIdx + 1);
                tris.Add(baseIdx + 2);
                tris.Add(baseIdx + 3);

                // Top cap
                int capIdx = verts.Count;
                verts.Add(t0);
                verts.Add(t1);
                verts.Add(topCenter);
                tris.Add(capIdx);
                tris.Add(capIdx + 2);
                tris.Add(capIdx + 1);
            }

            Mesh mesh = new Mesh { name = "SM_Backdrop_TreeTrunk" };
            mesh.SetVertices(verts);
            mesh.SetTriangles(tris, 0);
            mesh.RecalculateNormals();
            mesh.RecalculateBounds();
            return mesh;
        }

        private static Mesh BuildTreeCrownMesh()
        {
            List<Vector3> verts = new List<Vector3>(180);
            List<int> tris = new List<int>(180);

            // 3 overlapping slim organic faceted clusters spanning Y = 2.15 .. 5.00, max radius <= 1.45m
            AppendFacetedIcosahedron(verts, tris, new Vector3(0.00f, 3.15f, 0.00f), new Vector3(1.42f, 1.00f, 1.38f));
            AppendFacetedIcosahedron(verts, tris, new Vector3(0.24f, 3.85f, -0.20f), new Vector3(1.12f, 0.88f, 1.08f));
            AppendFacetedIcosahedron(verts, tris, new Vector3(-0.16f, 4.30f, 0.16f), new Vector3(0.84f, 0.70f, 0.82f));

            Mesh mesh = new Mesh { name = "SM_Backdrop_TreeCrown" };
            mesh.SetVertices(verts);
            mesh.SetTriangles(tris, 0);
            mesh.RecalculateNormals();
            mesh.RecalculateBounds();
            return mesh;
        }

        private static void AppendFacetedIcosahedron(
            List<Vector3> verts,
            List<int> tris,
            Vector3 center,
            Vector3 radii)
        {
            float t = (1f + Mathf.Sqrt(5f)) * 0.5f;
            Vector3[] raw = new Vector3[]
            {
                new Vector3(-1f,  t, 0f), new Vector3( 1f,  t, 0f), new Vector3(-1f, -t, 0f), new Vector3( 1f, -t, 0f),
                new Vector3( 0f, -1f,  t), new Vector3( 0f,  1f,  t), new Vector3( 0f, -1f, -t), new Vector3( 0f,  1f, -t),
                new Vector3( t, 0f, -1f), new Vector3( t, 0f,  1f), new Vector3(-t, 0f, -1f), new Vector3(-t, 0f,  1f)
            };

            for (int i = 0; i < raw.Length; i++)
            {
                Vector3 n = raw[i].normalized;
                raw[i] = center + Vector3.Scale(n, radii);
            }

            int[] faces = new int[]
            {
                0, 11, 5,  0, 5, 1,  0, 1, 7,  0, 7, 10, 0, 10, 11,
                1, 5, 9,   5, 11, 4, 11, 10, 2, 10, 7, 6, 7, 1, 8,
                3, 9, 4,   3, 4, 2,  3, 2, 6,  3, 6, 8,  3, 8, 9,
                4, 9, 5,   2, 4, 11, 6, 2, 10, 8, 6, 7,  9, 8, 1
            };

            for (int i = 0; i < faces.Length; i += 3)
            {
                int idx = verts.Count;
                verts.Add(raw[faces[i]]);
                verts.Add(raw[faces[i + 1]]);
                verts.Add(raw[faces[i + 2]]);
                tris.Add(idx);
                tris.Add(idx + 1);
                tris.Add(idx + 2);
            }
        }

        private static Mesh BuildHouseSilhouetteMesh()
        {
            // ~6m wide (X), ~4.6m tall (Y), ~5m deep (Z), 2 submeshes: 0 = walls, 1 = pitched roof
            List<Vector3> verts = new List<Vector3>(64);
            List<int> wallTris = new List<int>(36);
            List<int> roofTris = new List<int>(36);

            const float hw = 3.0f;
            const float hd = 2.5f;
            const float wallH = 3.1f;
            const float roofOverhang = 0.35f;
            const float ridgeH = 4.6f;

            // Walls box [(-hw, 0, -hd) .. (hw, wallH, hd)]
            AddQuad(verts, wallTris, new Vector3(-hw, 0f, -hd), new Vector3(hw, 0f, -hd), new Vector3(hw, wallH, -hd), new Vector3(-hw, wallH, -hd));
            AddQuad(verts, wallTris, new Vector3(hw, 0f, hd), new Vector3(-hw, 0f, hd), new Vector3(-hw, wallH, hd), new Vector3(hw, wallH, hd));
            AddQuad(verts, wallTris, new Vector3(-hw, 0f, hd), new Vector3(-hw, 0f, -hd), new Vector3(-hw, wallH, -hd), new Vector3(-hw, wallH, hd));
            AddQuad(verts, wallTris, new Vector3(hw, 0f, -hd), new Vector3(hw, 0f, hd), new Vector3(hw, wallH, hd), new Vector3(hw, wallH, -hd));

            // Pitched gable roof (ridge runs along Z)
            float rw = hw + roofOverhang;
            float rd = hd + roofOverhang;
            float eaveY = wallH - 0.1f;

            Vector3 fl = new Vector3(-rw, eaveY, -rd);
            Vector3 fr = new Vector3(rw, eaveY, -rd);
            Vector3 bl = new Vector3(-rw, eaveY, rd);
            Vector3 br = new Vector3(rw, eaveY, rd);
            Vector3 rf = new Vector3(0f, ridgeH, -rd);
            Vector3 rb = new Vector3(0f, ridgeH, rd);

            // Left slope, right slope, front gable, back gable
            AddQuad(verts, roofTris, fl, rf, rb, bl);
            AddQuad(verts, roofTris, rf, fr, br, rb);
            AddTri(verts, roofTris, fl, fr, rf);
            AddTri(verts, roofTris, br, bl, rb);

            Mesh mesh = new Mesh
            {
                name = "SM_Backdrop_HouseSilhouette",
                subMeshCount = 2
            };
            mesh.SetVertices(verts);
            mesh.SetTriangles(wallTris, 0);
            mesh.SetTriangles(roofTris, 1);
            mesh.RecalculateNormals();
            mesh.RecalculateBounds();
            return mesh;
        }

        private static void AddQuad(List<Vector3> verts, List<int> tris, Vector3 a, Vector3 b, Vector3 c, Vector3 d)
        {
            int idx = verts.Count;
            verts.Add(a);
            verts.Add(b);
            verts.Add(c);
            verts.Add(d);

            tris.Add(idx);
            tris.Add(idx + 2);
            tris.Add(idx + 1);
            tris.Add(idx);
            tris.Add(idx + 3);
            tris.Add(idx + 2);
        }

        private static void AddTri(List<Vector3> verts, List<int> tris, Vector3 a, Vector3 b, Vector3 c)
        {
            int idx = verts.Count;
            verts.Add(a);
            verts.Add(b);
            verts.Add(c);
            tris.Add(idx);
            tris.Add(idx + 2);
            tris.Add(idx + 1);
        }
    }
}
#endif
