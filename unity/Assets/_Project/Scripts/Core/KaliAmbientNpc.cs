using System;
using UnityEngine;
using UnityEngine.Animations;
using UnityEngine.Playables;

namespace KaliRiverSweeper.Core
{
    public enum AmbientNpcRole
    {
        Kids = 0,
        Fisher = 1,
        Washer = 2,
        Chatter = 3
    }

    public enum AmbientNpcSubBehavior
    {
        Standard = 0,
        SeatedFisher = 1,
        StandingFisher = 2,
        KidWader = 3,
        KidChaser = 4,
        KidJettyJumper = 5,
        CrouchedWasher = 6,
        ChatterBinCarrier = 7
    }

    /// <summary>
    /// Drives ambient kampung villager loops (PlayableGraph on SK_VillagerNPC + subtle procedural motion)
    /// with zero per-frame allocations, AnimatorCullUpdateTransforms safety, day/night fade (20:00..05:30),
    /// and monsoon storm water evacuation for kids and washers.
    /// </summary>
    [ExecuteAlways]
    public sealed class KaliAmbientNpc : MonoBehaviour
    {
        private static readonly int BaseColorId = Shader.PropertyToID("_BaseColor");
        private static readonly int ColorId = Shader.PropertyToID("_Color");
        private static readonly int BaseMapId = Shader.PropertyToID("_BaseMap");

        private const float JumperCycle = 5.6f;
        // Clip time at the jumper's take-off (procedural u = 0.36) is 0.87 s into Anim_Kid_JettyJump.
        private const float JumperClipStart = 0.36f * JumperCycle - 0.87f;
        private const string HeadPath = "VillagerRig/Hips/Spine/Chest/Neck/Head";

        private static readonly Quaternion SeatedUpperLegOffset = Quaternion.Euler(-82f, 0f, 0f);
        private static readonly Quaternion SeatedLowerLegOffset = Quaternion.Euler(84f, 0f, 0f);
        private static readonly Quaternion CrouchUpperLegOffset = Quaternion.Euler(-52f, 0f, 0f);
        private static readonly Quaternion CrouchLowerLegOffset = Quaternion.Euler(104f, 0f, 0f);
        private static readonly Quaternion CrouchFootOffset = Quaternion.Euler(-52f, 0f, 0f);
        private static readonly Quaternion CrouchSpineOffset = Quaternion.Euler(22f, 0f, 0f);
        private static readonly Quaternion CrouchChestOffset = Quaternion.Euler(14f, 0f, 0f);
        private static readonly Quaternion LeftArmRestRot = Quaternion.Euler(287.7f, 9.3f, 359.0f);
        private static readonly Quaternion RightArmRestRot = Quaternion.Euler(287.7f, 350.7f, 1.0f);

        [Header("Identity & Placement")]
        public string groupId = string.Empty;
        public AmbientNpcRole role = AmbientNpcRole.Chatter;
        public AmbientNpcSubBehavior subBehavior = AmbientNpcSubBehavior.Standard;
        public Vector3 anchorWorldPos;
        public Quaternion anchorWorldRot = Quaternion.identity;
        public float baseUniformScale = 1f;
        public float phaseOffset;
        public Color clothingTint = Color.white;

        [Header("Clips & Props (Read-Only Assets)")]
        public AnimationClip idleClip;
        public AnimationClip carryBinClip;
        public AnimationClip throwTrashClip;
        [Tooltip("Role clip from SK_VillagerNPC.fbx; when set, procedural bone offsets are skipped.")]
        public AnimationClip poseClip;
        [Tooltip("Played once on PlayTalk (Talk_Gesture). Leave null for seated/swimming/jumping roles.")]
        public AnimationClip talkClip;
        [Tooltip("Per-NPC palette, set as _BaseMap via MaterialPropertyBlock.")]
        public Texture2D paletteTexture;
        public Transform rodPivot;
        public Transform rodTip;
        public Transform rodLine;
        public Transform rodBobber;
        public Transform propRoot;

        [Header("Behavior Bounds")]
        public float chaseRadius = 0.75f;
        public Vector3 chaseAxisWorld = Vector3.forward;
        public Vector3 jumpWaterPos;

        private Animator cachedAnimator;
        private Renderer[] cachedRenderers;
        private MaterialPropertyBlock propBlock;

