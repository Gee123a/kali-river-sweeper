using System;
using UnityEngine;

namespace KaliRiverSweeper.Env
{
    /// <summary>
    /// Wesley (Environment): Core Mechanics v2 spec A - floor mark + post sign at every counter.
    /// Ivan's MapJsonImporter creates "&lt;Station&gt;_ServicePoint" (2 m trigger) in front of each station;
    /// this snaps each mark onto the matching service point and turns it so local +X faces the counter
    /// (floor text reads "BERDIRI DI SINI" for a player standing in the ring). No gameplay code needed:
    /// the marks follow the service points even after Ivan re-imports the map.
    /// </summary>
    [DisallowMultipleComponent]
    public class EnvServicePointMarks : MonoBehaviour
    {
        [Serializable]
        public class Mark
        {
            [Tooltip("Part of the station name, e.g. \"Bank Sampah\", \"Kopdes\".")]
            public string keyword;
            public Transform root;
        }

        public const string ServicePointSuffix = "_ServicePoint";
        public Mark[] marks = Array.Empty<Mark>();

        private void Start() => Snap(hideMissing: true);

        /// <summary>Move every mark onto its service point. Returns how many were found.</summary>
        [ContextMenu("Snap to service points")]
        public int Snap(bool hideMissing = false)
        {
            var all = FindObjectsOfType<Transform>();
            int found = 0;
            foreach (var m in marks)
            {
                if (m == null || m.root == null || string.IsNullOrEmpty(m.keyword)) continue;
                Transform sp = null;
                foreach (var t in all)
                {
                    if (t.name.EndsWith(ServicePointSuffix, StringComparison.Ordinal) &&
                        t.name.IndexOf(m.keyword, StringComparison.OrdinalIgnoreCase) >= 0) { sp = t; break; }
                }
                if (sp == null)
                {
                    if (hideMissing) m.root.gameObject.SetActive(false);
                    continue;
                }
                found++;
                // the importer offsets the point along world X only (river-facing side of the building)
                float dx = sp.parent != null ? sp.parent.position.x - sp.position.x : 1f;
                Vector3 toCounter = new Vector3(dx >= 0f ? 1f : -1f, 0f, 0f);
                m.root.SetPositionAndRotation(sp.position,
                    Quaternion.LookRotation(toCounter.normalized, Vector3.up) * Quaternion.Euler(0f, -90f, 0f));
                m.root.gameObject.SetActive(true);
            }
            return found;
        }
    }
}
