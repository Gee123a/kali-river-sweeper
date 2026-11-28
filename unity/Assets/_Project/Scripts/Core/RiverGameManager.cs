using System;
using System.Collections.Generic;
using UnityEngine;

namespace KaliRiverSweeper.Core
{
    public enum UpgradeTier
    {
        Galah4m = 1,
        WoodenSampan = 2,
        TrashBoom = 3,
        AmphibiousExcavator = 4
    }

    // Spec I: Title -> Playing <-> Paused -> Ended. Gameplay Tick and player input run only in Playing.
    public enum KaliGameState
    {
        Title,
        Playing,
        Paused,
        Ended
    }

    public enum GameEnding
    {
        None,
        FloodFail,
        CompromisedOceanFlush,
        TrueSdgVictory,
        HealthFail,
        PartialSurvival
    }

    public readonly struct StationAuditReceipt
    {
        public readonly DiscardStationType Station;
        public readonly bool IsPass;
        public readonly string Summary;
        public readonly int RupiahDelta;
        public readonly int TrustDelta;

        public StationAuditReceipt(DiscardStationType station, bool isPass, string summary, int rupiahDelta, int trustDelta)
        {
            Station = station;
            IsPass = isPass;
            Summary = summary;
            RupiahDelta = rupiahDelta;
            TrustDelta = trustDelta;
        }
    }

    public readonly struct SdgScorecard
    {
        public readonly string Rank;
        public readonly bool Sdg63Pass;
        public readonly bool Sdg115Pass;
        public readonly bool Sdg141Pass;
        public readonly string Summary;

        public SdgScorecard(string rank, bool sdg63Pass, bool sdg115Pass, bool sdg141Pass, string summary)
        {
            Rank = rank;
            Sdg63Pass = sdg63Pass;
            Sdg115Pass = sdg115Pass;
            Sdg141Pass = sdg141Pass;
            Summary = summary;
        }
    }

    public class RiverGameManager : MonoBehaviour
    {
        public static RiverGameManager Instance { get; private set; }
        private static readonly int WaterClarityId = Shader.PropertyToID("_WaterClarity");

        [Header("Economy & 3-Class Cargo")]
        public int rupiah;
        public int cumulativeEarnings;
        public int cargoCount;
        public int normalCargo;
        public int medicalCargo;
        public int biohazardCargo;
        public int cargoCapacity = 8;
        public int totalScooped;
        public int recycledKg;
        public int flushedKg;
        public int medicalWasteSecured;
        public int biohazardWasteSecured;
        public int infectionIncidents;
        public int wrongDiscardCount;
        public int totalFinesPaid;
        public int unpaidFineDebt;
        public int pengepulHazardDumped;

        [Header("Player Health & Hazards")]
        public float playerHealth = 100f;
        public float maxPlayerHealth = 100f;
        public float medicalPrickDamage = 10f;
        public float biohazardGraceSeconds = 30f;
        public float biohazardExposureTimer;
        public bool isPlayerInBoat; // set by KaliPlayerController; a sealed boat hold pauses biohazard exposure

        [Header("Swim Stamina & Drowning")]
        public float swimStamina = 100f;
        public float maxSwimStamina = 100f;
        public float swimStaminaDrainPerSecond = 8f;
        public float swimSprintStaminaDrainPerSecond = 16f;
        public float swimTreadStaminaDrainPerSecond = 4f;
        public float swimStaminaRegenPerSecond = 18f;
        public float drowningDamagePerSecond = 14f;
        public bool isPlayerSwimming;
        public bool isPlayerMovingInWater;
        public bool isPlayerSprintingInWater;

        [Header("20-Tool Milestones (1..20)")]
        [Range(1, 20)] public int equippedToolIndex = 1;
        [Range(1, 20)] public int highestUnlockedToolIndex = 1;

        [Header("Linear River Water & Flood State")]
        public const float BaseWaterLevelY = -0.25f;
        // Spec D: water rises from blockage (barrier pile), barely from floating trash, plus storm rain.
        public const float WaterRisePerPiledUnit = 0.022f;
        public const float WaterRisePerFloatingUnit = 0.004f;
        public const float MaxRainRiseY = 0.55f;
        public const float RainDecayPerSecond = 0.05f;
        public float rainRiseY;
        public float bankOverflowWaterY = 1.40f;
        public float sellLockWaterY = 1.85f;
        public float fatalFloodWaterY = 2.45f;
        public int activeRiverTrashCount;
        public int piledRiverTrashCount = 4;
        public float currentWaterLevelY;
        [Range(0f, 1f)] public float waterClarity = 0.12f;
        [Range(0f, 1f)] public float floodPressure = 0.18f;
        [Range(0f, 1f)] public float gunungSampahHealth = 1f;
        [Range(0, 100)] public int communityTrust = 40;
        public bool isMonsoonStorm;

        [Header("Monsoon Countdown")]
        public float monsoonCountdownSeconds = 300f;
        public float monsoonStormTriggerRemaining = 120f;
        public float monsoonCountdownRemaining = 300f;

        [Header("Unlocks, Vessels & Choices")]
        public bool galahUnlocked;
        public bool sampanUnlocked;
        public bool trashBoomActive;
        public bool excavatorUnlocked;
        public bool kampungBinsInstalled;
        public GameEnding activeEnding = GameEnding.None;
        public string lastStatusMessage = "Kumpulkan sampah dari sungai & jual ke stasiun yang tepat.";
        public string LastEndingDiagnosis { get; private set; } = string.Empty;

        public int TotalTrashInRiver => Mathf.Max(0, activeRiverTrashCount) + Mathf.Max(0, piledRiverTrashCount);
        public bool IsBankOverflowing => currentWaterLevelY >= bankOverflowWaterY;
        public bool IsSellLocked => currentWaterLevelY >= sellLockWaterY;
        public bool IsBiohazardDotActive => biohazardCargo > 0 && !isPlayerInBoat && biohazardExposureTimer >= biohazardGraceSeconds;
        public float BiohazardGraceRemaining => biohazardCargo > 0 ? Mathf.Max(0f, biohazardGraceSeconds - biohazardExposureTimer) : biohazardGraceSeconds;
        public float SwimStaminaNormalized => maxSwimStamina > 0f ? Mathf.Clamp01(swimStamina / maxSwimStamina) : 0f;
        public bool IsSwimming => isPlayerSwimming;
        public bool IsDrowning => isPlayerSwimming && swimStamina <= 0f && activeEnding == GameEnding.None;
        public ToolDefinition EquippedTool => ToolCatalog.GetTool(equippedToolIndex);
        public int SiagaLevel => floodPressure >= 0.85f ? 1 : floodPressure >= 0.60f ? 2 : floodPressure >= 0.35f ? 3 : 4;
        public bool IsTrustAuditPenaltyActive => isTrustAuditPenaltyActive;
        public bool IsTrustTrustedBonusActive => communityTrust >= 70;

        // Backwards-compatible events for Niki's UI & VFX
        public event Action OnStateChanged;
        public event Action<bool> OnWeatherChanged;
        public event Action<Vector3> OnWaterSplash;
        public event Action<Vector3> OnGunungTierBreached;
        public event Action<GameEnding> OnEndingTriggered;

        // Extended events for 20-tool milestones & hazard/station feedback
        public event Action<ToolDefinition> OnToolUnlocked;
        public event Action<ToolDefinition> OnEquippedToolChanged;
        public event Action OnHotbarChanged;
        public event Action<string, bool> OnHazardOrAlert;
        public event Action<StationAuditReceipt> OnStationAuditReceipt;
        public event Action<GameEnding, string> OnEndingWithDiagnosisTriggered;
        public event Action<string> OnObjectiveChanged;
        public event Action<KaliGameState> OnGameStateChanged;

        public KaliGameState State { get; private set; } = KaliGameState.Title;

        // Spec E: household plastic dominates (Normal 80 / Medical 14 / Biohazard 6), river spawns and barrier piles alike.
        public const float NormalWasteShare = 0.80f;
        public const float MedicalWasteShare = 0.14f;
        public static WasteClass RollWasteClass(float r01) =>
            r01 < NormalWasteShare ? WasteClass.Normal : (r01 < NormalWasteShare + MedicalWasteShare ? WasteClass.Medical : WasteClass.Biohazard);

