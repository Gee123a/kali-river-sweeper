using System.Collections.Generic;
using KaliRiverSweeper.Core;
using UnityEngine;
using UnityEngine.Rendering;

namespace KaliRiverSweeper.Player
{
    /// <summary>
    /// Floating down-pointing chevrons over the current objective's target (service points, docks, Pintu Air pile)
    /// plus one on the nearest trash while the objective is "Trash". Built at Start; the importer assigns the materials.
    /// </summary>
    public sealed class KaliWaypointChevrons : MonoBehaviour
    {
        public Material idleMaterial;
        public Material activeMaterial;

        private const float HoverHeight = 3.2f;
        private const float TrashHoverHeight = 1.6f;
        private const float ActiveScale = 1.8f;
        private const float IdleScale = 0.8f;
        private const float TrashSearchInterval = 0.5f;

        private static Mesh chevronMesh;
        private readonly List<Transform> targets = new List<Transform>();
        private readonly List<Transform> chevrons = new List<Transform>();
        private Transform trashChevron;
        private RiverTrashItem nearestTrash;
        private float nextTrashSearch;
        private KaliPlayerController player;

        public static string PickTargetToken(RiverGameManager gm)
        {
            if (gm == null) return null;
            string[] steps = RiverGameManager.ObjectiveSteps;
            if (gm.isMonsoonStorm) return "PintuAir";
            if (gm.biohazardCargo > 0) return "Karantina Biohazard";
            if (gm.medicalCargo > 0) return "Pos Medis";
            if (gm.cargoCount >= gm.cargoCapacity || (gm.CurrentObjective == steps[1] && gm.normalCargo > 0)) return "Bank Sampah";
            if (gm.CurrentObjective == steps[3]) return "Kopdes";
            if (gm.CurrentObjective == steps[0]) return "Trash";
            return null;
        }

        private void Start()
        {
            if (chevronMesh == null) chevronMesh = BuildChevronMesh();

            foreach (Transform t in FindObjectsOfType<Transform>())
            {
                if (t.name.EndsWith("_ServicePoint")) AddTarget(t);
            }
            foreach (string name in new[] { "Dermaga Awal", "Dermaga Tengah", "PintuAirPile_Zone" })
            {
                GameObject go = GameObject.Find(name);
                if (go != null) AddTarget(go.transform);
            }
            trashChevron = CreateChevron("TrashChevron");
        }

        private void AddTarget(Transform target)
        {
            targets.Add(target);
            chevrons.Add(CreateChevron("Chevron_" + target.name));
        }

        private Transform CreateChevron(string label)
        {
            GameObject go = new GameObject(label);
            go.transform.SetParent(transform, false);
            go.AddComponent<MeshFilter>().sharedMesh = chevronMesh;
            MeshRenderer mr = go.AddComponent<MeshRenderer>();
            mr.shadowCastingMode = ShadowCastingMode.Off;
            mr.receiveShadows = false;
            mr.sharedMaterial = idleMaterial;
            return go.transform;
        }

        private void LateUpdate()
        {
            RiverGameManager gm = RiverGameManager.Instance;
            bool show = gm != null && gm.State == KaliGameState.Playing;
            string token = show ? PickTargetToken(gm) : null;
            Camera cam = Camera.main;
            float bob = Mathf.Sin(Time.time * 3f) * 0.25f;

            for (int i = 0; i < targets.Count; i++)
            {
                Transform target = targets[i];
                bool exists = target != null;
                bool active = exists && token != null && target.name.Contains(token);
                Vector3 pos = exists ? target.position + Vector3.up * (HoverHeight + bob) : chevrons[i].position;
                Place(chevrons[i], pos, active, show && exists, cam);
            }

            bool trashActive = show && token == "Trash";
            if (trashActive && Time.time >= nextTrashSearch)
            {
                nextTrashSearch = Time.time + TrashSearchInterval;
                nearestTrash = FindNearestTrash();
            }
            bool trashShown = trashActive && nearestTrash != null && !nearestTrash.isCollected;
            if (trashShown)
            {
                Place(trashChevron, nearestTrash.transform.position + Vector3.up * TrashHoverHeight, true, true, cam);
            }
            else
            {
                trashChevron.GetComponent<MeshRenderer>().enabled = false;
            }
        }

        private void Place(Transform chevron, Vector3 pos, bool active, bool visible, Camera cam)
        {
            chevron.position = pos;
            chevron.localScale = Vector3.one * (active ? ActiveScale : IdleScale);
            if (cam != null)
            {
                Vector3 toCam = cam.transform.position - pos;
                toCam.y = 0f;
                if (toCam.sqrMagnitude > 0.0001f) chevron.rotation = Quaternion.LookRotation(toCam);
            }
            MeshRenderer mr = chevron.GetComponent<MeshRenderer>();
            mr.enabled = visible;
            mr.sharedMaterial = active ? activeMaterial : idleMaterial;
        }

        private RiverTrashItem FindNearestTrash()
        {
            if (player == null) player = FindObjectOfType<KaliPlayerController>();
            if (player == null) return null;

            RiverTrashItem best = null;
            float bestSqr = float.MaxValue;
            foreach (RiverTrashItem item in FindObjectsOfType<RiverTrashItem>())
            {
                if (item.isCollected) continue;
                float sqr = (item.transform.position - player.transform.position).sqrMagnitude;
                if (sqr < bestSqr)
                {
                    bestSqr = sqr;
                    best = item;
                }
            }
            return best;
        }

        // Down-pointing V, 1.2 m wide, 0.8 m tall, 0.22 m arm thickness, centred on its origin. Both faces.
        private static Mesh BuildChevronMesh()
        {
            Vector3[] v =
            {
                new Vector3(-0.6f, 0.8f, 0f), new Vector3(0f, 0f, 0f), new Vector3(0.6f, 0.8f, 0f),
                new Vector3(0.435f, 0.8f, 0f), new Vector3(0f, 0.22f, 0f), new Vector3(-0.435f, 0.8f, 0f),
            };
            for (int i = 0; i < v.Length; i++) v[i].y -= 0.4f;

            int[] front = { 0, 1, 4, 0, 4, 5, 1, 2, 3, 1, 3, 4 };
            int[] tris = new int[front.Length * 2];
            for (int i = 0; i < front.Length; i += 3)
            {
                tris[i * 2] = front[i];
                tris[i * 2 + 1] = front[i + 1];
                tris[i * 2 + 2] = front[i + 2];
                tris[i * 2 + 3] = front[i];
                tris[i * 2 + 4] = front[i + 2];
                tris[i * 2 + 5] = front[i + 1];
            }

            Mesh mesh = new Mesh { name = "KaliWaypointChevron" };
            mesh.vertices = v;
            mesh.triangles = tris;
            mesh.RecalculateBounds();
            return mesh;
        }
    }
}
