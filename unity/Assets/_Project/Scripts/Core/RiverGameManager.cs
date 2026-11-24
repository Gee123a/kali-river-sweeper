using System;
using UnityEngine;

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
        TrueSdgVictory
    }

    public class RiverGameManager : MonoBehaviour
    {
        public static RiverGameManager Instance { get; private set; }
        private static readonly int WaterClarityId = Shader.PropertyToID("_WaterClarity");

        [Header("Economy & Cargo")]
        public int rupiah;
        public int cargoCount;
        public int cargoCapacity = 8;
        public int totalScooped;
        public int recycledKg;
        public int flushedKg;

        [Header("River & Flood State")]
        [Range(0f, 1f)] public float waterClarity = 0.12f;
        [Range(0f, 1f)] public float floodPressure = 0.18f;
        [Range(0f, 1f)] public float gunungSampahHealth = 1f;
        [Range(0, 100)] public int communityTrust = 40;
        public bool isMonsoonStorm;

        [Header("Unlocks & ALP Choices")]
        public bool galahUnlocked;
        public bool sampanUnlocked;
        public bool trashBoomActive;
        public bool excavatorUnlocked;
        public bool kampungBinsInstalled;
        public bool demoHotkeysArmed;
        public GameEnding activeEnding = GameEnding.None;

        public int SiagaLevel => floodPressure >= 0.85f ? 1 : floodPressure >= 0.60f ? 2 : floodPressure >= 0.35f ? 3 : 4;

        public event Action OnStateChanged;
        public event Action<bool> OnWeatherChanged;
        public event Action<GameEnding> OnEndingTriggered;

        private float boomTimer;

        private void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
            Shader.SetGlobalFloat(WaterClarityId, waterClarity);
        }

        private void Update()
        {
            if (activeEnding != GameEnding.None) return;

            if (trashBoomActive)
            {
                boomTimer += Time.deltaTime;
                if (boomTimer >= 4f)
                {
                    boomTimer = 0f;
                    rupiah += 2500;
                    waterClarity = Mathf.Clamp01(waterClarity + 0.006f);
                    NotifyState();
                }
            }

            if (isMonsoonStorm && gunungSampahHealth > 0.05f)
            {
                float rate = trashBoomActive ? 0.012f : 0.024f;
                floodPressure = Mathf.Clamp01(floodPressure + rate * Time.deltaTime);
                if (floodPressure >= 1f) TriggerEnding(GameEnding.FloodFail);
                else NotifyState();
            }

            HandleDemoHotkeys();
        }

        public bool TryAddCargo(int amount = 1)
        {
            if (cargoCount >= cargoCapacity) return false;
            cargoCount = Mathf.Min(cargoCapacity, cargoCount + amount);
            totalScooped += amount;
            waterClarity = Mathf.Clamp01(waterClarity + 0.015f * amount);
            NotifyState();
            return true;
        }

        // Choice A (Fast Burn Pit vs Bank Sampah Sorting)
        public int DumpAtBurnPit()
        {
            if (cargoCount <= 0) return 0;
            int payout = cargoCount * 2000;
            rupiah += payout;
            communityTrust = Mathf.Max(0, communityTrust - 10);
            cargoCount = 0;
            NotifyState();
            return payout;
        }

        public int SellAtBankSampah(bool sortedAtPosSortir)
        {
            if (cargoCount <= 0) return 0;
            int rate = sortedAtPosSortir && trashBoomActive ? 7500 : 4000;
            int payout = cargoCount * rate;
            rupiah += payout;
            recycledKg += cargoCount * 5;
            communityTrust = Mathf.Min(100, communityTrust + 8);
            cargoCount = 0;
            NotifyState();
            return payout;
        }

        // Choice B (Personal Boat vs Upstream Kampung Bins Root-Cause Fix)
        public bool BuyKampungBins()
        {
            if (kampungBinsInstalled || rupiah < 30000) return false;
            rupiah -= 30000;
            kampungBinsInstalled = true;
            communityTrust = Mathf.Min(100, communityTrust + 25);
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

        public void DamageGunungSampah(float amount)
        {
            if (!excavatorUnlocked || gunungSampahHealth <= 0f) return;
            gunungSampahHealth = Mathf.Clamp01(gunungSampahHealth - amount);
            waterClarity = Mathf.Clamp01(waterClarity + amount * 0.35f);
            if (gunungSampahHealth <= 0.01f) CompleteCleanBreach();
            else NotifyState();
        }

        // Choice C (Monsoon Siaga 1 Climax: Emergency Flush vs Hold & Dredge)
        public void TriggerEmergencyFlush()
        {
            if (activeEnding != GameEnding.None) return;
            flushedKg += Mathf.RoundToInt(gunungSampahHealth * 1200f);
            gunungSampahHealth = 0f;
            floodPressure = 0.1f;
            TriggerEnding(GameEnding.CompromisedOceanFlush);
        }

        public void CompleteCleanBreach()
        {
            if (activeEnding != GameEnding.None) return;
            gunungSampahHealth = 0f;
            waterClarity = 1f;
            floodPressure = 0.08f;
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
            rupiah = Mathf.Max(rupiah, 250000);
            ApplyTier(UpgradeTier.Galah4m);
            ApplyTier(UpgradeTier.WoodenSampan);
            ApplyTier(UpgradeTier.TrashBoomAndPosSortir);
            ApplyTier(UpgradeTier.AmphibiousExcavator);
            NotifyState();
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

        private void NotifyState()
        {
            Shader.SetGlobalFloat(WaterClarityId, waterClarity);
            OnStateChanged?.Invoke();
        }

        // Built-in F9 Presentation Stage Jump for 3-minute Sidang Demo
        private void HandleDemoHotkeys()
        {
#if ENABLE_LEGACY_INPUT_MANAGER || !ENABLE_INPUT_SYSTEM
            if (Input.GetKeyDown(KeyCode.F9)) demoHotkeysArmed = !demoHotkeysArmed;
            if (!demoHotkeysArmed) return;
            if (Input.GetKeyDown(KeyCode.Alpha1)) { activeEnding = GameEnding.None; SetWeather(false); waterClarity = 0.12f; NotifyState(); }
            if (Input.GetKeyDown(KeyCode.Alpha2)) { UnlockSandboxDemo(); BuyKampungBins(); SetWeather(false); }
            if (Input.GetKeyDown(KeyCode.Alpha3)) { UnlockSandboxDemo(); SetWeather(true); floodPressure = 0.78f; NotifyState(); }
            if (Input.GetKeyDown(KeyCode.Alpha4)) { UnlockSandboxDemo(); SetWeather(false); CompleteCleanBreach(); }
#endif
        }
    }
}