        // Spec E: after the grace, 1.5 HP/s + 0.5 per extra drum, capped at 4 HP/s.
        public static float BiohazardDotPerSecond(int drums) => Mathf.Min(4f, 1.5f + 0.5f * Mathf.Max(0, drums - 1));

        // Spec F: first-run objective chain. Each step completes on a real event; the storm overrides.
        public static readonly string[] ObjectiveSteps =
        {
            "Ambil sampah di sungai — klik kiri saat dekat (lihat tumpukan di depan)",
            "Bawa ke Bank Sampah — berdiri di depan loket, tekan [E]",
            "Sampah medis → Pos Medis, biohazard → Karantina (ikuti papan arah)",
            "Beli alat lebih baik di Kopdes [E] — pilih slot 1–4",
            "Badai datang! Bersihkan tumpukan di Pintu Air agar air turun"
        };
        // ponytail: one static filler between "tool bought" and the storm, until Pak RT quests take over.
        public const string ObjectiveBeforeStorm = "Terus bersihkan sungai — jaga air tetap rendah sebelum badai";
        public const float HazardObjectiveTimeoutSeconds = 90f;
        public string CurrentObjective { get; private set; } = ObjectiveSteps[0];
        private bool objPickup, objDeposit, objHazard, objTool;
        private float objHazardTimer;

        public const float BoomIntervalSeconds = 5f;
        public const int BoomPayoutRupiah = 1500;
        public const float StormWarningLeadSeconds = 30f;
        public const float StormSurgeStartInterval = 8f;
        public const float StormSurgeEndInterval = 3f;

        private float boomTimer;
        private float stormSurgeTimer;
        private bool stormWarned;
        private bool stateDirty;
        private float notifyThrottleTimer;
        private bool isTrustAuditPenaltyActive;
        private float nextEmergencyTriageTime;
        private bool lowSwimStaminaWarned;
        private float drowningAlertCooldown;
        private bool lastDamageWasDrowning;
        // Hotbar: 4 carried tools (tool index per slot, 0 = empty). equippedToolIndex follows activeSlot.
        public const int HotbarSize = 4;
        public readonly int[] hotbar = { 1, 0, 0, 0 };
        public int activeSlot;
        private const float NotifyIntervalSeconds = 0.10f; // ~10 Hz throttle for Update ticks
        private const int MaxVisualBarrierProps = 22;

        private void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
            monsoonCountdownRemaining = monsoonCountdownSeconds;
            RecalculateWaterMetrics();
            Shader.SetGlobalFloat(WaterClarityId, waterClarity);
            CaptureSeedPiles();
            ApplyStateEffects();
        }

        public void SetState(KaliGameState next)
        {
            if (State == next) return;
            State = next;
            ApplyStateEffects();
            OnGameStateChanged?.Invoke(next);
        }

        // Paused / Ended freeze time and free the cursor; Title keeps time running (fly-over) but Tick is gated.
        // The open Kopdes shop freezes time too (KaliPlayerController.OpenShop / CloseShop).
        private void ApplyStateEffects()
        {
            Time.timeScale = State == KaliGameState.Paused || State == KaliGameState.Ended ? 0f : 1f;
            if (!Application.isPlaying) return;
            bool free = State != KaliGameState.Playing;
            Cursor.lockState = free ? CursorLockMode.None : CursorLockMode.Locked;
            Cursor.visible = free;
        }

        public void StartRun()
        {
            if (State == KaliGameState.Title) SetState(KaliGameState.Playing);
        }

        public void TogglePause()
        {
            if (State == KaliGameState.Playing) SetState(KaliGameState.Paused);
            else if (State == KaliGameState.Paused) SetState(KaliGameState.Playing);
        }

        public void ReturnToTitle()
        {
            ResetRun();
            SetState(KaliGameState.Title);
            NotifyState();
        }

        private void OnDestroy()
        {
            if (Instance == this && Application.isPlaying) Time.timeScale = 1f;
        }

        private void Update()
        {
            Tick(Time.deltaTime);
        }

        private void Tick(float dt)
        {
            if (State != KaliGameState.Playing || activeEnding != GameEnding.None) return;

            // 1. Monsoon countdown & automatic storm trigger
            if (monsoonCountdownRemaining > 0f)
            {
                monsoonCountdownRemaining = Mathf.Max(0f, monsoonCountdownRemaining - dt);
                if (!stormWarned && !isMonsoonStorm && monsoonCountdownRemaining <= monsoonStormTriggerRemaining + StormWarningLeadSeconds)
                {
                    stormWarned = true;
                    RaiseAlert("Awan monsun mendekat! Badai dalam 30 detik — turunkan level air sekarang.", true);
                }
                if (monsoonCountdownRemaining <= monsoonStormTriggerRemaining && !isMonsoonStorm)
                {
                    SetWeather(true);
                }
                if (isMonsoonStorm)
                {
                    // Upstream surge: piled trash arrives faster as the storm goes on (8s -> 3s).
                    float progress = monsoonStormTriggerRemaining > 0f
                        ? Mathf.Clamp01(1f - monsoonCountdownRemaining / monsoonStormTriggerRemaining)
                        : 1f;
                    rainRiseY = MaxRainRiseY * progress;
                    RecalculateWaterMetrics();
                    stormSurgeTimer += dt;
                    if (stormSurgeTimer >= Mathf.Lerp(StormSurgeStartInterval, StormSurgeEndInterval, progress))
                    {
                        stormSurgeTimer = 0f;
                        piledRiverTrashCount++;
                        RecalculateWaterMetrics();
                    }
                }
                else if (rainRiseY > 0f)
                {
                    rainRiseY = Mathf.Max(0f, rainRiseY - RainDecayPerSecond * dt);
                    RecalculateWaterMetrics();
                }
                MarkStateDirty();

                if (objDeposit && !objHazard)
                {
                    objHazardTimer += dt;
                    if (objHazardTimer >= HazardObjectiveTimeoutSeconds) { objHazard = true; RefreshObjective(); }
                }

                if (monsoonCountdownRemaining <= 0f)
                {
                    if (gunungSampahHealth <= 0.01f)
                    {
                        RaiseAlert("Badai Monsun berhasil dilewati & Gunung Sampah bersih! Sungai & desa selamat.", false);
                        CompleteCleanBreach();
                    }
                    else
                    {
                        RaiseAlert("Badai Monsun terlewati, tetapi Gunung Sampah masih tersisa! Keruk Gunung untuk Kemenangan SDG Penuh.", false);
                        TriggerEnding(GameEnding.PartialSurvival);
                    }
                    return;
                }
            }

            // 2. Trash Boom passive income & water relief
            if (trashBoomActive)
            {
                boomTimer += dt;
                if (boomTimer >= BoomIntervalSeconds)
                {
                    boomTimer = 0f;
                    // Rupiah only: passive income must not count toward Kopdes tool milestones.
                    rupiah += BoomPayoutRupiah;
                    if (piledRiverTrashCount > 0) piledRiverTrashCount--;
                    RecalculateWaterMetrics();
                    MarkStateDirty();
                }
            }

            // 3. Biohazard cargo Damage Over Time (DoT) & passive safe recovery
            if (biohazardCargo > 0)
            {
                // ponytail: the sealed boat hold pauses both the grace timer and the DoT.
                if (!isPlayerInBoat)
                {
                    biohazardExposureTimer += dt;
                    if (biohazardExposureTimer >= biohazardGraceSeconds)
                    {
                        ApplyPlayerDamage(BiohazardDotPerSecond(biohazardCargo) * dt, notifyImmediate: false);
                        if (activeEnding != GameEnding.None) return;
                    }
                }
                MarkStateDirty();
            }
            else
            {
                if (biohazardExposureTimer > 0f)
                {
                    biohazardExposureTimer = Mathf.Max(0f, biohazardExposureTimer - 3f * dt);
                    MarkStateDirty();
                }
                if (!IsBankOverflowing && !isPlayerSwimming && !IsDrowning && playerHealth < maxPlayerHealth)
                {
                    playerHealth = Mathf.Min(maxPlayerHealth, playerHealth + 0.8f * dt);
                    MarkStateDirty();
                }
            }

            // 3b. Surface swimming stamina & drowning damage
            if (drowningAlertCooldown > 0f) drowningAlertCooldown = Mathf.Max(0f, drowningAlertCooldown - dt);
            if (isPlayerSwimming)
            {
                float drainRate = isPlayerSprintingInWater
                    ? swimSprintStaminaDrainPerSecond
                    : (isPlayerMovingInWater ? swimStaminaDrainPerSecond : swimTreadStaminaDrainPerSecond);
                if (swimStamina > 0f)
                {
                    swimStamina = Mathf.Max(0f, swimStamina - drainRate * dt);
                    if (!lowSwimStaminaWarned && SwimStaminaNormalized <= 0.25f && swimStamina > 0f)
                    {
                        lowSwimStaminaWarned = true;
                        RaiseAlert("Stamina renang menipis! Segera naik ke darat atau Dermaga.", true);
                    }
                    if (swimStamina <= 0f)
                    {
                        drowningAlertCooldown = 2.5f;
                        RaiseAlert("Stamina renang habis — TENGGELAM! Segera ke tepi sungai atau Dermaga!", true);
                    }
                    MarkStateDirty();
                }
                else
                {
                    if (drowningAlertCooldown <= 0f)
                    {
                        drowningAlertCooldown = 2.5f;
                        RaiseAlert("TENGGELAM! Naik ke darat/Dermaga sebelum kehabisan HP!", true);
                    }
                    ApplyDamageCore(drowningDamagePerSecond * dt, notifyImmediate: false, fromDrowning: true);
                    if (activeEnding != GameEnding.None) return;
                }
            }
            else if (swimStamina < maxSwimStamina)
            {
                swimStamina = Mathf.Min(maxSwimStamina, swimStamina + swimStaminaRegenPerSecond * dt);
                if (SwimStaminaNormalized >= 0.35f) lowSwimStaminaWarned = false;
                MarkStateDirty();
            }

            // 4. Fatal Flood drowning check
            if (currentWaterLevelY >= fatalFloodWaterY)
            {
                RaiseAlert("Tanggul jebol! Air melampaui batas fatal — desa tenggelam!", true);
                TriggerEnding(GameEnding.FloodFail);
                return;
            }

            // 5. Throttled state broadcast (~10 Hz)
            if (stateDirty)
            {
                notifyThrottleTimer += dt;
                if (notifyThrottleTimer >= NotifyIntervalSeconds)
                {
                    NotifyState();
                }
            }
        }

