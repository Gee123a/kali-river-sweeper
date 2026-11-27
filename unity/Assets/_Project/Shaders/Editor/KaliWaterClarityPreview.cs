#if UNITY_EDITOR
using UnityEditor;
using UnityEngine;

namespace Kali.Shaders.Editor
{
    /// <summary>
    /// Wesley's edit-mode test slider for SG_KaliWater: drives the same global float
    /// RiverGameManager sets at runtime (Shader.SetGlobalFloat("_WaterClarity", ...)).
    /// </summary>
    public class KaliWaterClarityPreview : EditorWindow
    {
        private float clarity = 0.12f;

        [MenuItem("KALI/Wesley/Water Clarity Preview")]
        private static void Open() => GetWindow<KaliWaterClarityPreview>("Water Clarity");

        private void OnGUI()
        {
            EditorGUI.BeginChangeCheck();
            clarity = EditorGUILayout.Slider("_WaterClarity", clarity, 0.05f, 1f);
            if (EditorGUI.EndChangeCheck())
            {
                Shader.SetGlobalFloat("_WaterClarity", clarity);
                SceneView.RepaintAll();
            }
            EditorGUILayout.HelpBox("0.05 = coklat keruh, 1.00 = toska jernih. Di Play mode RiverGameManager mengambil alih nilai ini.", MessageType.Info);
        }
    }
}
#endif
