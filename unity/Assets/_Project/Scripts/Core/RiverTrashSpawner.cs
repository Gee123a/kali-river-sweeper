using UnityEngine;

namespace KaliRiverSweeper.Core
{
    /// <summary>
    /// Spawns Normal, Medical, and Biohazard waste upstream near Gunung Sampah (-Z)
    /// so debris drifts downstream (+Z) toward Pintu Air and raises water level linearly until cleared.
    /// </summary>
    public class RiverTrashSpawner : MonoBehaviour
    {
        [Header("Optional Prefabs (Fallback Primitives Used If Empty)")]
        public GameObject[] normalPrefabs;
        public GameObject[] medicalPrefabs;
        public GameObject[] biohazardPrefabs;

        [Header("Spawn Tuning")]
        // Spec said ~2.0 s; progression_sim.py shows 2-4 unit bundles every 2.0 s flood every archetype by ~200 s
        // (cargo 8 can't keep up). 4.0 s (2.0 s in the storm) hits idle flood ~235 s and keeps an active sweeper alive.
        public float baseSpawnInterval = 4.0f;
        public float monsoonIntervalMultiplier = 0.5f;
        public float kampungBinsSlowdownMultiplier = 2.5f;
        public int maxVisualFloatingTrash = 120;

        [Header("Readable Bundles (spec D)")]
        public float bundleVisualScale = 2.2f;
        public int minBundleUnits = 2;
        public int maxBundleUnits = 4;
        public float upstreamSpawnMinZ = -60f;
        public float upstreamSpawnMaxZ = -46f;

        private float spawnTimer;
        private Transform trashRoot;

        public void SetTrashRoot(Transform root)
        {
            trashRoot = root;
        }

        public void ResetSpawnerState()
        {
            spawnTimer = 0f;
        }

        private void Update()
        {
            RiverGameManager gm = RiverGameManager.Instance;
            if (gm == null || gm.State != KaliGameState.Playing || gm.activeEnding != GameEnding.None) return;
            if (gm.gunungSampahHealth <= 0.01f) return;

            float interval = baseSpawnInterval;
            if (gm.isMonsoonStorm) interval *= monsoonIntervalMultiplier;
            if (gm.kampungBinsInstalled) interval *= kampungBinsSlowdownMultiplier;

            // As Gunung Sampah is dismantled, shedding slows down proportionally.
            float gunungFactor = Mathf.Lerp(2.4f, 1.0f, gm.gunungSampahHealth);
            interval *= gunungFactor;

            spawnTimer += Time.deltaTime;
            if (spawnTimer < interval) return;
            spawnTimer = 0f;

            // ponytail: the spawn parent's child count stands in for live visual objects (cheap, no registry).
            Transform parent = trashRoot != null ? trashRoot : transform;
            if (parent.childCount >= maxVisualFloatingTrash)
            {
                // Cap active visual GameObjects to protect 60+ FPS while still escalating river pileup pressure.
                gm.AddPiledTrash(Random.Range(minBundleUnits, maxBundleUnits + 1));
                return;
            }

            SpawnRandomTrash();
        }

        public GameObject SpawnRandomTrash()
        {
            WasteClass wc = RiverGameManager.RollWasteClass(Random.value);
            float z = Random.Range(upstreamSpawnMinZ, upstreamSpawnMaxZ);
            float mapY = z / RiverMath.MapScale + RiverMath.WorldH * 0.5f;
            float centerX = (RiverMath.RiverCenterMapX(mapY) - RiverMath.WorldW * 0.5f) * RiverMath.MapScale;
            float halfW = RiverMath.RiverHalfWidthMap(mapY) * RiverMath.MapScale * 0.65f;
            float x = centerX + Random.Range(-halfW, halfW);
            float y = RiverGameManager.Instance != null ? RiverGameManager.Instance.currentWaterLevelY : 0f;

            return SpawnTrashAt(new Vector3(x, y, z), wc);
        }