        public void RegisterActiveTrash(int units = 1)
        {
            activeRiverTrashCount += Mathf.Max(1, units);
            RecalculateWaterMetrics();
            MarkStateDirty();
        }

        public void UnregisterActiveTrash(int units = 1)
        {
            activeRiverTrashCount = Mathf.Max(0, activeRiverTrashCount - Mathf.Max(1, units));
            RecalculateWaterMetrics();
            MarkStateDirty();
        }

        public void AddPiledTrash(int units = 1)
        {
            piledRiverTrashCount += Mathf.Max(1, units);
            RecalculateWaterMetrics();
            MarkStateDirty();
        }

        public void RemovePiledTrash(int units = 1)
        {
            piledRiverTrashCount = Mathf.Max(0, piledRiverTrashCount - Mathf.Max(1, units));
            RecalculateWaterMetrics();
            MarkStateDirty();
        }

        public void ConvertActiveToPiled(int units = 1)
        {
            int u = Mathf.Max(1, units);
            activeRiverTrashCount = Mathf.Max(0, activeRiverTrashCount - u);
            piledRiverTrashCount += u;
            RecalculateWaterMetrics();
            MarkStateDirty();
        }

        public bool ShouldAbsorbVisualBarrierProp()
        {
            return piledRiverTrashCount >= MaxVisualBarrierProps;
        }

        public int TryScoopPiledBarrierTrash(int maxUnits)
        {
            if (activeEnding != GameEnding.None) return 0;
            if (EquippedTool.Role != ToolRole.Garuk)
            {
                RaiseRoleAlert(ToolRole.Garuk, "tumpukan Pintu Air");
                return 0;
            }
            int space = cargoCapacity - cargoCount;
            if (space <= 0 || piledRiverTrashCount <= 0) return 0;

            int take = Mathf.Min(maxUnits, Mathf.Min(space, piledRiverTrashCount));
            piledRiverTrashCount -= take;

            // Barrier piles are mixed Normal/Medical/Biohazard
            for (int i = 0; i < take; i++)
            {
                ApplyCargoGainAndMedicalCheck(RollWasteClass(UnityEngine.Random.value), 1);
            }

            RecalculateWaterMetrics();
            NotifyState();
            return take;
        }

        public bool TryAddCargo(int amount = 1)
        {
            return TryPickupWaste(WasteClass.Normal, amount);
        }

        public bool TryPickupWaste(WasteClass wasteClass, int amount = 1)
        {
            if (activeEnding != GameEnding.None) return false;
            if (!CanPickup(wasteClass))
            {
                RaiseRoleAlert(ToolCatalog.RoleFor(wasteClass), WasteNoun(wasteClass));
                return false;
            }
            if (cargoCount >= cargoCapacity)
            {
                RaiseAlert("Kargo penuh! Buang ke stasiun atau tekan [Q] di daratan tinggi.", true);
                return false;
            }

            int added = Mathf.Min(ClampScoopUnits(wasteClass, Mathf.Max(1, amount)), cargoCapacity - cargoCount);
            ApplyCargoGainAndMedicalCheck(wasteClass, added);
            RecalculateWaterMetrics();
            NotifyState();
            return true;
        }

        // Spec C2 pickup rules: Medical needs Capit, Biohazard needs Ganco, Normal works with any role.
        public bool CanPickup(WasteClass wasteClass) =>
            wasteClass == WasteClass.Normal || EquippedTool.Role == ToolCatalog.RoleFor(wasteClass);

        // Non-Serok roles take at most 1 Normal unit per scoop; Serok (and the specialist role on its own class) takes the bundle.
        public int ClampScoopUnits(WasteClass wasteClass, int units) =>
            wasteClass == WasteClass.Normal && EquippedTool.Role != ToolRole.Serok ? Mathf.Min(1, units) : units;

        public bool CanDredgeGunung => excavatorUnlocked || (EquippedTool.Role == ToolRole.Ganco && EquippedTool.GunungDamagePerSwing > 0f);

        public static string WasteNoun(WasteClass wc) => wc switch
        {
            WasteClass.Medical => "limbah medis",
            WasteClass.Biohazard => "drum biohazard",
            _ => "sampah"
        };

        /// <summary>Null when the equipped role fits; otherwise the hint naming the slot to switch to or buy.</summary>
        public string RoleBlockReason(ToolRole need, string what)
        {
            if (EquippedTool.Role == need) return null;
            int slot = (int)need;
            string role = ToolCatalog.RoleName(need);
            return hotbar[slot] > 0
                ? $"Ganti ke {role} [{slot + 1}] untuk {what}"
                : $"Butuh {role} (slot {slot + 1}) untuk {what} — beli di Kopdes";
        }

        private string lastRoleAlert;
        private float nextRoleAlertTime;

        // ponytail: the same blocked-pickup hint repeats at most every 2 s (scoop spam), a different one shows at once.
        private void RaiseRoleAlert(ToolRole need, string what)
        {
            string msg = RoleBlockReason(need, what);
            if (msg == null) return;
            float now = Time.realtimeSinceStartup;
            if (msg == lastRoleAlert && now < nextRoleAlertTime) return;
            lastRoleAlert = msg;
            nextRoleAlertTime = now + 2f;
            RaiseAlert(msg, true);
        }

        // Spec C2: prick risk applies only to Capit tools (per tier; #10 Capitan Ular = 0%).
        public float GetEffectiveMedicalPrickChance()
        {
            return EquippedTool.Role == ToolRole.Capit ? EquippedTool.MedicalPrickChance : 0f;
        }