        private Transform spineBone;
        private Transform chestBone;
        private Transform leftUpperLeg;
        private Transform leftLowerLeg;
        private Transform leftFoot;
        private Transform rightUpperLeg;
        private Transform rightLowerLeg;
        private Transform rightFoot;
        private Transform leftUpperArm;
        private Transform leftLowerArm;
        private Transform rightUpperArm;
        private Transform rightLowerArm;

        private Quaternion lastSpineRot;
        private Quaternion lastChestRot;
        private Quaternion lastLeftUpperLegRot;
        private Quaternion lastLeftLowerLegRot;
        private Quaternion lastLeftFootRot;
        private Quaternion lastRightUpperLegRot;
        private Quaternion lastRightLowerLegRot;
        private Quaternion lastRightFootRot;
        private bool hasAppliedBonePose;

        private PlayableGraph playableGraph;
        private AnimationClipPlayable clipPlayable;
        private float activeClipLength = 1f;
        private bool graphInitialized;
        private AnimationClip graphClip;
        private float talkUntil;

        private float animTimer;
        private float currentVisibility = 1f;
        private bool visualsActive = true;
        private Quaternion rodBaseLocalRot = Quaternion.identity;
        private bool hasRodBaseRot;

        private void Awake()
        {
            CacheComponents();
            ApplyClothingTint();

            if (Application.isPlaying)
            {
                SampleBasePoseForCleanStart();
                SetupPlayableGraph(SelectActiveClip());
            }
        }

        private void OnEnable()
        {
            CacheComponents();
            ApplyClothingTint();

            if (Application.isPlaying && !graphInitialized)
            {
                SampleBasePoseForCleanStart();
                SetupPlayableGraph(SelectActiveClip());
            }
        }

        private void OnDisable()
        {
            DestroyPlayableGraph();
        }

        private void OnDestroy()
        {
            DestroyPlayableGraph();
        }

        public void ApplyEditorPreviewPose()
        {
            CacheComponents();
            ApplyClothingTint();
            SampleBasePoseForCleanStart();
            ApplyAnchoredTransform(phaseOffset);
            ApplyBonePostureOffsets(forceApply: true);
        }

        /// <summary>
        /// Lifts the anchor when the lowest foot over the clip sinks below the ground under it.
        /// Bare and Sarung bodies have lower hips than the base rig, so the same clip sinks their feet
        /// into the bank. Lift-only: base-body NPCs already clear the ground and are not moved.
        /// ponytail: one 16-sample sweep, no per-body config.
        /// </summary>
        public float SettleFeetToGround(AnimationClip clip, float footClearance = 0.07f)
        {
            if (clip == null) return 0f;
            CacheComponents();
            float worst = float.MaxValue;
            Transform[] bones = GetComponentsInChildren<Transform>();
            for (int k = 0; k < 16; k++)
            {
                float t = clip.length * k / 16f;
                clip.SampleAnimation(gameObject, t);
                ApplyAnchoredTransform(t);
                for (int i = 0; i < bones.Length; i++)
                {
                    string n = bones[i].name;
                    if (n.IndexOf("Foot", StringComparison.OrdinalIgnoreCase) < 0 && n.IndexOf("Toe", StringComparison.OrdinalIgnoreCase) < 0) continue;
                    Vector3 p = bones[i].position;
                    float groundY = Physics.Raycast(new Vector3(p.x, 12f, p.z), Vector3.down, out RaycastHit hit, 25f, ~0, QueryTriggerInteraction.Ignore)
                        ? hit.point.y
                        : p.y;
                    worst = Mathf.Min(worst, p.y - groundY);
                }
            }
            float lift = footClearance - worst;
            if (worst == float.MaxValue || lift < 0.03f) return 0f;
            anchorWorldPos.y += lift;
            return lift;
        }