        // units 0 = random bundle size (minBundleUnits..maxBundleUnits); restart re-seeds map piles with 1.
        public GameObject SpawnTrashAt(Vector3 worldPos, WasteClass wasteClass, int units = 0)
        {
            GameObject prefab = PickPrefab(wasteClass);
            Transform parent = trashRoot != null ? trashRoot : transform;
            GameObject go;

            if (prefab != null)
            {
                go = Instantiate(prefab, worldPos, Quaternion.Euler(0f, Random.Range(0f, 360f), 0f), parent);
                go.transform.localScale *= bundleVisualScale; // prop scale (7-22 cm) -> readable bundle; colliders scale with it
            }
            else
            {
                go = CreateFallbackTrashPrimitive(wasteClass, worldPos, parent);
            }

            RiverTrashItem item = go.GetComponent<RiverTrashItem>();
            if (item == null) item = go.AddComponent<RiverTrashItem>();
            item.TryUnregister(); // prefab instances register 1 unit in OnEnable; re-register with the bundle size
            item.wasteClass = wasteClass;
            item.trashUnits = units > 0 ? units : Random.Range(minBundleUnits, maxBundleUnits + 1);
            item.TryRegister();

            if (go.GetComponent<RiverFlowBuoyancy>() == null)
            {
                go.AddComponent<RiverFlowBuoyancy>();
            }
            if (go.GetComponentInChildren<Collider>(true) == null)
            {
                BoxCollider bc = go.AddComponent<BoxCollider>();
                bool hasBounds = false;
                Bounds bounds = default;
                foreach (Renderer r in go.GetComponentsInChildren<Renderer>())
                {
                    if (r is ParticleSystemRenderer) continue;
                    if (!hasBounds)
                    {
                        bounds = r.bounds;
                        hasBounds = true;
                    }
                    else
                    {
                        bounds.Encapsulate(r.bounds);
                    }
                }

                if (hasBounds)
                {
                    // ponytail: one combined box from renderer bounds, no per-mesh colliders.
                    Vector3 ls = go.transform.lossyScale;
                    bc.center = go.transform.InverseTransformPoint(bounds.center);
                    bc.size = Vector3.Scale(bounds.size, new Vector3(
                        1f / Mathf.Max(ls.x, 0.0001f),
                        1f / Mathf.Max(ls.y, 0.0001f),
                        1f / Mathf.Max(ls.z, 0.0001f)));
                }
                else
                {
                    bc.size = Vector3.one * 0.85f;
                }
            }

            return go;
        }

        private GameObject PickPrefab(WasteClass wasteClass)
        {
            GameObject[] pool = wasteClass switch
            {
                WasteClass.Medical => medicalPrefabs,
                WasteClass.Biohazard => biohazardPrefabs,
                _ => normalPrefabs
            };
            if (pool == null || pool.Length == 0) return null;
            return pool[Random.Range(0, pool.Length)];
        }

        private static GameObject CreateFallbackTrashPrimitive(WasteClass wasteClass, Vector3 pos, Transform parent)
        {
            PrimitiveType prim = wasteClass switch
            {
                WasteClass.Biohazard => PrimitiveType.Cylinder,
                WasteClass.Medical => PrimitiveType.Cube,
                _ => PrimitiveType.Cube
            };

            GameObject go = GameObject.CreatePrimitive(prim);
            go.transform.SetParent(parent);
            go.transform.position = pos;
            go.transform.rotation = Quaternion.Euler(0f, Random.Range(0f, 360f), 0f);

            Color col;
            if (wasteClass == WasteClass.Biohazard)
            {
                go.name = "PF_Trash_BiohazardDrum_Fallback";
                go.transform.localScale = new Vector3(0.75f, 0.85f, 0.75f);
                col = new Color(0.66f, 0.33f, 0.97f); // Radioactive hazard purple
            }
            else if (wasteClass == WasteClass.Medical)
            {
                go.name = "PF_Trash_MedicalBox_Fallback";
                go.transform.localScale = new Vector3(0.65f, 0.45f, 0.55f);
                col = new Color(0.92f, 0.70f, 0.03f); // Hazard yellow B3
            }
            else
            {
                go.name = "PF_Trash_Normal_Fallback";
                go.transform.localScale = new Vector3(0.70f, 0.35f, 0.50f);
                col = new Color(0.22f, 0.74f, 0.97f); // Plastic PET blue
            }

            Renderer r = go.GetComponent<Renderer>();
            if (r != null)
            {
                Shader sh = Shader.Find("Universal Render Pipeline/Lit") ?? Shader.Find("Standard");
                Material mat = new Material(sh) { color = col };
                if (wasteClass == WasteClass.Biohazard && mat.HasProperty("_EmissionColor"))
                {
                    mat.EnableKeyword("_EMISSION");
                    mat.SetColor("_EmissionColor", col * 0.45f);
                }
                r.sharedMaterial = mat;
            }

            return go;
        }
    }
}