        private void ApplyCargoGainAndMedicalCheck(WasteClass wasteClass, int added)
        {
            switch (wasteClass)
            {
                case WasteClass.Medical:
                    medicalCargo += added;
                    break;
                case WasteClass.Biohazard:
                    biohazardCargo += added;
                    break;
                default:
                    normalCargo += added;
                    break;
            }

            // Update cargo counts BEFORE firing alerts/damage so HUD never sees stale totals
            totalScooped += added;
            SyncCargoTotal();
            if (!objPickup) { objPickup = true; RefreshObjective(); }

            if (wasteClass == WasteClass.Medical)
            {
                float prickChance = GetEffectiveMedicalPrickChance();
                for (int i = 0; i < added; i++)
                {
                    if (prickChance > 0f && UnityEngine.Random.value < prickChance)
                    {
                        infectionIncidents++;
                        ApplyPlayerDamage(medicalPrickDamage, notifyImmediate: false);
                        RaiseAlert($"Tertusuk limbah medis! (-{medicalPrickDamage:0} HP) Gunakan #10 Capitan Ular!", true);
                    }
                }
            }
            else if (wasteClass == WasteClass.Biohazard)
            {
                RaiseAlert($"Biohazard Radioaktif di kargo ({biohazardCargo})! Bawa ke Karantina sebelum DoT!", true);
            }
        }

        public bool SecureMedicalWaste(bool usingSnakeGrabber)
        {
            if (usingSnakeGrabber)
            {
                medicalWasteSecured++;
                AddEarnings(15000);
                communityTrust = Mathf.Min(100, communityTrust + 12);
                NotifyState();
                return true;
            }
            infectionIncidents++;
            communityTrust = Mathf.Max(0, communityTrust - 15);
            ApplyPlayerDamage(medicalPrickDamage, notifyImmediate: true);
            return false;
        }

        public bool TryEmergencyPosMedisTriage()
        {
            if (activeEnding != GameEnding.None) return false;
            if (playerHealth >= maxPlayerHealth) return false;
            if (Time.unscaledTime < nextEmergencyTriageTime) return false;

            nextEmergencyTriageTime = Time.unscaledTime + 8f;
            playerHealth = Mathf.Min(maxPlayerHealth, playerHealth + 10f);
            RaiseAlert("Triase Darurat Pos Medis B3: +10 HP (Rp 0 saat Sell-Lock).", false);
            NotifyState();
            return true;
        }

        private static WasteClass GetLegalWasteClassForStation(DiscardStationType station) => station switch
        {
            DiscardStationType.PosMedisB3 => WasteClass.Medical,
            DiscardStationType.KarantinaBiohazard => WasteClass.Biohazard,
            _ => WasteClass.Normal
        };

        /// <summary>
        /// Safe [E] station interaction: deposits ONLY the legal matching waste class at Bank Sampah / Pos Medis / Karantina
        /// with zero accidental fines. At Gudang Pengepul, sells all held cargo.
        /// </summary>
        public int DiscardLegalAtStation(DiscardStationType station)
        {
            if (activeEnding != GameEnding.None) return 0;
            if (IsSellLocked)
            {
                if (station == DiscardStationType.PosMedisB3 && TryEmergencyPosMedisTriage())
                {
                    return 0;
                }
                RaiseAlert("SELL-LOCK! Stasiun terendam banjir. Tahan [Q] untuk buang kargo di daratan tinggi!", true);
                return 0;
            }

            if (station == DiscardStationType.GudangPengepul)
            {
                return SellAllAtPengepul();
            }

            WasteClass legalClass = GetLegalWasteClassForStation(station);
            int qty = GetCargoForClass(legalClass);
            if (qty <= 0)
            {
                if (station == DiscardStationType.PosMedisB3 && TryEmergencyPosMedisTriage())
                {
                    return 0;
                }

                string hint = BuildWrongStationHint(station);
                RaiseAlert(hint, cargoCount > 0);
                NotifyState();
                return 0;
            }

            return DiscardWasteAtStation(station, legalClass);
        }

        private string BuildWrongStationHint(DiscardStationType station)
        {
            if (cargoCount <= 0) return $"Kargo kosong. Serok sampah di sungai dulu untuk setor ke {StationName(station)}.";
            return GetDepositPreview(station).Replace("\n", " | ");
        }

        public static string StationName(DiscardStationType station) => station switch
        {
            DiscardStationType.BankSampah => "Bank Sampah",
            DiscardStationType.PosMedisB3 => "Pos Medis",
            DiscardStationType.KarantinaBiohazard => "Karantina",
            _ => "Gudang Pengepul"
        };

        private static string ClassName(WasteClass wc) => wc switch
        {
            WasteClass.Medical => "Medis",
            WasteClass.Biohazard => "Biohazard",
            _ => "Normal"
        };

        private static int StationRate(WasteClass wc) => wc switch
        {
            WasteClass.Medical => 9000,
            WasteClass.Biohazard => 14000,
            _ => 4000
        };

        private static string Rp(int amount) => "Rp " + amount.ToString("#,0", System.Globalization.CultureInfo.InvariantCulture).Replace(',', '.');

        /// <summary>
        /// Truthful [E] prompt: what this station takes from current cargo and for how much (line 1),
        /// and what has to go elsewhere (line 2, may be empty).
        /// </summary>
        public string GetDepositPreview(DiscardStationType station)
        {
            if (station == DiscardStationType.GudangPengepul)
            {
                if (cargoCount <= 0) return "Gudang Pengepul borong semua kelas (harga murah). Kargo kosong.";
                int pay = normalCargo * 2000 + medicalCargo * 3000 + biohazardCargo * 4500;
                int trustLoss = medicalCargo * 8 + biohazardCargo * 12;
                string line1 = $"Gudang Pengepul borong semua ×{cargoCount} → {Rp(pay)} (murah)";
                return trustLoss > 0 ? line1 + $"\nMedis/Biohazard ikut dijual: -{trustLoss} Trust" : line1;
            }

            WasteClass legal = GetLegalWasteClassForStation(station);
            int qty = GetCargoForClass(legal);
            UpdateTrustAuditState();
            float trustMult = communityTrust >= 70 ? 1.15f : (isTrustAuditPenaltyActive ? 0.75f : 1.0f);
            string head = $"{StationName(station)} menerima: {ClassName(legal)}";
            string first = qty > 0
                ? $"{head} ×{qty} → {Rp(Mathf.RoundToInt(qty * StationRate(legal) * trustMult))}"
                : $"{head} ({Rp(StationRate(legal))}/item) — tidak ada di kargo";

            string rest = string.Empty;
            foreach (WasteClass wc in new[] { WasteClass.Normal, WasteClass.Medical, WasteClass.Biohazard })
            {
                int q = GetCargoForClass(wc);
                if (wc == legal || q <= 0) continue;
                DiscardStationType target = wc == WasteClass.Medical ? DiscardStationType.PosMedisB3
                    : wc == WasteClass.Biohazard ? DiscardStationType.KarantinaBiohazard : DiscardStationType.BankSampah;
                rest += (rest.Length > 0 ? " · " : string.Empty) + $"{ClassName(wc)} ×{q} → bawa ke {StationName(target)}";
            }
            return rest.Length > 0 ? first + "\n" + rest : first;
        }

