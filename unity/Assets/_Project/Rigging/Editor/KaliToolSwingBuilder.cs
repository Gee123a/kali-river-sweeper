#if UNITY_EDITOR
using System.Linq;
using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;

namespace KaliRiverSweeper.RiggingEditor
{
    /// <summary>
    /// Task 5C: wires the first-person tool swing.
    /// Menu: KALI > JC > Build Tool Swing Rig.
    ///   Rigging/Animation/AC_PlayerToolSwing.controller  (Generic: Idle_Hold default, SerokanScoop / GancoHookSwing
    ///                                                     one-shots via triggers "Scoop" / "Hook", back to Idle_Hold)
    ///   Rigging/PF_PlayerArms.prefab                      (SK_PlayerArms + Animator, tools go under .../ToolHolder)
    ///   Rigging/PF_ToolHolderRig.prefab                   (Anim_PlayerToolSwing without arms, same controller layout)
    /// Usage (Ivan): put the prefab under Main Camera/ToolSocket at local 0, parent the equipped PF_Tool_* under its
    /// ToolHolder at localRotation Euler(65, -8, 0), fire SetTrigger("Scoop") / SetTrigger("Hook") on use, and turn off
    /// the procedural ToolSocket rock so the two motions do not add up (see Rigging/README.md).
    /// </summary>
    public static class KaliToolSwingBuilder
    {
        private const string Root = "Assets/_Project/Rigging";
        private const string ArmsFbx = Root + "/SK_PlayerArms.fbx";
        private const string HolderFbx = Root + "/Anim_PlayerToolSwing.fbx";
        private const string ArmsController = Root + "/Animation/AC_PlayerArms.controller";
        private const string HolderController = Root + "/Animation/AC_PlayerToolSwing.controller";
        public const string ScoopTrigger = "Scoop";
        public const string HookTrigger = "Hook";

        [MenuItem("KALI/JC/Build Tool Swing Rig")]
        public static void Build()
        {
            if (!AssetDatabase.IsValidFolder(Root + "/Animation")) AssetDatabase.CreateFolder(Root, "Animation");

            bool arms = BuildOne(ArmsFbx, ArmsController, Root + "/PF_PlayerArms.prefab", hasIdle: true);
            bool holder = BuildOne(HolderFbx, HolderController, Root + "/PF_ToolHolderRig.prefab", hasIdle: false);

            AssetDatabase.SaveAssets();
            Debug.Log("[KALI] Tool swing rig: PF_PlayerArms=" + arms + ", PF_ToolHolderRig=" + holder);
        }

        private static bool BuildOne(string fbxPath, string controllerPath, string prefabPath, bool hasIdle)
        {
            var importer = AssetImporter.GetAtPath(fbxPath) as ModelImporter;
            if (importer == null)
            {
                Debug.LogError("[KALI] Missing " + fbxPath);
                return false;
            }

            // Generic rig, loop only the idle (README: Loop Time off for the swings).
            importer.animationType = ModelImporterAnimationType.Generic;
            importer.avatarSetup = ModelImporterAvatarSetup.CreateFromThisModel;
            ModelImporterClipAnimation[] clips = importer.defaultClipAnimations;
            foreach (ModelImporterClipAnimation c in clips) c.loopTime = c.name == "Idle_Hold";
            importer.clipAnimations = clips;
            importer.SaveAndReimport();

            AnimationClip[] all = AssetDatabase.LoadAllAssetsAtPath(fbxPath).OfType<AnimationClip>()
                .Where(c => !c.name.StartsWith("__preview__")).ToArray();
            AnimationClip scoop = all.FirstOrDefault(c => c.name == "SerokanScoop");
            AnimationClip hook = all.FirstOrDefault(c => c.name == "GancoHookSwing");
            AnimationClip idle = all.FirstOrDefault(c => c.name == "Idle_Hold");
            if (scoop == null || hook == null || (hasIdle && idle == null))
            {
                Debug.LogError("[KALI] " + fbxPath + " is missing a swing clip: " + string.Join(", ", all.Select(c => c.name)));
                return false;
            }

            // Rebuilt from scratch each run (asset path kept, so the GUID survives).
            AnimatorController ac = AssetDatabase.LoadAssetAtPath<AnimatorController>(controllerPath);
            if (ac != null) AssetDatabase.DeleteAsset(controllerPath);
            ac = AnimatorController.CreateAnimatorControllerAtPath(controllerPath);
            ac.AddParameter(ScoopTrigger, AnimatorControllerParameterType.Trigger);
            ac.AddParameter(HookTrigger, AnimatorControllerParameterType.Trigger);

            AnimatorStateMachine sm = ac.layers[0].stateMachine;
            AnimatorState rest = sm.AddState(hasIdle ? "Idle_Hold" : "Rest");
            rest.motion = idle;                       // null for the holder rig: bone stays at its rest pose
            sm.defaultState = rest;
            AddSwing(sm, rest, scoop, ScoopTrigger);
            AddSwing(sm, rest, hook, HookTrigger);

            var src = AssetDatabase.LoadAssetAtPath<GameObject>(fbxPath);
            var go = (GameObject)PrefabUtility.InstantiatePrefab(src);
            PrefabUtility.UnpackPrefabInstance(go, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
            go.name = System.IO.Path.GetFileNameWithoutExtension(prefabPath);
            Animator anim = go.GetComponent<Animator>() ?? go.AddComponent<Animator>();
            anim.runtimeAnimatorController = ac;
            anim.applyRootMotion = false;
            anim.cullingMode = AnimatorCullingMode.AlwaysAnimate;   // first-person: never culled
            foreach (Collider c in go.GetComponentsInChildren<Collider>(true)) Object.DestroyImmediate(c);

            PrefabUtility.SaveAsPrefabAsset(go, prefabPath);
            Object.DestroyImmediate(go);
            return true;
        }

        private static void AddSwing(AnimatorStateMachine sm, AnimatorState rest, AnimationClip clip, string trigger)
        {
            AnimatorState s = sm.AddState(clip.name);
            s.motion = clip;

            AnimatorStateTransition enter = rest.AddTransition(s);
            enter.AddCondition(AnimatorConditionMode.If, 0f, trigger);
            enter.hasExitTime = false;
            enter.duration = 0.05f;

            AnimatorStateTransition back = s.AddTransition(rest);
            back.hasExitTime = true;
            back.exitTime = 1f;
            back.duration = 0.1f;
        }
    }
}
#endif