        /// <summary>
        /// Deterministic step entrypoint used by Update and QA verification.
        /// </summary>
        public void StepSimulation(float dt)
        {
            if (dt < 0f) dt = 0f;
            animTimer += dt;

            float targetVis = EvaluateTargetVisibility();
            currentVisibility = dt > 0f
                ? Mathf.MoveTowards(currentVisibility, targetVis, dt * 1.4f)
                : targetVis;

            bool shouldShow = currentVisibility > 0.02f;
            SetVisualsActive(shouldShow);
            if (!shouldShow) return;

            float visScale = baseUniformScale * Mathf.SmoothStep(0.05f, 1f, Mathf.Clamp01(currentVisibility));
            transform.localScale = new Vector3(visScale, visScale, visScale);

            AnimationClip wanted = animTimer < talkUntil ? talkClip : SelectActiveClip();
            if (graphInitialized && wanted != graphClip) SetupPlayableGraph(wanted);

            if (graphInitialized && clipPlayable.IsValid())
            {
                float speed = subBehavior == AmbientNpcSubBehavior.KidChaser ? 1.25f : 1.0f;
                clipPlayable.SetTime(ComputeClipTime(speed));
            }

            ApplyAnchoredTransform(animTimer + phaseOffset);
        }

        /// <summary>Plays talkClip once (its full length), then the ambient clip resumes.</summary>
        public void PlayTalk()
        {
            if (talkClip == null) return;
            talkUntil = animTimer + talkClip.length;
        }

        private double ComputeClipTime(float speed)
        {
            if (animTimer < talkUntil) return activeClipLength - (talkUntil - animTimer);
            if (poseClip != null && subBehavior == AmbientNpcSubBehavior.KidJettyJumper)
            {
                // Clip plays once, in step with the procedural jump arc; holds its last frame.
                float cyc = (animTimer + phaseOffset) % JumperCycle;
                return Mathf.Clamp(cyc - JumperClipStart, 0f, activeClipLength - 1f / 30f);
            }
            return ((animTimer * speed) + phaseOffset) % activeClipLength;
        }

        private void Update()
        {
            if (!Application.isPlaying) return;
            StepSimulation(Time.deltaTime);
        }

        private void LateUpdate()
        {
            if (!Application.isPlaying || !visualsActive) return;
            ApplyBonePostureOffsets(forceApply: false);
        }

        private void CacheComponents()
        {
            if (cachedAnimator == null)
            {
                cachedAnimator = GetComponent<Animator>();
            }
            if (cachedAnimator != null)
            {
                cachedAnimator.cullingMode = AnimatorCullingMode.CullUpdateTransforms;
                cachedAnimator.applyRootMotion = false;
            }

            if (cachedRenderers == null || cachedRenderers.Length == 0)
            {
                cachedRenderers = GetComponentsInChildren<Renderer>(true);
            }
            if (propBlock == null)
            {
                propBlock = new MaterialPropertyBlock();
            }

            if (spineBone == null)
            {
                spineBone = transform.Find("VillagerRig/Hips/Spine");
                chestBone = transform.Find("VillagerRig/Hips/Spine/Chest");
                leftUpperLeg = transform.Find("VillagerRig/Hips/LeftUpperLeg");
                leftLowerLeg = transform.Find("VillagerRig/Hips/LeftUpperLeg/LeftLowerLeg");
                leftFoot = transform.Find("VillagerRig/Hips/LeftUpperLeg/LeftLowerLeg/LeftFoot");
                rightUpperLeg = transform.Find("VillagerRig/Hips/RightUpperLeg");
                rightLowerLeg = transform.Find("VillagerRig/Hips/RightUpperLeg/RightLowerLeg");
                rightFoot = transform.Find("VillagerRig/Hips/RightUpperLeg/RightLowerLeg/RightFoot");
                leftUpperArm = transform.Find("VillagerRig/Hips/Spine/Chest/LeftShoulder/LeftUpperArm");
                leftLowerArm = transform.Find("VillagerRig/Hips/Spine/Chest/LeftShoulder/LeftUpperArm/LeftLowerArm");
                rightUpperArm = transform.Find("VillagerRig/Hips/Spine/Chest/RightShoulder/RightUpperArm");
                rightLowerArm = transform.Find("VillagerRig/Hips/Spine/Chest/RightShoulder/RightUpperArm/RightLowerArm");
            }

            if (rodPivot != null)
            {
                if (!hasRodBaseRot)
                {
                    rodBaseLocalRot = rodPivot.localRotation;
                    hasRodBaseRot = true;
                }
                if (rodTip == null) rodTip = rodPivot.Find("Rod_Tip");
                if (rodLine == null) rodLine = rodPivot.Find("Rod_Line");
                if (rodBobber == null) rodBobber = rodPivot.Find("Rod_Bobber");
            }
        }

