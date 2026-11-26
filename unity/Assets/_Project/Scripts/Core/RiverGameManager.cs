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
        TrashBoomAndPosSortir = 3,
        AmphibiousExcavator = 4
    }

    public enum GameEnding
    {
        None,
        FloodFail,
        CompromisedOceanFlush,
        TrueSdgVictory,
        HealthFail
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
        public int pengepulHazardDumped;

        [Header("Player Health & Hazards")]
        public float playerHealth = 100f;
        public float maxPlayerHealth = 100f;
        public float medicalPrickDamage = 18f;
        public float biohazardGraceSeconds = 10f;
        public float biohazardExposureTimer;

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

        public int TotalTrashInRiver => Mathf.Max(0, activeRiverTrashCount) + Mathf.Max(0, piledRiverTrashCount);
        public bool IsBankOverflowing => currentWaterLevelY >= bankOverflowWaterY;
        public bool IsSellLocked => currentWaterLevelY >= sellLockWaterY;
        public bool IsBiohazardDotActive => biohazardCargo > 0 && biohazardExposureTimer >= biohazardGraceSeconds;
        public float BiohazardGraceRemaining => biohazardCargo > 0 ? Mathf.Max(0f, biohazardGraceSeconds - biohazardExposureTimer) : biohazardGraceSeconds;
        public ToolDefinition EquippedTool => ToolCatalog.GetTool(equippedToolIndex);
        public int SiagaLevel => floodPressure >= 0.85f ? 1 : floodPressure >= 0.60f ? 2 : floodPressure >= 0.35f ? 3 : 4;
        public bool IsDemoHotkeyBusy => demoHotkeysArmed || demoJumpConsumedFrame == Time.frameCount;

        // Backwards-compatible events for Niki's UI & VFX
        public event Action OnStateChanged;
        public event Action<bool> OnWeatherChanged;
        public event Action<GameEnding> OnEndingTriggered;

        // Extended events for 20-tool milestones & hazard/station feedback
        public event Action<ToolDefinition> OnToolUnlocked;
        public event Action<ToolDefinition> OnEquippedToolChanged;
        public event Action<string, bool> OnHazardOrAlert;

        private float boomTimer;
        private bool stateDirty;
        private float notifyThrottleTimer;
        private int demoJumpConsumedFrame = -1;
        private const float NotifyIntervalSeconds = 0.10f; // ~10 Hz throttle for Update ticks
        private const int MaxVisualBarrierProps = 22;

        private void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
            monsoonCountdownRemaining = monsoonCountdownSeconds;
            RecalculateWaterMetrics();
            Shader.SetGlobalFloat(WaterClarityId, waterClarity);
        }

        private void Update()
        {
            HandleDemoHotkeys();
            if (activeEnding != GameEnding.None) return;

            // 1. Monsoon countdown & automatic storm trigger
            if (monsoonCountdownRemaining > 0f)
            {
                monsoonCountdownRemaining = Mathf.Max(0f, monsoonCountdownRemaining - Time.deltaTime);
                if (monsoonCountdownRemaining <= monsoonStormTriggerRemaining && !isMonsoonStorm)
                {
                    SetWeather(true);
                }
                MarkStateDirty();

                if (monsoonCountdownRemaining <= 0f)
                {
                    RaiseAlert("Badai Monsun berhasil dilewati! Sungai & desa selamat.", false);
                    TriggerEnding(GameEnding.TrueSdgVictory);
                    return;
                }
            }

            // 2. Trash Boom passive income & water relief
            if (trashBoomActive)
            {
                boomTimer += Time.deltaTime;
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
                biohazardExposureTimer += Time.deltaTime;
                if (biohazardExposureTimer >= biohazardGraceSeconds)
                {
                    float dotRate = Mathf.Min(12f, 2.5f + 1.5f * biohazardCargo);
                    ApplyPlayerDamage(dotRate * Time.deltaTime, notifyImmediate: false);
                }
                MarkStateDirty();
            }
            else
            {
                if (biohazardExposureTimer > 0f)
                {
                    biohazardExposureTimer = Mathf.Max(0f, biohazardExposureTimer - 3f * Time.deltaTime);
                    MarkStateDirty();
                }
                if (!IsBankOverflowing && playerHealth < maxPlayerHealth)
                {
                    playerHealth = Mathf.Min(maxPlayerHealth, playerHealth + 0.8f * Time.deltaTime);
                    MarkStateDirty();
                }
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
                notifyThrottleTimer += Time.deltaTime;
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

        private void ApplyCargoGainAndMedicalCheck(WasteClass wasteClass, int added)
        {
            switch (wasteClass)
            {
                case WasteClass.Medical:
                    medicalCargo += added;
                    ToolDefinition tool = EquippedTool;
                    for (int i = 0; i < added; i++)
                    {
                        if (UnityEngine.Random.value < tool.MedicalPrickChance)
                        {
                            infectionIncidents++;
                            ApplyPlayerDamage(medicalPrickDamage, notifyImmediate: false);
                            RaiseAlert($"Tertusuk limbah medis! (-{medicalPrickDamage:0} HP) Gunakan #10 Capitan Ular!", true);
                        }
                    }
                    break;
                case WasteClass.Biohazard:
                    biohazardCargo += added;
                    RaiseAlert($"Biohazard Radioaktif di kargo ({biohazardCargo})! Bawa ke Karantina sebelum DoT!", true);
                    break;
                default:
                    normalCargo += added;
                    break;
            }

            totalScooped += added;
            SyncCargoTotal();
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

        /// <summary>
        /// Discards a single waste class at the target station.
        /// Proper station yields full Rupiah & trust; wrong station incurs a Rupiah fine & trust penalty.
        /// Blocked during Sell-Lock.
        /// </summary>
        public int DiscardWasteAtStation(DiscardStationType station, WasteClass wasteClass, bool sortedAtPosSortir = false)
        {
            if (activeEnding != GameEnding.None) return 0;
            if (IsSellLocked)
            {
                RaiseAlert("SELL-LOCK! Stasiun terendam banjir. Tekan [Q] untuk buang kargo di daratan tinggi!", true);
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
                    WasteClass.Normal => (sortedAtPosSortir && trashBoomActive) ? 7500 : 4000,
                    WasteClass.Medical => 9000,
                    WasteClass.Biohazard => 14000,
                    _ => 4000
                };
                int payout = qty * rate;
                AddEarnings(payout);
                recycledKg += qty * 5;
                communityTrust = Mathf.Min(100, communityTrust + qty * 4);

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

                RaiseAlert($"Setor {qty}x {wasteClass} bersih: +Rp {payout:N0}", false);
                NotifyState();
                return payout;
            }

            int finePerItem = wasteClass switch
            {
                WasteClass.Biohazard => 8000,
                WasteClass.Medical => 5000,
                _ => 2500
            };
            int fine = qty * finePerItem;
            rupiah = Mathf.Max(0, rupiah - fine);
            totalFinesPaid += fine;
            wrongDiscardCount += qty;
            int trustLoss = qty * (wasteClass == WasteClass.Biohazard ? 12 : (wasteClass == WasteClass.Medical ? 8 : 4));
            communityTrust = Mathf.Max(0, communityTrust - trustLoss);

            if (wasteClass == WasteClass.Biohazard) biohazardExposureTimer = 0f;

            RaiseAlert($"SALAH STASIUN ({wasteClass} -> {station})! Denda Rp {fine:N0} (-{trustLoss} Trust)", true);
            NotifyState();
            return -fine;
        }

        /// <summary>
        /// Discards all held waste classes at a station in one action.
        /// At Gudang Pengepul, sells everything cheaply with Trust/SDG penalties for hazardous waste.
        /// </summary>
        public int DiscardAllAtStation(DiscardStationType station, bool sortedAtPosSortir = false)
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
            if (normalCargo > 0) net += DiscardWasteAtStation(station, WasteClass.Normal, sortedAtPosSortir);
            if (medicalCargo > 0) net += DiscardWasteAtStation(station, WasteClass.Medical, sortedAtPosSortir);
            if (biohazardCargo > 0) net += DiscardWasteAtStation(station, WasteClass.Biohazard, sortedAtPosSortir);
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
                communityTrust = Mathf.Max(0, communityTrust - trustPenalty);
                if (wasteClass == WasteClass.Biohazard) biohazardExposureTimer = 0f;
                RaiseAlert($"Jual {qty}x {wasteClass} ke Pengepul: +Rp {payout:N0} (Penalti -{trustPenalty} Trust!)", true);
            }
            else
            {
                RaiseAlert($"Jual {qty}x Normal ke Pengepul: +Rp {payout:N0}", false);
            }

            NotifyState();
            return payout;
        }

        public int SellAllAtPengepul()
        {
            if (activeEnding != GameEnding.None) return 0;
            if (IsSellLocked)
            {
                RaiseAlert("SELL-LOCK! Stasiun terendam banjir. Tekan [Q] untuk buang kargo di daratan tinggi!", true);
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
                communityTrust = Mathf.Max(0, communityTrust - trustPenalty);
                RaiseAlert($"Pengepul borong semua: +Rp {payout:N0} (Penalti -{trustPenalty} Trust karena limbah B3/Biohazard!)", true);
            }
            else
            {
                RaiseAlert($"Pengepul borong semua: +Rp {payout:N0} (Harga murah)", false);
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

        public int SellAtBankSampah(bool sortedAtPosSortir)
        {
            return DiscardAllAtStation(DiscardStationType.BankSampah, sortedAtPosSortir);
        }

        public bool BuyKampungBins()
        {
            if (kampungBinsInstalled || rupiah < 30000) return false;
            rupiah -= 30000;
            kampungBinsInstalled = true;
            communityTrust = Mathf.Min(100, communityTrust + 25);
            RaiseAlert("Tempat Sampah Kampung terpasang! Sampah desa turun 60%.", false);
            NotifyState();
            return true;
        }

        public bool BuyUpgrade(UpgradeTier tier)
        {
            int cost = tier switch
            {
                UpgradeTier.Galah4m => 20000,
                UpgradeTier.WoodenSampan => 40000,
                UpgradeTier.TrashBoomAndPosSortir => 75000,
                UpgradeTier.AmphibiousExcavator => 120000,
                _ => 999999
            };
            if (rupiah < cost) return false;
            rupiah -= cost;
            ApplyTier(tier);
            NotifyState();
            return true;
        }

        public bool SelectTool(int toolIndex)
        {
            int clamped = Mathf.Clamp(toolIndex, 1, highestUnlockedToolIndex);
            if (clamped == equippedToolIndex) return false;
            equippedToolIndex = clamped;
            OnEquippedToolChanged?.Invoke(EquippedTool);
            NotifyState();
            return true;
        }

        public void CycleTool(int delta)
        {
            if (highestUnlockedToolIndex <= 1) return;
            int next = equippedToolIndex + delta;
            if (next < 1) next = highestUnlockedToolIndex;
            if (next > highestUnlockedToolIndex) next = 1;
            SelectTool(next);
        }

        public void DamageGunungSampah(float amount)
        {
            bool canDredge = excavatorUnlocked || EquippedTool.GunungDamagePerSwing > 0f;
            if (!canDredge || gunungSampahHealth <= 0f || activeEnding != GameEnding.None) return;

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

        public void TriggerEmergencyFlush()
        {
            if (activeEnding != GameEnding.None) return;
            flushedKg += Mathf.RoundToInt(gunungSampahHealth * 1200f) + TotalTrashInRiver * 5;
            gunungSampahHealth = 0f;
            activeRiverTrashCount = 0;
            piledRiverTrashCount = 0;
            RecalculateWaterMetrics();
            TriggerEnding(GameEnding.CompromisedOceanFlush);
        }

        public void CompleteCleanBreach()
        {
            if (activeEnding != GameEnding.None) return;
            gunungSampahHealth = 0f;
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
            ApplyTier(UpgradeTier.TrashBoomAndPosSortir);
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
            equippedToolIndex = newHighest;
            if (newHighest >= 6) galahUnlocked = true;

            for (int i = prevHighest + 1; i <= newHighest; i++)
            {
                ToolDefinition tool = ToolCatalog.GetTool(i);
                OnToolUnlocked?.Invoke(tool);
                RaiseAlert($"Alat Baru Terbuka: #{tool.Index:00} {tool.DisplayName}!", false);
            }

            OnEquippedToolChanged?.Invoke(EquippedTool);
        }

        private void ApplyPlayerDamage(float amount, bool notifyImmediate)
        {
            if (amount <= 0f || activeEnding != GameEnding.None) return;
            playerHealth = Mathf.Max(0f, playerHealth - amount);
            if (playerHealth <= 0f)
            {
                RaiseAlert("HP habis! Paparan limbah B3/infeksi berakibat fatal.", true);
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
                case UpgradeTier.TrashBoomAndPosSortir: trashBoomActive = true; break;
                case UpgradeTier.AmphibiousExcavator: excavatorUnlocked = true; cargoCapacity = 60; break;
            }
        }

        private void TriggerEnding(GameEnding ending)
        {
            activeEnding = ending;
            NotifyState();
            OnEndingTriggered?.Invoke(ending);
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
            SetWeather(monsoon);
            playerHealth = maxPlayerHealth;
            normalCargo = 0;
            medicalCargo = 0;
            biohazardCargo = 0;
            biohazardExposureTimer = 0f;
            SyncCargoTotal();

            cumulativeEarnings = targetCumulativeRupiah;
            rupiah = targetRupiah;
            highestUnlockedToolIndex = ToolCatalog.GetHighestUnlockedIndex(cumulativeEarnings);
            equippedToolIndex = Mathf.Clamp(targetToolIdx, 1, highestUnlockedToolIndex);
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
