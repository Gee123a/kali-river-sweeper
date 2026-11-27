using System;
using UnityEngine;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem;
#endif

namespace KaliRiverSweeper.Core
{
    public enum UpgradeTier
    {
        Galah4m = 1,
        WoodenSampan = 2,
        TrashBoom = 3,
        AmphibiousExcavator = 4
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
        public float medicalPrickDamage = 18f;
        public float biohazardGraceSeconds = 10f;
        public float biohazardExposureTimer;

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
        public const float WaterRisePerTrashUnit = 0.020f;
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
        public bool demoHotkeysArmed;
        public GameEnding activeEnding = GameEnding.None;
        public string lastStatusMessage = "Kumpulkan sampah dari sungai & jual ke stasiun yang tepat.";
        public string LastEndingDiagnosis { get; private set; } = string.Empty;

        public int TotalTrashInRiver => Mathf.Max(0, activeRiverTrashCount) + Mathf.Max(0, piledRiverTrashCount);
        public bool IsBankOverflowing => currentWaterLevelY >= bankOverflowWaterY;
        public bool IsSellLocked => currentWaterLevelY >= sellLockWaterY;
        public bool IsBiohazardDotActive => biohazardCargo > 0 && biohazardExposureTimer >= biohazardGraceSeconds;
        public float BiohazardGraceRemaining => biohazardCargo > 0 ? Mathf.Max(0f, biohazardGraceSeconds - biohazardExposureTimer) : biohazardGraceSeconds;
        public float SwimStaminaNormalized => maxSwimStamina > 0f ? Mathf.Clamp01(swimStamina / maxSwimStamina) : 0f;
        public bool IsSwimming => isPlayerSwimming;
        public bool IsDrowning => isPlayerSwimming && swimStamina <= 0f && activeEnding == GameEnding.None;
        public ToolDefinition EquippedTool => ToolCatalog.GetTool(equippedToolIndex);
        public int SiagaLevel => floodPressure >= 0.85f ? 1 : floodPressure >= 0.60f ? 2 : floodPressure >= 0.35f ? 3 : 4;
        public bool IsDemoHotkeyBusy => demoHotkeysArmed || demoJumpConsumedFrame == Time.frameCount;
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
        public event Action<string, bool> OnHazardOrAlert;
        public event Action<StationAuditReceipt> OnStationAuditReceipt;
        public event Action<GameEnding, string> OnEndingWithDiagnosisTriggered;

        private float boomTimer;
        private bool stateDirty;
        private float notifyThrottleTimer;
        private int demoJumpConsumedFrame = -1;
        private bool isTrustAuditPenaltyActive;
        private float nextEmergencyTriageTime;
        private bool lowSwimStaminaWarned;
        private float drowningAlertCooldown;
        private bool lastDamageWasDrowning;
        private readonly bool[] ownedTools = new bool[21];
        private const float NotifyIntervalSeconds = 0.10f; // ~10 Hz throttle for Update ticks
        private const int MaxVisualBarrierProps = 22;

        private void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
            if (Application.isPlaying) Time.timeScale = 1f;
            ownedTools[1] = true;
            monsoonCountdownRemaining = monsoonCountdownSeconds;
            RecalculateWaterMetrics();
            Shader.SetGlobalFloat(WaterClarityId, waterClarity);
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
            HandleDemoHotkeys();
            if (activeEnding != GameEnding.None) return;

            // 1. Monsoon countdown & automatic storm trigger
            if (monsoonCountdownRemaining > 0f)
            {
                monsoonCountdownRemaining = Mathf.Max(0f, monsoonCountdownRemaining - dt);
                if (monsoonCountdownRemaining <= monsoonStormTriggerRemaining && !isMonsoonStorm)
                {
                    SetWeather(true);
                }
                MarkStateDirty();

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
                if (boomTimer >= 4f)
                {
                    boomTimer = 0f;
                    AddEarnings(2500);
                    if (piledRiverTrashCount > 0) piledRiverTrashCount--;
                    RecalculateWaterMetrics();
                    MarkStateDirty();
                }
            }