        // Body (skinned) and its accessory (under Head) get tint + palette; props stay untouched.
        private void ApplyClothingTint()
        {
            if (cachedRenderers == null || propBlock == null) return;
            Transform head = transform.Find(HeadPath);
            for (int i = 0; i < cachedRenderers.Length; i++)
            {
                Renderer r = cachedRenderers[i];
                if (r == null || !(r is SkinnedMeshRenderer || (head != null && r.transform.IsChildOf(head)))) continue;
                r.GetPropertyBlock(propBlock);
                propBlock.SetColor(BaseColorId, clothingTint);
                propBlock.SetColor(ColorId, clothingTint);
                if (paletteTexture != null) propBlock.SetTexture(BaseMapId, paletteTexture);
                r.SetPropertyBlock(propBlock);
            }
        }

        private AnimationClip SelectActiveClip()
        {
            if (poseClip != null) return poseClip;
            if (subBehavior == AmbientNpcSubBehavior.KidChaser && carryBinClip != null)
            {
                return carryBinClip;
            }
            if (idleClip != null) return idleClip;
            if (carryBinClip != null) return carryBinClip;
            return throwTrashClip;
        }

        private void SampleBasePoseForCleanStart()
        {
            AnimationClip clip = SelectActiveClip();
            if (clip != null)
            {
                float len = Mathf.Max(0.1f, clip.length);
                clip.SampleAnimation(gameObject, phaseOffset % len);
            }
            hasAppliedBonePose = false;
        }

        private void SetupPlayableGraph(AnimationClip clip)
        {
            DestroyPlayableGraph();
            graphClip = clip;
            if (cachedAnimator == null || clip == null) return;

            activeClipLength = Mathf.Max(0.1f, clip.length);
            playableGraph = PlayableGraph.Create("KALI_Npc_" + gameObject.GetInstanceID());
            playableGraph.SetTimeUpdateMode(DirectorUpdateMode.GameTime);

            AnimationPlayableOutput output = AnimationPlayableOutput.Create(playableGraph, "NpcAnim", cachedAnimator);
            clipPlayable = AnimationClipPlayable.Create(playableGraph, clip);
            clipPlayable.SetSpeed(0.0);
            clipPlayable.SetTime(phaseOffset % activeClipLength);

            output.SetSourcePlayable(clipPlayable);
            playableGraph.Play();
            graphInitialized = true;
        }

        private void DestroyPlayableGraph()
        {
            if (playableGraph.IsValid())
            {
                playableGraph.Destroy();
            }
            graphInitialized = false;
        }

        private float EvaluateTargetVisibility()
        {
            float dayVis = 1f;
            KaliDayNightCycle cycle = KaliDayNightCycle.Instance;
            if (cycle != null)
            {
                float h = cycle.CurrentHour;
                if (h < 5.5f || h >= 20.15f)
                {
                    dayVis = 0f;
                }
                else if (h < 6.25f)
                {
                    dayVis = Mathf.SmoothStep(0f, 1f, (h - 5.5f) / 0.75f);
                }
                else if (h > 19.5f)
                {
                    dayVis = 1f - Mathf.SmoothStep(0f, 1f, (h - 19.5f) / 0.65f);
                }
            }

            if (dayVis <= 0f) return 0f;

            RiverGameManager gm = RiverGameManager.Instance;
            if (gm != null && gm.isMonsoonStorm)
            {
                if (role == AmbientNpcRole.Kids || role == AmbientNpcRole.Washer)
                {
                    return 0f;
                }
            }

            return dayVis;
        }

        private void SetVisualsActive(bool active)
        {
            if (visualsActive == active) return;
            visualsActive = active;

            if (cachedRenderers != null)
            {
                for (int i = 0; i < cachedRenderers.Length; i++)
                {
                    if (cachedRenderers[i] != null) cachedRenderers[i].enabled = active;
                }
            }

            if (cachedAnimator != null)
            {
                cachedAnimator.enabled = active;
            }

            if (propRoot != null)
            {
                propRoot.gameObject.SetActive(active);
            }
        }