        /// <summary>
        /// Discards a single waste class at the target station.
        /// Proper station yields full Rupiah & trust; wrong station incurs a Rupiah fine & trust penalty.
        /// Blocked during Sell-Lock (except Pos Medis B3 emergency triage).
        /// </summary>
        public int DiscardWasteAtStation(DiscardStationType station, WasteClass wasteClass)
        {
            if (activeEnding != GameEnding.None) return 0;
            if (IsSellLocked)
            {
                if (station == DiscardStationType.PosMedisB3 && TryEmergencyPosMedisTriage())
                {
                    return 0;
                }
                RaiseAlert("SELL-LOCK! Stasiun terendam banjir. Tahan [Q] untuk buang kargo di daratan tinggi!", true);
                return 0;
            }

            if (station == DiscardStationType.GudangPengepul)
            {
                return DiscardSingleAtPengepul(wasteClass);
            }

            int qty = GetCargoForClass(wasteClass);
            if (qty <= 0) return 0;

            ClearCargoForClass(wasteClass);
            SyncCargoTotal();

            bool isMatch =
                (station == DiscardStationType.BankSampah && wasteClass == WasteClass.Normal) ||
                (station == DiscardStationType.PosMedisB3 && wasteClass == WasteClass.Medical) ||
                (station == DiscardStationType.KarantinaBiohazard && wasteClass == WasteClass.Biohazard);

            if (isMatch)
            {
                int basePayout = qty * StationRate(wasteClass);
                UpdateTrustAuditState();
                float trustMult = communityTrust >= 70 ? 1.15f : (isTrustAuditPenaltyActive ? 0.75f : 1.0f);
                int grossPayout = Mathf.RoundToInt(basePayout * trustMult);

                int debtPaid = 0;
                if (unpaidFineDebt > 0)
                {
                    debtPaid = Mathf.Min(unpaidFineDebt, grossPayout);
                    unpaidFineDebt -= debtPaid;
                    totalFinesPaid += debtPaid;
                }
                int netPayout = grossPayout - debtPaid;
                AddEarnings(netPayout);
                recycledKg += qty * 5;
                int trustGain = qty * 4;
                int prevTrust = communityTrust;
                communityTrust = Mathf.Min(100, communityTrust + trustGain);
                UpdateTrustAuditState();

                if (wasteClass == WasteClass.Medical)
                {
                    medicalWasteSecured += qty;
                    playerHealth = Mathf.Min(maxPlayerHealth, playerHealth + 10f);
                }
                else if (wasteClass == WasteClass.Biohazard)
                {
                    biohazardWasteSecured += qty;
                    biohazardExposureTimer = 0f;
                }
                objDeposit = true;
                if (wasteClass != WasteClass.Normal) objHazard = true;
                RefreshObjective();

                string modTag = debtPaid > 0 ? $" (potong utang denda Rp {debtPaid:N0})" :
                    (trustMult > 1.01f ? " (Bonus Terpercaya +15%)" : (trustMult < 0.99f ? " (Penalti Sidak DLH -25%)" : string.Empty));
                string msg = $"Setor {qty}x {wasteClass} bersih: +Rp {netPayout:N0}{modTag}";
                RaiseAlert(msg, false);
                OnStationAuditReceipt?.Invoke(new StationAuditReceipt(station, true, "LOLOS SORTIR", netPayout, communityTrust - prevTrust));
                NotifyState();
                return netPayout;
            }

            int finePerItem = wasteClass switch
            {
                WasteClass.Biohazard => 8000,
                WasteClass.Medical => 5000,
                _ => 2500
            };
            int fine = qty * finePerItem;
            int paidNow = Mathf.Min(rupiah, fine);
            int shortfall = fine - paidNow;
            rupiah -= paidNow;
            totalFinesPaid += paidNow;
            unpaidFineDebt += shortfall;
            wrongDiscardCount += qty;

            int extraDebtTrustLoss = shortfall > 0 ? Mathf.Max(2, shortfall / 5000 * 2) : 0;
            int trustLoss = qty * (wasteClass == WasteClass.Biohazard ? 12 : (wasteClass == WasteClass.Medical ? 8 : 4)) + extraDebtTrustLoss;
            int oldTrust = communityTrust;
            communityTrust = Mathf.Max(0, communityTrust - trustLoss);
            UpdateTrustAuditState();

            if (wasteClass == WasteClass.Biohazard) biohazardExposureTimer = 0f;

            string debtNote = shortfall > 0 ? $" | Utang Denda +Rp {shortfall:N0}" : string.Empty;
            RaiseAlert($"SALAH STASIUN ({wasteClass} -> {station})! Denda Rp {fine:N0}{debtNote} (-{trustLoss} Trust)", true);
            OnStationAuditReceipt?.Invoke(new StationAuditReceipt(station, false, "PELANGGARAN B3", -paidNow, communityTrust - oldTrust));
            NotifyState();
            return -fine;
        }

        /// <summary>
        /// Discards all held waste classes at a station in one action.
        /// At Gudang Pengepul, sells everything cheaply with Trust/SDG penalties for hazardous waste.
        /// </summary>
        public int DiscardAllAtStation(DiscardStationType station)
        {
            if (activeEnding != GameEnding.None) return 0;
            if (IsSellLocked)
            {
                RaiseAlert("SELL-LOCK! Stasiun terendam banjir. Tekan [Q] untuk buang kargo di daratan tinggi!", true);
                return 0;
            }
            if (cargoCount <= 0) return 0;

            if (station == DiscardStationType.GudangPengepul)
            {
                return SellAllAtPengepul();
            }

            int net = 0;
            if (normalCargo > 0) net += DiscardWasteAtStation(station, WasteClass.Normal);
            if (medicalCargo > 0) net += DiscardWasteAtStation(station, WasteClass.Medical);
            if (biohazardCargo > 0) net += DiscardWasteAtStation(station, WasteClass.Biohazard);
            return net;
        }

        private int DiscardSingleAtPengepul(WasteClass wasteClass)
        {
            int qty = GetCargoForClass(wasteClass);
            if (qty <= 0) return 0;

            int rate = wasteClass == WasteClass.Biohazard ? 4500 : (wasteClass == WasteClass.Medical ? 3000 : 2000);
            int payout = qty * rate;
            ClearCargoForClass(wasteClass);
            SyncCargoTotal();
            AddEarnings(payout);

            if (wasteClass != WasteClass.Normal)
            {
                int trustPenalty = qty * (wasteClass == WasteClass.Biohazard ? 12 : 8);
                pengepulHazardDumped += qty;
                int prevTrust = communityTrust;
                communityTrust = Mathf.Max(0, communityTrust - trustPenalty);
                UpdateTrustAuditState();
                if (wasteClass == WasteClass.Biohazard) biohazardExposureTimer = 0f;
                RaiseAlert($"Jual {qty}x {wasteClass} ke Pengepul: +Rp {payout:N0} (Penalti -{trustPenalty} Trust!)", true);
                OnStationAuditReceipt?.Invoke(new StationAuditReceipt(DiscardStationType.GudangPengepul, false, "PELANGGARAN B3", payout, communityTrust - prevTrust));
            }
            else
            {
                RaiseAlert($"Jual {qty}x Normal ke Pengepul: +Rp {payout:N0}", false);
                OnStationAuditReceipt?.Invoke(new StationAuditReceipt(DiscardStationType.GudangPengepul, true, "LOLOS SORTIR", payout, 0));
            }

            NotifyState();
            return payout;
        }

        public int SellAllAtPengepul()
        {
            if (activeEnding != GameEnding.None) return 0;
            if (IsSellLocked)
            {
                RaiseAlert("SELL-LOCK! Stasiun terendam banjir. Tahan [Q] untuk buang kargo di daratan tinggi!", true);
                return 0;
            }
            if (cargoCount <= 0) return 0;

            int payout = normalCargo * 2000 + medicalCargo * 3000 + biohazardCargo * 4500;
            int hazardQty = medicalCargo + biohazardCargo;
            int trustPenalty = medicalCargo * 8 + biohazardCargo * 12;

            normalCargo = 0;
            medicalCargo = 0;
            biohazardCargo = 0;
            biohazardExposureTimer = 0f;
            SyncCargoTotal();

            AddEarnings(payout);
            if (hazardQty > 0)
            {
                pengepulHazardDumped += hazardQty;
                int prevTrust = communityTrust;
                communityTrust = Mathf.Max(0, communityTrust - trustPenalty);
                UpdateTrustAuditState();
                RaiseAlert($"Pengepul borong semua: +Rp {payout:N0} (Penalti -{trustPenalty} Trust karena limbah B3/Biohazard!)", true);
                OnStationAuditReceipt?.Invoke(new StationAuditReceipt(DiscardStationType.GudangPengepul, false, "PELANGGARAN B3", payout, communityTrust - prevTrust));
            }
            else
            {
                RaiseAlert($"Pengepul borong semua: +Rp {payout:N0} (Harga murah)", false);
                OnStationAuditReceipt?.Invoke(new StationAuditReceipt(DiscardStationType.GudangPengepul, true, "LOLOS SORTIR", payout, 0));
            }

            NotifyState();
            return payout;
        }

        /// <summary>
        /// Anti-deadlock high-ground cargo dump (Q key). Clears cargo with zero Rupiah when hubs are Sell-Locked.
        /// </summary>
        public int DumpCargoOnHighGround()
        {
            if (activeEnding != GameEnding.None || cargoCount <= 0) return 0;

            int dropped = cargoCount;
            int hazardQty = medicalCargo + biohazardCargo;

            normalCargo = 0;
            medicalCargo = 0;
            biohazardCargo = 0;
            biohazardExposureTimer = 0f;
            SyncCargoTotal();

            // Dumping on high ground during Sell-Lock is an emergency anti-deadlock action (0 penalty).
            if (!IsSellLocked && hazardQty > 0)
            {
                communityTrust = Mathf.Max(0, communityTrust - hazardQty * 2);
            }

            RaiseAlert($"Dumped {dropped} cargo safely on high ground (Rp 0).", false);
            NotifyState();
            return dropped;
        }

