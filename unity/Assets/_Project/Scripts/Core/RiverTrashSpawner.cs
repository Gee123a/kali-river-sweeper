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
        public float baseSpawnInterval = 4.2f;
        public float monsoonIntervalMultiplier = 0.42f;
        public float kampungBinsSlowdownMultiplier = 2.5f;
        public int maxVisualFloatingTrash = 72;
        public float upstreamSpawnMinZ = -60f;
        public float upstreamSpawnMaxZ = -46f;

        private float spawnTimer;
        private Transform trashRoot;

        public void SetTrashRoot(Transform root)
        {
            trashRoot = root;
        }

        private void Update()
        {
            RiverGameManager gm = RiverGameManager.Instance;
            if (gm == null || gm.activeEnding != GameEnding.None) return;
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

            if (gm.activeRiverTrashCount >= maxVisualFloatingTrash)
            {
                // Cap active visual GameObjects to protect 60+ FPS while still escalating river pileup pressure.
                gm.AddPiledTrash(1);
                return;
            }

            SpawnRandomTrash();
        }

        public GameObject SpawnRandomTrash()
        {
            float roll = Random.value;
            WasteClass wc = roll < 0.62f ? WasteClass.Normal : (roll < 0.85f ? WasteClass.Medical : WasteClass.Biohazard);
            float z = Random.Range(upstreamSpawnMinZ, upstreamSpawnMaxZ);
            float mapY = z / RiverMath.MapScale + RiverMath.WorldH * 0.5f;
            float centerX = (RiverMath.RiverCenterMapX(mapY) - RiverMath.WorldW * 0.5f) * RiverMath.MapScale;
            float halfW = RiverMath.RiverHalfWidthMap(mapY) * RiverMath.MapScale * 0.65f;
            float x = centerX + Random.Range(-halfW, halfW);
            float y = RiverGameManager.Instance != null ? RiverGameManager.Instance.currentWaterLevelY : 0f;

            return SpawnTrashAt(new Vector3(x, y, z), wc);
        }

        public GameObject SpawnTrashAt(Vector3 worldPos, WasteClass wasteClass)
        {
            GameObject prefab = PickPrefab(wasteClass);
            Transform parent = trashRoot != null ? trashRoot : transform;
            GameObject go;

            if (prefab != null)
            {
                go = Instantiate(prefab, worldPos, Quaternion.Euler(0f, Random.Range(0f, 360f), 0f), parent);
            }
            else
            {
                go = CreateFallbackTrashPrimitive(wasteClass, worldPos, parent);
            }

            RiverTrashItem item = go.GetComponent<RiverTrashItem>();
            if (item == null) item = go.AddComponent<RiverTrashItem>();
            item.wasteClass = wasteClass;
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