        private void ApplyAnchoredTransform(float t)
        {
            Vector3 pos = anchorWorldPos;
            Quaternion rot = anchorWorldRot;
            float castLift = 0f;

            switch (subBehavior)
            {
                case AmbientNpcSubBehavior.SeatedFisher:
                {
                    pos.y -= 0.42f;
                    float sway = Mathf.Sin(t * 1.15f) * 2.2f;
                    rot *= Quaternion.Euler(Mathf.Sin(t * 0.9f) * 1.5f, sway, 0f);
                    if (rodPivot != null && hasRodBaseRot)
                    {
                        float castCycle = ((t * 0.12f) + 0.35f) % 1f;
                        float castPitch = 0f;
                        if (castCycle > 0.88f)
                        {
                            castLift = Mathf.Sin(((castCycle - 0.88f) / 0.12f) * Mathf.PI);
                            castPitch = -castLift * 14f;
                        }
                        else
                        {
                            castPitch = Mathf.Sin(t * 1.8f) * 2.2f;
                        }
                        if (poseClip == null) rodPivot.localRotation = rodBaseLocalRot * Quaternion.Euler(castPitch, 0f, 0f);
                    }
                    break;
                }

                case AmbientNpcSubBehavior.StandingFisher:
                {
                    pos.y += Mathf.Sin(t * 1.6f) * 0.012f;
                    rot *= Quaternion.Euler(Mathf.Sin(t * 1.1f) * 1.8f, Mathf.Sin(t * 0.7f) * 3.5f, 0f);
                    if (rodPivot != null && hasRodBaseRot)
                    {
                        float castCycle = ((t * 0.11f) + 0.35f) % 1f;
                        float castPitch = 0f;
                        if (castCycle > 0.86f)
                        {
                            castLift = Mathf.Sin(((castCycle - 0.86f) / 0.14f) * Mathf.PI);
                            castPitch = -castLift * 16f;
                        }
                        else
                        {
                            castPitch = Mathf.Sin(t * 1.6f) * 2.4f;
                        }
                        if (poseClip == null) rodPivot.localRotation = rodBaseLocalRot * Quaternion.Euler(castPitch, 0f, 0f);
                    }
                    break;
                }

                case AmbientNpcSubBehavior.CrouchedWasher:
                {
                    pos.y -= 0.215f;
                    float scrub = Mathf.Sin(t * 4.4f);
                    pos.y += Mathf.Abs(scrub) * 0.012f;
                    rot *= Quaternion.Euler(4f + scrub * 3.0f, 0f, Mathf.Cos(t * 2.2f) * 2.0f);
                    break;
                }

                case AmbientNpcSubBehavior.KidWader:
                {
                    float splashHop = Mathf.Abs(Mathf.Sin(t * 3.2f)) * 0.11f;
                    float waterBaseY = GetSafeShallowFloorY(anchorWorldPos.y);
                    pos.y = waterBaseY + splashHop;
                    rot *= Quaternion.Euler(Mathf.Sin(t * 3.2f) * 5f, Mathf.Sin(t * 1.9f) * 16f, Mathf.Cos(t * 3.2f) * 5f);
                    break;
                }

                case AmbientNpcSubBehavior.KidChaser:
                {
                    float omega = 1.45f;
                    float angle = t * omega;
                    float arc = Mathf.Sin(angle);
                    float side = Mathf.Cos(angle);
                    Vector3 axis = chaseAxisWorld.sqrMagnitude > 0.001f ? chaseAxisWorld.normalized : Vector3.forward;
                    Vector3 perp = Vector3.Cross(Vector3.up, axis).normalized;
                    const float ovalHalfWidth = 0.18f;
                    Vector3 offset = axis * (arc * chaseRadius) + perp * (side * ovalHalfWidth);
                    float strideHop = Mathf.Abs(Mathf.Sin(t * 5.2f)) * 0.08f;
                    pos = anchorWorldPos + offset;
                    pos.y = GetSafeShallowFloorY(anchorWorldPos.y) + strideHop;

                    Vector3 moveDir = axis * (side * chaseRadius) - perp * (arc * ovalHalfWidth);
                    if (moveDir.sqrMagnitude > 0.0001f)
                    {
                        rot = Quaternion.LookRotation(moveDir.normalized, Vector3.up) * Quaternion.Euler(4f, 0f, Mathf.Sin(t * 5.2f) * 5f);
                    }
                    break;
                }

                case AmbientNpcSubBehavior.KidJettyJumper:
                {
                    float u = (t % JumperCycle) / JumperCycle;
                    float waterY = GetSafeShallowFloorY(jumpWaterPos.y);
                    Vector3 splashTarget = new Vector3(jumpWaterPos.x, waterY, jumpWaterPos.z);
                    Vector3 toWater = splashTarget - anchorWorldPos;
                    toWater.y = 0f;
                    Quaternion faceWaterRot = toWater.sqrMagnitude > 0.001f
                        ? Quaternion.LookRotation(toWater.normalized, Vector3.up)
                        : anchorWorldRot;
                    Quaternion faceJettyRot = toWater.sqrMagnitude > 0.001f
                        ? Quaternion.LookRotation(-toWater.normalized, Vector3.up)
                        : anchorWorldRot;

                    if (u < 0.36f)
                    {
                        float hop = Mathf.Abs(Mathf.Sin((u / 0.36f) * Mathf.PI * 3f)) * 0.08f;
                        pos = anchorWorldPos + new Vector3(0f, hop, 0f);
                        rot = faceWaterRot;
                    }
                    else if (u < 0.54f)
                    {
                        float j = (u - 0.36f) / 0.18f;
                        pos = Vector3.Lerp(anchorWorldPos, splashTarget, j);
                        pos.y += Mathf.Sin(j * Mathf.PI) * 0.85f;
                        rot = faceWaterRot * Quaternion.Euler(j * 16f, 0f, 0f);
                    }
                    else if (u < 0.80f)
                    {
                        float s = (u - 0.54f) / 0.26f;
                        pos = splashTarget + new Vector3(0f, Mathf.Abs(Mathf.Sin(s * Mathf.PI * 4f)) * 0.09f, 0f);
                        rot = faceWaterRot * Quaternion.Euler(0f, Mathf.Sin(s * Mathf.PI * 2f) * 28f, 0f);
                    }
                    else
                    {
                        float c = (u - 0.80f) / 0.20f;
                        pos = Vector3.Lerp(splashTarget, anchorWorldPos, Mathf.SmoothStep(0f, 1f, c));
                        pos.y += Mathf.Sin(c * Mathf.PI) * 0.45f;
                        rot = faceJettyRot;
                    }
                    break;
                }

                default:
                {
                    pos.y += Mathf.Sin(t * 1.4f) * 0.01f;
                    rot *= Quaternion.Euler(Mathf.Sin(t * 1.8f) * 1.8f, Mathf.Sin(t * 0.9f) * 7.5f, 0f);
                    break;
                }
            }

            transform.SetPositionAndRotation(pos, rot);

            if (subBehavior == AmbientNpcSubBehavior.SeatedFisher || subBehavior == AmbientNpcSubBehavior.StandingFisher)
            {
                UpdateFishingLineAndBobber(t, castLift);
            }
        }