        // Backwards-compatible legacy Choice A wrappers
        public int DumpAtBurnPit() => SellAllAtPengepul();

        public int SellAtBankSampah()
        {
            return DiscardAllAtStation(DiscardStationType.BankSampah);
        }

        public const int KampungBinsCost = 30000;

        public static int GetUpgradeCost(UpgradeTier tier)
        {
            return tier switch
            {
                UpgradeTier.Galah4m => 20000,
                UpgradeTier.WoodenSampan => 40000,
                UpgradeTier.TrashBoom => 75000,
                UpgradeTier.AmphibiousExcavator => 120000,
                _ => 999999
            };
        }

        public bool IsToolUnlocked(int index) =>
            index >= 1 && index <= 20 && cumulativeEarnings >= ToolCatalog.GetTool(index).UnlockRupiah;

        public bool IsToolOwned(int index) => FindHotbarSlot(index) >= 0;

        public int FindHotbarSlot(int toolIndex)
        {
            if (toolIndex < 1) return -1;
            for (int i = 0; i < HotbarSize; i++) if (hotbar[i] == toolIndex) return i;
            return -1;
        }

        public static int RoleSlot(int toolIndex) => (int)ToolCatalog.GetTool(toolIndex).Role;

        // Spec C2 auto trade-in: the tool already in the new tool's role slot is returned for 50% of its catalog price.
        public const float ToolTradeInCredit = 0.5f;

        public int GetTradeInCredit(int toolIndex)
        {
            int held = hotbar[RoleSlot(toolIndex)];
            return held > 0 && held != toolIndex ? GetCreditFor(held) : 0;
        }

        // Net price the player actually pays (catalog price minus the role slot's trade-in); negative = paid back.
        public int GetToolPrice(int toolIndex) => ToolCatalog.GetTool(toolIndex).UnlockRupiah - GetTradeInCredit(toolIndex);

        /// <summary>Buys into the tool's role slot; an occupied slot is traded in automatically for 50% credit.</summary>
        public bool BuyTool(int toolIndex)
        {
            if (toolIndex < 1 || toolIndex > 20 || IsToolOwned(toolIndex)) return false;

            ToolDefinition tool = ToolCatalog.GetTool(toolIndex);
            if (!IsToolUnlocked(toolIndex))
            {
                RaiseAlert($"#{tool.Index:00} {tool.DisplayName} belum terbuka — kumpulkan Rp {tool.UnlockRupiah - cumulativeEarnings:N0} lagi dari sungai.", true);
                return false;
            }

            int slot = (int)tool.Role;
            int cost = GetToolPrice(toolIndex);
            if (rupiah < cost)
            {
                RaiseAlert($"Rupiah kurang untuk #{tool.Index:00} {tool.DisplayName}: butuh Rp {cost:N0} (punya Rp {rupiah:N0}).", true);
                return false;
            }

            int oldTool = hotbar[slot];
            rupiah -= cost;
            hotbar[slot] = toolIndex;
            if (tool.Tier >= 1) galahUnlocked = true;

            activeSlot = slot;
            equippedToolIndex = toolIndex;
            objTool = true;
            RefreshObjective();
            OnHotbarChanged?.Invoke();
            OnEquippedToolChanged?.Invoke(EquippedTool);
            string tradeNote = oldTool > 0 ? $" (tukar #{oldTool:00}, kredit Rp {GetCreditFor(oldTool):N0})" : string.Empty;
            RaiseAlert($"Alat #{tool.Index:00} {tool.DisplayName} dibeli & dipakai di slot {slot + 1} {ToolCatalog.RoleName(tool.Role)}!{tradeNote}", false);
            NotifyState();
            return true;
        }

        private static int GetCreditFor(int toolIndex) => Mathf.RoundToInt(ToolCatalog.GetTool(toolIndex).UnlockRupiah * ToolTradeInCredit);

        public bool IsUpgradeOwned(UpgradeTier tier) => tier switch
        {
            UpgradeTier.Galah4m => galahUnlocked,
            UpgradeTier.WoodenSampan => sampanUnlocked,
            UpgradeTier.TrashBoom => trashBoomActive,
            UpgradeTier.AmphibiousExcavator => excavatorUnlocked,
            _ => false
        };

        public bool BuyKampungBins()
        {
            if (kampungBinsInstalled || rupiah < KampungBinsCost) return false;
            rupiah -= KampungBinsCost;
            kampungBinsInstalled = true;
            communityTrust = Mathf.Min(100, communityTrust + 25);
            UpdateTrustAuditState();
            RaiseAlert("Tempat Sampah Kampung terpasang! Sampah desa turun 60%.", false);
            NotifyState();
            return true;
        }

        public bool BuyUpgrade(UpgradeTier tier)
        {
            if (IsUpgradeOwned(tier)) return false;
            int cost = GetUpgradeCost(tier);
            if (rupiah < cost) return false;
            rupiah -= cost;
            ApplyTier(tier);
            NotifyState();
            return true;
        }

        private void UpdateTrustAuditState()
        {
            if (communityTrust < 25) isTrustAuditPenaltyActive = true;
            else if (communityTrust >= 30) isTrustAuditPenaltyActive = false;
        }

        public bool SelectTool(int toolIndex)
        {
            int slot = FindHotbarSlot(toolIndex);
            return slot >= 0 && SelectSlot(slot);
        }

        public bool SelectSlot(int slot)
        {
            if (slot < 0 || slot >= HotbarSize) return false;
            if (hotbar[slot] == 0)
            {
                RaiseAlert($"Slot {slot + 1} {ToolCatalog.RoleName((ToolRole)slot)} kosong — beli di Kopdes.", false);
                return false;
            }
            if (slot == activeSlot && hotbar[slot] == equippedToolIndex) return false;
            activeSlot = slot;
            equippedToolIndex = hotbar[slot];
            OnHotbarChanged?.Invoke();
            OnEquippedToolChanged?.Invoke(EquippedTool);
            NotifyState();
            return true;
        }

        // Cycles non-empty hotbar slots.
        public void CycleTool(int delta)
        {
            int step = delta >= 0 ? 1 : -1;
            int slot = activeSlot;
            for (int i = 0; i < HotbarSize; i++)
            {
                slot = (slot + step + HotbarSize) % HotbarSize;
                if (hotbar[slot] != 0)
                {
                    SelectSlot(slot);
                    return;
                }
            }
        }

        public void NotifyWaterSplash(Vector3 worldPos)
        {
            OnWaterSplash?.Invoke(worldPos);
        }

        public void DamageGunungSampah(float amount, Vector3? impactPos = null)
        {
            if (!CanDredgeGunung || gunungSampahHealth <= 0f || activeEnding != GameEnding.None) return;

            int prevTier = Mathf.CeilToInt(gunungSampahHealth * 4f);

            GunungNodeController[] nodes = FindObjectsOfType<GunungNodeController>(true);
            if (nodes != null && nodes.Length > 0)
            {
                float sum = 0f;
                for (int i = 0; i < nodes.Length; i++) sum += Mathf.Clamp01(nodes[i].nodeHealth);
                gunungSampahHealth = Mathf.Clamp01(sum / nodes.Length);
            }
            else
            {
                gunungSampahHealth = Mathf.Clamp01(gunungSampahHealth - amount);
            }

            int nextTier = Mathf.CeilToInt(gunungSampahHealth * 4f);
            if (nextTier < prevTier)
            {
                Vector3 breachPos = impactPos.HasValue ? impactPos.Value : (nodes != null && nodes.Length > 0 ? nodes[0].transform.position : new Vector3(0f, currentWaterLevelY, 0f));
                OnGunungTierBreached?.Invoke(breachPos);
            }

            RecalculateWaterMetrics();
            if (gunungSampahHealth <= 0.01f) CompleteCleanBreach();
            else NotifyState();
        }

        public void NotifyCannotDredgeGunung()
        {
            RaiseAlert("Butuh GANCO #13 Ganco Ganda Winch+ (slot 3) atau Pindad Excavator untuk mengeruk Gunung Sampah!", true);
            NotifyState();
        }

