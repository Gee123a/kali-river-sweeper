using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using B = KaliRiverSweeper.EnvEditor.EnvDressingBuilder;

namespace KaliRiverSweeper.EnvEditor
{
    /// <summary>
    /// Wesley (Environment): KALI > Environment > Build Backdrop Hills & Kampung Kit (plan Steps 4B, 4C, 4D).
    ///   PF_Env_BackdropHills      840 m low-poly horizon ring (blender/wesley_env/bukit.py). Same heights as
    ///                             KaliMapBackdropBuilder.SampleBackdropHeight, so Ivan can swap it for the
    ///                             procedural Backdrop_RollingHills 1:1 (place at the origin, no collider).
    ///   PF_Env_JettyKayu          drop-in for KaliKampungBuilder's plank jetty (same pivot, footprint and
    ///                             deck BoxCollider as CreateJettyObject).
    ///   PF_Env_PagarKampung(_Tiang), PF_Env_JalanSetapak(_Tangga)  modular fence bays + footpath tiles.
    /// Re-running is safe: assets are updated in place.
    /// </summary>
    public static class EnvKampungKitBuilder
    {
        private const string Env = "Assets/_Project/Environment/";
        private const string HillsFbx = Env + "Meshes/SM_Env_BackdropHills.fbx";
        private const string KitFbx = Env + "Meshes/SM_Env_KampungKit.fbx";

        [MenuItem("KALI/Environment/Build Backdrop Hills & Kampung Kit")]
        public static void BuildAll()
        {
            BuildMaterials();
            B.RemapFbx(HillsFbx);
            B.RemapFbx(KitFbx);

            var hills = B.MeshObject(HillsFbx, "SM_Env_BackdropHills", "PF_Env_BackdropHills");
            var hr = hills.GetComponent<MeshRenderer>();
            hr.shadowCastingMode = ShadowCastingMode.Off;                  // like Ivan's ring: receives, never casts
            GameObjectUtility.SetStaticEditorFlags(hills, StaticEditorFlags.BatchingStatic | StaticEditorFlags.OccludeeStatic);
            B.Save(hills, "PF_Env_BackdropHills");

            var jetty = new GameObject("PF_Env_JettyKayu");
            B.Child(jetty, KitFbx, "SM_Env_JettyKayu");
            B.Box(jetty, "Jetty_Deck", new Vector3(0.7f, 1.40f, 0f), new Vector3(3.8f, 0.25f, 1.6f));   // = CreateJettyObject
            B.Save(jetty, "PF_Env_JettyKayu");

            var pagar = new GameObject("PF_Env_PagarKampung");
            B.Child(pagar, KitFbx, "SM_Env_PagarBambu");
            B.Box(pagar, "Pagar_Collider", new Vector3(0.07f, 0.6f, 1.0f), new Vector3(0.16f, 1.2f, 2.05f));
            B.Save(pagar, "PF_Env_PagarKampung");

            var tiang = new GameObject("PF_Env_PagarKampung_Tiang");
            B.Child(tiang, KitFbx, "SM_Env_PagarBambu_Tiang");
            B.Box(tiang, "Tiang_Collider", new Vector3(0f, 0.6f, 0f), new Vector3(0.12f, 1.2f, 0.12f));
            B.Save(tiang, "PF_Env_PagarKampung_Tiang");

            var jalan = new GameObject("PF_Env_JalanSetapak");
            B.Child(jalan, KitFbx, "SM_Env_JalanSetapak");
            B.Box(jalan, "Jalan_Collider", new Vector3(0f, -0.04f, 1.0f), new Vector3(1.2f, 0.18f, 2.0f));
            B.Save(jalan, "PF_Env_JalanSetapak");

            var tangga = new GameObject("PF_Env_JalanSetapak_Tangga");
            var tm = B.Child(tangga, KitFbx, "SM_Env_JalanSetapak_Tangga");
            tm.AddComponent<MeshCollider>().sharedMesh = tm.GetComponent<MeshFilter>().sharedMesh;
            B.Save(tangga, "PF_Env_JalanSetapak_Tangga");

            AssetDatabase.SaveAssets();
            Debug.Log("[EnvKampungKitBuilder] PF_Env_BackdropHills, PF_Env_JettyKayu, PF_Env_PagarKampung(+_Tiang), PF_Env_JalanSetapak(+_Tangga) built.");
        }

        private static void BuildMaterials()
        {
                        // same tint as the bank so zone borders never show as a saw-tooth; only the far ridge (>150 m, already
            // in fog) shifts slightly blue-green for aerial perspective
            B.Weathered("M_Env_BukitHijau", "T_Env_TanahRumput", Color.white, 0.08f, 0.15f);
            B.Weathered("M_Env_BukitJauh", "T_Env_TanahRumput", new Color(0.86f, 0.93f, 0.92f), 0.02f, 0f);
            var n = AssetDatabase.LoadAssetAtPath<Texture2D>(Env + "Textures/T_Env_TanahRumput_N.png");
            foreach (var name in new[] { "M_Env_BukitHijau", "M_Env_BukitJauh" })
            {
                var m = AssetDatabase.LoadAssetAtPath<Material>(Env + "Materials/" + name + ".mat");
                m.SetTexture("_BumpMap", n);
                m.SetFloat("_BumpScale", name == "M_Env_BukitHijau" ? 1.0f : 0.4f);
                m.SetFloat("_WetHeight", -10f);                            // hills are never wet
                EditorUtility.SetDirty(m);
            }
        }
    }
}