        private void UpdateFishingLineAndBobber(float t, float castLift)
        {
            if (rodTip == null || rodLine == null || rodBobber == null) return;

            RiverGameManager gm = RiverGameManager.Instance;
            float waterY = gm != null ? gm.currentWaterLevelY : -0.17f;

            Vector3 tipWorld = rodTip.position;
            float restBobberY = Mathf.Clamp(waterY + Mathf.Sin(t * 2.3f) * 0.012f, -0.35f, tipWorld.y - 0.35f);
            float castBobberY = Mathf.Max(restBobberY, tipWorld.y - 0.65f);
            float bobberY = castLift > 0.001f ? Mathf.Lerp(restBobberY, castBobberY, castLift) : restBobberY;

            Vector3 bobberWorld = new Vector3(tipWorld.x, bobberY, tipWorld.z);
            float lineDist = Mathf.Max(0.25f, tipWorld.y - bobberWorld.y);
            float npcScale = Mathf.Max(0.25f, transform.localScale.y);

            rodLine.position = (tipWorld + bobberWorld) * 0.5f;
            rodLine.rotation = Quaternion.identity;
            rodLine.localScale = new Vector3(0.008f, (lineDist / npcScale) * 0.5f, 0.008f);

            rodBobber.position = bobberWorld;
            rodBobber.rotation = Quaternion.identity;
        }

        private float GetSafeShallowFloorY(float bakedFloorY)
        {
            RiverGameManager gm = RiverGameManager.Instance;
            if (gm == null) return bakedFloorY;
            float minWadingFloor = gm.currentWaterLevelY - 0.38f;
            return Mathf.Max(bakedFloorY, minWadingFloor);
        }