            // 3. Biohazard cargo Damage Over Time (DoT) & passive safe recovery
            if (biohazardCargo > 0)
            {
                biohazardExposureTimer += dt;
                if (biohazardExposureTimer >= biohazardGraceSeconds)
                {
                    float dotRate = Mathf.Min(12f, 2.5f + 1.5f * biohazardCargo);
                    ApplyPlayerDamage(dotRate * dt, notifyImmediate: false);
                    if (activeEnding != GameEnding.None) return;
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
            int space = cargoCapacity - cargoCount;
            if (space <= 0 || piledRiverTrashCount <= 0) return 0;

            int take = Mathf.Min(maxUnits, Mathf.Min(space, piledRiverTrashCount));
            piledRiverTrashCount -= take;

            // Barrier piles are mixed Normal/Medical/Biohazard
            for (int i = 0; i < take; i++)
            {
                float r = UnityEngine.Random.value;
                WasteClass wc = r < 0.70f ? WasteClass.Normal : (r < 0.88f ? WasteClass.Medical : WasteClass.Biohazard);
                ApplyCargoGainAndMedicalCheck(wc, 1);
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
            if (cargoCount >= cargoCapacity)
            {
                RaiseAlert("Kargo penuh! Buang ke stasiun atau tekan [Q] di daratan tinggi.", true);
                return false;
            }

            int added = Mathf.Min(Mathf.Max(1, amount), cargoCapacity - cargoCount);
            ApplyCargoGainAndMedicalCheck(wasteClass, added);
            RecalculateWaterMetrics();
            NotifyState();
            return true;
        }

        public float GetEffectiveMedicalPrickChance()
        {
            if (highestUnlockedToolIndex >= ToolCatalog.SnakeGrabberIndex) return 0f;
            return EquippedTool.MedicalPrickChance;
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
            if (cargoCount <= 0) return $"Kargo kosong. Serok sampah di sungai dulu untuk setor ke {station}.";

            string held = string.Empty;
            if (normalCargo > 0) held += $"{normalCargo} Normal -> Bank Sampah [1]  ";
            if (medicalCargo > 0) held += $"{medicalCargo} Medis -> Pos Medis B3 [2]  ";
            if (biohazardCargo > 0) held += $"{biohazardCargo} Biohazard -> Karantina [3]";

            string accepts = station switch
            {
                DiscardStationType.BankSampah => "Bank Sampah hanya terima NORMAL [1]",
                DiscardStationType.PosMedisB3 => "Pos Medis B3 hanya terima MEDIS [2]",
                DiscardStationType.KarantinaBiohazard => "Karantina hanya terima BIOHAZARD [3]",
                _ => station.ToString()
            };
            return $"{accepts}! Kargo kamu: {held.Trim()} (salah tekan 1/2/3 = DENDA!)";
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
                int rate = wasteClass switch
                {
                    WasteClass.Normal => 4000,
                    WasteClass.Medical => 9000,
                    WasteClass.Biohazard => 14000,
                    _ => 4000
                };
                int basePayout = qty * rate;
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

        public bool IsToolUnlocked(int index) => index >= 1 && index <= highestUnlockedToolIndex;

        public bool IsToolOwned(int index) => index >= 1 && index <= 20 && (index == 1 || ownedTools[index]);

        public bool BuyTool(int toolIndex)
        {
            if (toolIndex < 1 || toolIndex > 20 || IsToolOwned(toolIndex)) return false;

            ToolDefinition tool = ToolCatalog.GetTool(toolIndex);
            int cost = tool.UnlockRupiah;
            if (rupiah < cost) return false;

            rupiah -= cost;
            ownedTools[toolIndex] = true;
            if (toolIndex > highestUnlockedToolIndex) highestUnlockedToolIndex = toolIndex;
            if (toolIndex >= 6) galahUnlocked = true;

            equippedToolIndex = toolIndex;
            OnEquippedToolChanged?.Invoke(EquippedTool);
            RaiseAlert($"Alat #{tool.Index:00} {tool.DisplayName} dibeli & dipakai!", false);
            NotifyState();
            return true;
        }

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
            int clamped = Mathf.Clamp(toolIndex, 1, 20);
            if (!IsToolOwned(clamped)) return false;
            if (clamped == equippedToolIndex) return false;
            equippedToolIndex = clamped;
            OnEquippedToolChanged?.Invoke(EquippedTool);
            NotifyState();
            return true;
        }

        public void CycleTool(int delta)
        {
            int step = delta >= 0 ? 1 : -1;
            int idx = equippedToolIndex;
            for (int i = 0; i < 20; i++)
            {
                idx += step;
                if (idx < 1) idx = 20;
                if (idx > 20) idx = 1;
                if (IsToolOwned(idx))
                {
                    SelectTool(idx);
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
            bool canDredge = excavatorUnlocked || EquippedTool.GunungDamagePerSwing > 0f;
            if (!canDredge || gunungSampahHealth <= 0f || activeEnding != GameEnding.None) return;

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
            RaiseAlert("Butuh alat #13 Ganco Ganda Winch+ atau Pindad Excavator untuk mengeruk Gunung Sampah!", true);
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
            NotifyState();
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
            rupiah += amount;
            cumulativeEarnings += amount;
            CheckToolMilestones();
        }

        private void CheckToolMilestones()
        {
            int newHighest = ToolCatalog.GetHighestUnlockedIndex(cumulativeEarnings);
            if (newHighest <= highestUnlockedToolIndex) return;

            int prevHighest = highestUnlockedToolIndex;
            highestUnlockedToolIndex = newHighest;
            if (newHighest >= 6) galahUnlocked = true;

            for (int i = prevHighest + 1; i <= newHighest; i++)
            {
                ToolDefinition tool = ToolCatalog.GetTool(i);
                OnToolUnlocked?.Invoke(tool);
                RaiseAlert($"Alat Baru Tersedia di Kopdes: #{tool.Index:00} {tool.DisplayName}!", false);
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
            currentWaterLevelY = BaseWaterLevelY + totalTrash * WaterRisePerTrashUnit;
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
                : "HP habis akibat tusukan limbah medis atau paparan Biohazard >10 detik. Buka #10 Capitan Ular (Rp 80rb) & segera setor ke Pos Medis B3 / Karantina!",
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
            if (Application.isPlaying)
            {
                Time.timeScale = 0f;
                Cursor.lockState = CursorLockMode.None;
                Cursor.visible = true;
            }
            NotifyState();
            OnEndingTriggered?.Invoke(ending);
            OnEndingWithDiagnosisTriggered?.Invoke(ending, LastEndingDiagnosis);
        }

        public void RestartRun()
        {
            ResetStageState(targetCumulativeRupiah: 0, targetRupiah: 0, targetToolIdx: 1,
                galah: false, sampan: false, boom: false, bins: false, excavator: false, monsoon: false);
            piledRiverTrashCount = 4;
            monsoonCountdownRemaining = monsoonCountdownSeconds;
            RestoreAllGunungNodes();
            gunungSampahHealth = 1f;
            RecalculateWaterMetrics();

            RiverTrashSpawner spawner = FindObjectOfType<RiverTrashSpawner>();
            if (spawner != null) spawner.ResetSpawnerState();

            KaliRiverSweeper.Player.KaliPlayerController player = FindObjectOfType<KaliRiverSweeper.Player.KaliPlayerController>();
            if (player != null) player.ResetToInitialSpawn();

            RaiseAlert("Permainan diulang! Kumpulkan sampah dari sungai & setor ke stasiun yang tepat.", false);
            NotifyState();
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

        // Built-in F9 Presentation Stage Jump for 3-minute Sidang Demo
        private void HandleDemoHotkeys()
        {
            if (WasF9Pressed())
            {
                demoHotkeysArmed = !demoHotkeysArmed;
                RaiseAlert(demoHotkeysArmed ? "F9 Stage Jump Armed: Tekan 1, 2, 3, atau 4" : "F9 Stage Jump Disarmed", false);
                NotifyState();
            }
            if (!demoHotkeysArmed) return;

            if (WasDigitPressed(1))
            {
                demoHotkeysArmed = false;
                demoJumpConsumedFrame = Time.frameCount;
                ResetStageState(targetCumulativeRupiah: 0, targetRupiah: 0, targetToolIdx: 1,
                    galah: false, sampan: false, boom: false, bins: false, excavator: false, monsoon: false);
                piledRiverTrashCount = 4;
                monsoonCountdownRemaining = monsoonCountdownSeconds;
                RestoreAllGunungNodes();
                gunungSampahHealth = 1f;
                RecalculateWaterMetrics();
                NotifyState();
            }
            else if (WasDigitPressed(2))
            {
                demoHotkeysArmed = false;
                demoJumpConsumedFrame = Time.frameCount;
                ResetStageState(targetCumulativeRupiah: 80000, targetRupiah: 45000, targetToolIdx: ToolCatalog.SnakeGrabberIndex,
                    galah: true, sampan: true, boom: false, bins: true, excavator: false, monsoon: false);
                communityTrust = Mathf.Max(communityTrust, 65);
                piledRiverTrashCount = 10;
                monsoonCountdownRemaining = monsoonCountdownSeconds;
                RestoreAllGunungNodes();
                gunungSampahHealth = 1f;
                RecalculateWaterMetrics();
                NotifyState();
            }
            else if (WasDigitPressed(3))
            {
                demoHotkeysArmed = false;
                demoJumpConsumedFrame = Time.frameCount;
                ResetStageState(targetCumulativeRupiah: 360000, targetRupiah: 250000, targetToolIdx: 20,
                    galah: true, sampan: true, boom: true, bins: true, excavator: true, monsoon: true);
                piledRiverTrashCount = Mathf.Max(0, 117 - activeRiverTrashCount); // Places waterLevelY at ~2.09m (Siaga 1 + Sell-Lock)
                monsoonCountdownRemaining = 45f;
                RestoreAllGunungNodes();
                gunungSampahHealth = 1f;
                RecalculateWaterMetrics();
                NotifyState();
            }
            else if (WasDigitPressed(4))
            {
                demoHotkeysArmed = false;
                demoJumpConsumedFrame = Time.frameCount;
                ResetStageState(targetCumulativeRupiah: 360000, targetRupiah: 250000, targetToolIdx: 20,
                    galah: true, sampan: true, boom: true, bins: true, excavator: true, monsoon: false);
                piledRiverTrashCount = 0;
                activeRiverTrashCount = 0;
                CompleteCleanBreach();
            }
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
            if (Application.isPlaying) Time.timeScale = 1f;
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
            nextEmergencyTriageTime = 0f;

            cumulativeEarnings = targetCumulativeRupiah;
            rupiah = targetRupiah;
            highestUnlockedToolIndex = ToolCatalog.GetHighestUnlockedIndex(cumulativeEarnings);
            for (int i = 1; i < ownedTools.Length; i++)
            {
                ownedTools[i] = i <= targetToolIdx;
            }
            equippedToolIndex = Mathf.Clamp(targetToolIdx, 1, 20);
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

        private static bool WasF9Pressed()
        {
#if ENABLE_INPUT_SYSTEM
            if (Keyboard.current != null && Keyboard.current.f9Key.wasPressedThisFrame) return true;
#endif
#if ENABLE_LEGACY_INPUT_MANAGER
            if (Input.GetKeyDown(KeyCode.F9)) return true;
#endif
            return false;
        }

        private static bool WasDigitPressed(int digit)
        {
#if ENABLE_INPUT_SYSTEM
            if (Keyboard.current != null)
            {
                bool hit = digit switch
                {
                    1 => Keyboard.current.digit1Key.wasPressedThisFrame,
                    2 => Keyboard.current.digit2Key.wasPressedThisFrame,
                    3 => Keyboard.current.digit3Key.wasPressedThisFrame,
                    4 => Keyboard.current.digit4Key.wasPressedThisFrame,
                    _ => false
                };
                if (hit) return true;
            }
#endif
#if ENABLE_LEGACY_INPUT_MANAGER
            KeyCode kc = (KeyCode)((int)KeyCode.Alpha0 + digit);
            if (Input.GetKeyDown(kc)) return true;
#endif
            return false;
        }
    }
}
