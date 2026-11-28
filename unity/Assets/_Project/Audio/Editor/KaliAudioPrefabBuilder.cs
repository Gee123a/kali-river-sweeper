using UnityEditor;
using UnityEngine;

namespace KaliRiverSweeper.Audio.Editor
{
    /// <summary>
    /// Builds Assets/_Project/Audio/Prefabs/Audio_Director.prefab with all generated WAV clips wired.
    /// Run from menu: KALI > Audio > Build Audio_Director.
    /// </summary>
    public static class KaliAudioPrefabBuilder
    {
        private const string ClipFolder = "Assets/_Project/Audio/Clips/";
        private const string PrefabFolder = "Assets/_Project/Audio/Prefabs";
        private const string PrefabPath = PrefabFolder + "/Audio_Director.prefab";

        [MenuItem("KALI/Audio/Build Audio_Director")]
        public static void Build()
        {
            if (!AssetDatabase.IsValidFolder(PrefabFolder))
            {
                AssetDatabase.CreateFolder("Assets/_Project/Audio", "Prefabs");
            }

            GameObject root = new GameObject("Audio_Director", typeof(KaliAudioDirector));
            KaliAudioDirector director = root.GetComponent<KaliAudioDirector>();

            director.bgmKalimasTheme = LoadClip("BGM_KalimasTheme.wav");
            director.ambRiverCalm = LoadClip("AMB_RiverCalm.wav");
            director.ambMonsoonStorm = LoadClip("AMB_MonsoonStorm.wav");
            director.sfxWaterSplash = LoadClip("SFX_WaterSplashMuddy.wav");
            director.sfxGunungAvalanche = LoadClip("SFX_GunungAvalanche.wav");
            director.sfxSirenSiaga = LoadClip("SFX_SirenSiaga.wav");
            director.sfxBiohazardGeiger = LoadClip("SFX_BiohazardGeiger.wav");
            director.sfxMedicalPrickAlert = LoadClip("SFX_MedicalPrickAlert.wav");
            director.sfxStationPass = LoadClip("SFX_StationPass.wav");
            director.sfxStationFineBuzzer = LoadClip("SFX_StationFineBuzzer.wav");
            director.sfxToolUnlockFanfare = LoadClip("SFX_ToolUnlockFanfare.wav");
            director.sfxEquipClick = LoadClip("SFX_EquipClick.wav");
            director.sfxVictorySdg = LoadClip("SFX_VictorySdg.wav");
            director.sfxEndingFail = LoadClip("SFX_EndingFail.wav");
            director.sfxNpcTalkBlip = LoadClip("SFX_NpcTalkBlip.wav");
            director.sfxQuestComplete = LoadClip("SFX_QuestComplete.wav");

            PrefabUtility.SaveAsPrefabAsset(root, PrefabPath);
            Object.DestroyImmediate(root);
            AssetDatabase.Refresh();
            Debug.Log("Audio_Director prefab written to " + PrefabPath);
        }

        private static AudioClip LoadClip(string fileName)
        {
            return AssetDatabase.LoadAssetAtPath<AudioClip>(ClipFolder + fileName);
        }
    }
}