        public void NotifyInfo(string msg, bool isDanger = false)
        {
            RaiseAlert(msg, isDanger);
            NotifyState();
        }

        public bool TriggerEmergencyFlush(bool confirmed = false)
        {
            if (activeEnding != GameEnding.None) return false;
            if (!IsSellLocked)
            {
                RaiseAlert("Emergency Flush hanya aktif saat banjir mencapai Sell-Lock (>= +1.85m).", true);
                NotifyState();
                return false;
            }
            if (!confirmed)
            {
                RaiseAlert("Tahan [Shift + X] selama 1.5 detik untuk konfirmasi Emergency Flush ke laut!", true);
                NotifyState();
                return false;
            }

            flushedKg += Mathf.RoundToInt(gunungSampahHealth * 1200f) + TotalTrashInRiver * 5;
            gunungSampahHealth = 0f;
            activeRiverTrashCount = 0;
            piledRiverTrashCount = 0;
            rainRiseY = 0f;
            RecalculateWaterMetrics();
            TriggerEnding(GameEnding.CompromisedOceanFlush);
            return true;
        }

        public void CompleteCleanBreach()
        {
            if (activeEnding != GameEnding.None) return;
            gunungSampahHealth = 0f;
            activeRiverTrashCount = 0;
            piledRiverTrashCount = 0;
            rainRiseY = 0f;
            waterClarity = 1f;
            floodPressure = 0.05f;
            currentWaterLevelY = BaseWaterLevelY;
            foreach (GunungNodeController node in FindObjectsOfType<GunungNodeController>(true))
            {
                node.ApplyDamage(1f);
            }
            TriggerEnding(GameEnding.TrueSdgVictory);
        }

        public void SetWeather(bool monsoon)
        {
            if (isMonsoonStorm == monsoon) return;
            isMonsoonStorm = monsoon;
            OnWeatherChanged?.Invoke(isMonsoonStorm);
            RefreshObjective();
            NotifyState();
        }

        private void RefreshObjective()
        {
            string next = isMonsoonStorm ? ObjectiveSteps[4]
                : !objPickup ? ObjectiveSteps[0]
                : !objDeposit ? ObjectiveSteps[1]
                : !objHazard ? ObjectiveSteps[2]
                : !objTool ? ObjectiveSteps[3]
                : ObjectiveBeforeStorm;
            if (next == CurrentObjective) return;
            CurrentObjective = next;
            OnObjectiveChanged?.Invoke(next);
        }

        public void UnlockSandboxDemo()
        {
            AddEarnings(Mathf.Max(0, 360000 - cumulativeEarnings));
            rupiah = Mathf.Max(rupiah, 250000);
            ApplyTier(UpgradeTier.Galah4m);
            ApplyTier(UpgradeTier.WoodenSampan);
            ApplyTier(UpgradeTier.TrashBoom);
            ApplyTier(UpgradeTier.AmphibiousExcavator);
            NotifyState();
        }

        private void AddEarnings(int amount)
        {
            if (amount <= 0) return;
            int prevCumulative = cumulativeEarnings;
            rupiah += amount;
            cumulativeEarnings += amount;
            CheckToolMilestones(prevCumulative);
        }

        // Role ladders are not index-sorted, so announce every tool whose price was crossed by this payout.
        private void CheckToolMilestones(int prevCumulative)
        {
            highestUnlockedToolIndex = ToolCatalog.GetHighestUnlockedIndex(cumulativeEarnings);
            if (IsToolUnlocked(6)) galahUnlocked = true;

            foreach (ToolDefinition tool in ToolCatalog.AllTools)
            {
                if (tool.UnlockRupiah <= prevCumulative || tool.UnlockRupiah > cumulativeEarnings) continue;
                OnToolUnlocked?.Invoke(tool);
                RaiseAlert($"Alat Baru di Kopdes: #{tool.Index:00} {tool.DisplayName} ({ToolCatalog.RoleName(tool.Role)}, slot {(int)tool.Role + 1})!", false);
            }
        }

        public void SetPlayerSwimming(bool swimming, bool movingInWater = false, bool sprintingInWater = false)
        {
            bool changed = isPlayerSwimming != swimming;
            isPlayerSwimming = swimming;
            isPlayerMovingInWater = swimming && movingInWater;
            isPlayerSprintingInWater = swimming && movingInWater && sprintingInWater;
            if (!swimming) drowningAlertCooldown = 0f;
            if (changed) NotifyState();
        }

        private void ApplyPlayerDamage(float amount, bool notifyImmediate)
        {
            ApplyDamageCore(amount, notifyImmediate, fromDrowning: false);
        }

        private void ApplyDamageCore(float amount, bool notifyImmediate, bool fromDrowning)
        {
            if (amount <= 0f || activeEnding != GameEnding.None) return;
            lastDamageWasDrowning = fromDrowning;
            playerHealth = Mathf.Max(0f, playerHealth - amount);
            if (playerHealth <= 0f)
            {
                RaiseAlert(
                    fromDrowning
                        ? "HP habis! Kamu tenggelam karena kehabisan stamina renang."
                        : "HP habis! Paparan limbah B3/infeksi berakibat fatal.",
                    true);
                TriggerEnding(GameEnding.HealthFail);
                return;
            }
            if (notifyImmediate) NotifyState();
            else MarkStateDirty();
        }

        private void RecalculateWaterMetrics()
        {
            int totalTrash = TotalTrashInRiver;
            currentWaterLevelY = BaseWaterLevelY
                + Mathf.Max(0, piledRiverTrashCount) * WaterRisePerPiledUnit
                + Mathf.Max(0, activeRiverTrashCount) * WaterRisePerFloatingUnit
                + rainRiseY;
            floodPressure = Mathf.Clamp01(Mathf.Max(0f, currentWaterLevelY) / fatalFloodWaterY);

            float trashClarity = Mathf.Clamp01(1f - (totalTrash / 95f));
            float gunungClarity = 1f - gunungSampahHealth;
            waterClarity = Mathf.Clamp(0.08f + trashClarity * 0.42f + gunungClarity * 0.50f, 0.05f, 1f);
        }

        private int GetCargoForClass(WasteClass wc) => wc switch
        {
            WasteClass.Medical => medicalCargo,
            WasteClass.Biohazard => biohazardCargo,
            _ => normalCargo
        };

        private void ClearCargoForClass(WasteClass wc)
        {
            switch (wc)
            {
                case WasteClass.Medical: medicalCargo = 0; break;
                case WasteClass.Biohazard: biohazardCargo = 0; break;
                default: normalCargo = 0; break;
            }
        }

        private void SyncCargoTotal()
        {
            cargoCount = normalCargo + medicalCargo + biohazardCargo;
        }

        private void ApplyTier(UpgradeTier tier)
        {
            switch (tier)
            {
                case UpgradeTier.Galah4m: galahUnlocked = true; break;
                case UpgradeTier.WoodenSampan: sampanUnlocked = true; cargoCapacity = Mathf.Max(cargoCapacity, 22); break;
                case UpgradeTier.TrashBoom: trashBoomActive = true; break;
                case UpgradeTier.AmphibiousExcavator: excavatorUnlocked = true; cargoCapacity = 60; break;
            }
        }

        private string BuildEndingDiagnosis(GameEnding ending) => ending switch
        {
            GameEnding.TrueSdgVictory => "Semua target SDG tercapai: Gunung Sampah berhasil dikeruk bersih tanpa membuang limbah ke laut. Pertahankan pemilahan di 3 stasiun!",
            GameEnding.PartialSurvival => "Badai Monsun berhasil dilewati, tetapi Gunung Sampah masih tersisa. Buka Pindad Excavator (Rp 120rb) atau alat #13+ untuk mengeruk Gunung Sampah hingga 0%!",
            GameEnding.CompromisedOceanFlush => "Pintu Air dibuka paksa saat krisis: desa selamat dari banjir, tetapi ribuan kg sampah mengalir ke laut. Turunkan level air lebih awal dengan Trash Boom & setoran rutin!",
            GameEnding.FloodFail => "Tinggi air sungai melampaui +2.45m karena penumpukan sampah. Pasang Trash Boom / Kampung Bins dan tahan [Q] saat Sell-Lock!",
            GameEnding.HealthFail => lastDamageWasDrowning
                ? "HP habis karena tenggelam setelah kehabisan stamina renang! Naik ke Dermaga, daratan, atau gunakan perahu untuk beristirahat."
                : "HP habis akibat tusukan limbah medis atau paparan Biohazard >30 detik. Beli CAPIT #10 Capitan Ular (Rp 55rb) & segera setor ke Pos Medis B3 / Karantina!",
            _ => string.Empty
        };