        private void ApplyBonePostureOffsets(bool forceApply)
        {
            // Role clip already holds the pose; offsets are fallback only when it is missing.
            if (poseClip != null) return;
            if (subBehavior == AmbientNpcSubBehavior.SeatedFisher)
            {
                ApplyBoneDelta(leftUpperLeg, SeatedUpperLegOffset, ref lastLeftUpperLegRot, forceApply);
                ApplyBoneDelta(rightUpperLeg, SeatedUpperLegOffset, ref lastRightUpperLegRot, forceApply);
                ApplyBoneDelta(leftLowerLeg, SeatedLowerLegOffset, ref lastLeftLowerLegRot, forceApply);
                ApplyBoneDelta(rightLowerLeg, SeatedLowerLegOffset, ref lastRightLowerLegRot, forceApply);
                hasAppliedBonePose = true;
            }
            else if (subBehavior == AmbientNpcSubBehavior.CrouchedWasher)
            {
                ApplyBoneDelta(leftUpperLeg, CrouchUpperLegOffset, ref lastLeftUpperLegRot, forceApply);
                ApplyBoneDelta(rightUpperLeg, CrouchUpperLegOffset, ref lastRightUpperLegRot, forceApply);
                ApplyBoneDelta(leftLowerLeg, CrouchLowerLegOffset, ref lastLeftLowerLegRot, forceApply);
                ApplyBoneDelta(rightLowerLeg, CrouchLowerLegOffset, ref lastRightLowerLegRot, forceApply);
                ApplyBoneDelta(leftFoot, CrouchFootOffset, ref lastLeftFootRot, forceApply);
                ApplyBoneDelta(rightFoot, CrouchFootOffset, ref lastRightFootRot, forceApply);
                ApplyBoneDelta(spineBone, CrouchSpineOffset, ref lastSpineRot, forceApply);
                ApplyBoneDelta(chestBone, CrouchChestOffset, ref lastChestRot, forceApply);

                float scrub = Mathf.Sin((animTimer + phaseOffset) * 4.4f);
                if (leftUpperArm != null) leftUpperArm.localRotation = LeftArmRestRot * Quaternion.Euler(0f, 0f, 38f + scrub * 8f);
                if (rightUpperArm != null) rightUpperArm.localRotation = RightArmRestRot * Quaternion.Euler(0f, 0f, -38f + scrub * 8f);
                if (leftLowerArm != null) leftLowerArm.localRotation = Quaternion.Euler(0f, 0f, 36f + scrub * 10f);
                if (rightLowerArm != null) rightLowerArm.localRotation = Quaternion.Euler(0f, 0f, -36f + scrub * 10f);
                hasAppliedBonePose = true;
            }
            else if (subBehavior == AmbientNpcSubBehavior.KidChaser)
            {
                float swing = Mathf.Sin((animTimer + phaseOffset) * 5.2f) * 26f;
                if (leftUpperArm != null) leftUpperArm.localRotation = LeftArmRestRot * Quaternion.Euler(0f, 0f, swing);
                if (rightUpperArm != null) rightUpperArm.localRotation = RightArmRestRot * Quaternion.Euler(0f, 0f, swing);
                if (leftLowerArm != null) leftLowerArm.localRotation = Quaternion.Euler(0f, 0f, 34f);
                if (rightLowerArm != null) rightLowerArm.localRotation = Quaternion.Euler(0f, 0f, -34f);
            }
            else if (subBehavior == AmbientNpcSubBehavior.ChatterBinCarrier)
            {
                if (leftUpperArm != null) leftUpperArm.localRotation = LeftArmRestRot * Quaternion.Euler(0f, 0f, 22f);
                if (rightUpperArm != null) rightUpperArm.localRotation = RightArmRestRot * Quaternion.Euler(0f, 0f, -22f);
                if (leftLowerArm != null) leftLowerArm.localRotation = Quaternion.Euler(0f, 0f, 54f);
                if (rightLowerArm != null) rightLowerArm.localRotation = Quaternion.Euler(0f, 0f, -54f);
            }
        }

        private void ApplyBoneDelta(Transform bone, Quaternion localOffset, ref Quaternion lastWritten, bool forceApply)
        {
            if (bone == null) return;
            if (!forceApply && hasAppliedBonePose && Mathf.Abs(Quaternion.Dot(bone.localRotation, lastWritten)) >= 0.9999f)
            {
                return;
            }
            Quaternion next = bone.localRotation * localOffset;
            bone.localRotation = next;
            lastWritten = next;
        }
    }
}