        public SdgScorecard ComputeSdgScorecard()
        {
            bool sdg63 = waterClarity >= 0.55f && wrongDiscardCount <= 2 && pengepulHazardDumped == 0;
            bool sdg115 = activeEnding != GameEnding.FloodFail && activeEnding != GameEnding.HealthFail && communityTrust >= 40;
            bool sdg141 = activeEnding != GameEnding.CompromisedOceanFlush && flushedKg == 0 && gunungSampahHealth <= 0.01f;

            int score = 0;
            if (sdg63) score += 35;
            else if (waterClarity >= 0.35f) score += 15;
            if (sdg115) score += 30;
            else if (activeEnding != GameEnding.FloodFail) score += 10;
            if (sdg141) score += 35;
            else if (flushedKg == 0) score += 15;

            if (activeEnding == GameEnding.FloodFail || activeEnding == GameEnding.HealthFail) score = Mathf.Min(score, 35);
            if (activeEnding == GameEnding.CompromisedOceanFlush) score = Mathf.Min(score, 55);

            string rank = score >= 90 ? "S" : score >= 75 ? "A" : score >= 55 ? "B" : score >= 40 ? "C" : "F";
            string summary = $"Rank {rank} | SDG 6.3: {(sdg63 ? "PASS" : "FAIL")} | SDG 11.5: {(sdg115 ? "PASS" : "FAIL")} | SDG 14.1: {(sdg141 ? "PASS" : "FAIL")}";
            return new SdgScorecard(rank, sdg63, sdg115, sdg141, summary);
        }

        private void TriggerEnding(GameEnding ending)
        {
            activeEnding = ending;
            LastEndingDiagnosis = BuildEndingDiagnosis(ending);
            SetState(KaliGameState.Ended);
            NotifyState();
            OnEndingTriggered?.Invoke(ending);
            OnEndingWithDiagnosisTriggered?.Invoke(ending, LastEndingDiagnosis);
        }

        public void RestartRun()
        {
            ResetRun();
            SetState(KaliGameState.Playing);
            RaiseAlert("Permainan diulang! Kumpulkan sampah dari sungai & setor ke stasiun yang tepat.", false);
            NotifyState();
        }

        private void ResetRun()
        {
            CaptureSeedPiles(); // edit-mode / late managers capture before ResetStageState destroys the baked piles
            ResetStageState(targetCumulativeRupiah: 0, targetRupiah: 0, targetToolIdx: 1,
                galah: false, sampan: false, boom: false, bins: false, excavator: false, monsoon: false);
            piledRiverTrashCount = 4;
            monsoonCountdownRemaining = monsoonCountdownSeconds;
            RestoreAllGunungNodes();
            gunungSampahHealth = 1f;
            RecalculateWaterMetrics();

            RiverTrashSpawner spawner = FindObjectOfType<RiverTrashSpawner>();
            if (spawner != null) spawner.ResetSpawnerState();

            ReseedPiles(spawner);

            KaliRiverSweeper.Player.KaliPlayerController player = FindObjectOfType<KaliRiverSweeper.Player.KaliPlayerController>();
            if (player != null) player.ResetToInitialSpawn();
        }

        // Baked map trash_pile items (snagged: buoyancy without drift) are destroyed by a restart, so remember where they were.
        // ponytail: re-seed spot + class through the spawner (prefab may differ from the bake), not a full prefab snapshot.
        private List<(Vector3 pos, WasteClass wc)> seedPiles;

        private void CaptureSeedPiles()
        {
            if (seedPiles != null) return;
            seedPiles = new List<(Vector3, WasteClass)>();
            foreach (RiverTrashItem item in FindObjectsOfType<RiverTrashItem>())
            {
                RiverFlowBuoyancy buoy = item.GetComponent<RiverFlowBuoyancy>();
                if (buoy != null && !buoy.driftDownstream && !item.isCollected) seedPiles.Add((item.transform.position, item.wasteClass));
            }
        }

        private void ReseedPiles(RiverTrashSpawner spawner)
        {
            if (spawner == null || seedPiles == null) return;
            foreach ((Vector3 pos, WasteClass wc) in seedPiles)
            {
                GameObject go = spawner.SpawnTrashAt(pos, wc, 1);
                RiverFlowBuoyancy buoy = go.GetComponent<RiverFlowBuoyancy>();
                if (buoy != null) buoy.driftDownstream = false;
            }
        }

        private void RaiseAlert(string msg, bool isDanger)
        {
            lastStatusMessage = msg;
            OnHazardOrAlert?.Invoke(msg, isDanger);
        }

        private void MarkStateDirty()
        {
            stateDirty = true;
        }

        private void NotifyState()
        {
            stateDirty = false;
            notifyThrottleTimer = 0f;
            Shader.SetGlobalFloat(WaterClarityId, waterClarity);
            OnStateChanged?.Invoke();
        }

        private void ResetStageState(
            int targetCumulativeRupiah,
            int targetRupiah,
            int targetToolIdx,
            bool galah,
            bool sampan,
            bool boom,
            bool bins,
            bool excavator,
            bool monsoon)
        {
            activeEnding = GameEnding.None;
            // Remove live trash so activeRiverTrashCount (decremented in RiverTrashItem.OnDisable) matches the scene
            foreach (RiverTrashItem item in FindObjectsOfType<RiverTrashItem>())
            {
                item.TryUnregister(); // Synchronous: Destroy() defers OnDisable, and isRegistered guards double decrement
                if (Application.isPlaying) Destroy(item.gameObject); else DestroyImmediate(item.gameObject); // edit-mode QA calls this too
            }
            LastEndingDiagnosis = string.Empty;
            SetWeather(monsoon);
            playerHealth = maxPlayerHealth;
            swimStamina = maxSwimStamina;
            isPlayerSwimming = false;
            isPlayerMovingInWater = false;
            isPlayerSprintingInWater = false;
            lowSwimStaminaWarned = false;
            drowningAlertCooldown = 0f;
            lastDamageWasDrowning = false;
            normalCargo = 0;
            medicalCargo = 0;
            biohazardCargo = 0;
            biohazardExposureTimer = 0f;
            SyncCargoTotal();
            rainRiseY = 0f;
            objPickup = objDeposit = objHazard = objTool = false;
            objHazardTimer = 0f;
            RefreshObjective();

            totalScooped = 0;
            recycledKg = 0;
            flushedKg = 0;
            medicalWasteSecured = 0;
            biohazardWasteSecured = 0;
            infectionIncidents = 0;
            wrongDiscardCount = 0;
            totalFinesPaid = 0;
            unpaidFineDebt = 0;
            pengepulHazardDumped = 0;
            communityTrust = 40;
            isTrustAuditPenaltyActive = false;
            boomTimer = 0f;
            stormSurgeTimer = 0f;
            stormWarned = false;
            nextEmergencyTriageTime = 0f;

            cumulativeEarnings = targetCumulativeRupiah;
            rupiah = targetRupiah;
            highestUnlockedToolIndex = ToolCatalog.GetHighestUnlockedIndex(cumulativeEarnings);
            for (int i = 0; i < HotbarSize; i++) hotbar[i] = 0;
            hotbar[0] = Mathf.Clamp(targetToolIdx, 1, 20);
            activeSlot = 0;
            equippedToolIndex = hotbar[0];
            OnHotbarChanged?.Invoke();
            galahUnlocked = galah;
            sampanUnlocked = sampan;
            trashBoomActive = boom;
            kampungBinsInstalled = bins;
            excavatorUnlocked = excavator;
            cargoCapacity = excavator ? 60 : (sampan ? 22 : 8);
            OnEquippedToolChanged?.Invoke(EquippedTool);
        }

        private static void RestoreAllGunungNodes()
        {
            foreach (GunungNodeController node in FindObjectsOfType<GunungNodeController>(true))
            {
                node.Restore();
            }
        }
    }
}
