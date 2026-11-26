using System.Globalization;
using KaliRiverSweeper.Core;
using TMPro;
using UnityEngine;

namespace KaliRiverSweeper.UI
{
    /// <summary>
    /// Drives Canvas_HUD from RiverGameManager events. Reads state only inside handlers,
    /// never polls gameplay fields in Update.
    /// Child elements are located by name at Awake, so Canvas_HUD.prefab must keep the
    /// names from docs/HUD_SPEC_NIKI.md section 3.
    /// </summary>
    public sealed class KaliHudController : MonoBehaviour
    {
        private static readonly CultureInfo Invariant = CultureInfo.InvariantCulture;

        private RiverGameManager manager;

        private TMP_Text hpValue;
        private TMP_Text siagaLevel;
        private TMP_Text waterMeters;
        private TMP_Text gunungPercent;
        private TMP_Text clarityPercent;
        private TMP_Text monsunTimer;
        private TMP_Text monsunLabel;
        private GameObject biohazardStrip;
        private TMP_Text biohazardCountdown;
        private GameObject sellLockStrip;
        private TMP_Text normalCount;
        private TMP_Text medisCount;
        private TMP_Text bioCount;
        private TMP_Text kas;
        private TMP_Text muatan;
        private TMP_Text warga;
        private GameObject toast;
        private TMP_Text toastText;
        private float toastTimer;

        private void Awake()
        {
            hpValue = Find<TMP_Text>("TL_SurvivalFloodSheet/Row_HP/TMP_HPValue");
            siagaLevel = Find<TMP_Text>("TL_SurvivalFloodSheet/Row_SiagaWater/TMP_SiagaLevel");
            waterMeters = Find<TMP_Text>("TL_SurvivalFloodSheet/Row_SiagaWater/TMP_WaterMeters");
            gunungPercent = Find<TMP_Text>("TC_EcologicalHydroRail/Cell_GunungSampah/TMP_GunungPct");
            clarityPercent = Find<TMP_Text>("TC_EcologicalHydroRail/Cell_Kejernihan/TMP_KejernihanPct");
            monsunTimer = Find<TMP_Text>("TC_EcologicalHydroRail/Cell_MonsunTimer/TMP_MonsunTimer");
            monsunLabel = Find<TMP_Text>("TC_EcologicalHydroRail/Cell_MonsunTimer/TMP_MonsunLabel");
            biohazardStrip = FindGo("TC_ContextualAlertRail/Strip_BiohazardTimer");
            biohazardCountdown = Find<TMP_Text>("TC_ContextualAlertRail/Strip_BiohazardTimer/TMP_BiohazardCountdown");
            sellLockStrip = FindGo("TC_ContextualAlertRail/Strip_SellLockDump");
            normalCount = Find<TMP_Text>("TR_EconomyCargoLedger/Grid_Cargo3Class/Cell_Normal/TMP_NormalCount");
            medisCount = Find<TMP_Text>("TR_EconomyCargoLedger/Grid_Cargo3Class/Cell_MedisB3/TMP_MedisCount");
            bioCount = Find<TMP_Text>("TR_EconomyCargoLedger/Grid_Cargo3Class/Cell_Biohazard/TMP_BioCount");
            kas = Find<TMP_Text>("TR_EconomyCargoLedger/Row_KasRupiah/TMP_KasValue");
            muatan = Find<TMP_Text>("TR_EconomyCargoLedger/Row_MuatanHeader/TMP_MuatanValue");
            warga = Find<TMP_Text>("TR_EconomyCargoLedger/Row_WargaTrust/TMP_WargaValue");
            toast = FindGo("TL_ToolUnlockToast");
            toastText = Find<TMP_Text>("TL_ToolUnlockToast/TMP_ToastText");

            if (toast != null) toast.SetActive(false);
        }

        private void OnEnable()
        {
            TrySubscribe();
        }

        // Start runs after every Awake, so RiverGameManager.Instance is set by now.
        private void Start()
        {
            TrySubscribe();
        }

        private void OnDisable()
        {
            if (manager == null) return;

            manager.OnStateChanged -= Refresh;
            manager.OnToolUnlocked -= HandleToolUnlocked;
            manager = null;
        }

        private void Update()
        {
            // Subscription retry: covers a manager spawned after the HUD. Not a gameplay poll.
            if (manager == null)
            {
                TrySubscribe();
            }

            if (toast == null || !toast.activeSelf) return;

            toastTimer -= Time.unscaledDeltaTime;
            if (toastTimer <= 0f) toast.SetActive(false);
        }

        private void TrySubscribe()
        {
            if (manager != null || RiverGameManager.Instance == null) return;

            manager = RiverGameManager.Instance;
            manager.OnStateChanged += Refresh;
            manager.OnToolUnlocked += HandleToolUnlocked;
            Refresh();
        }

        private void Refresh()
        {
            if (manager == null) return;

            SetText(hpValue, Mathf.RoundToInt(manager.playerHealth).ToString(Invariant));
            SetText(siagaLevel, "SIAGA " + manager.SiagaLevel.ToString(Invariant));
            SetText(waterMeters, FormatMeters(manager.currentWaterLevelY));
            SetText(gunungPercent, Mathf.RoundToInt(manager.gunungSampahHealth * 100f).ToString(Invariant) + "%");
            SetText(clarityPercent, Mathf.RoundToInt(manager.waterClarity * 100f).ToString(Invariant) + "%");
            SetText(monsunTimer, FormatClock(manager.monsoonCountdownRemaining));
            SetText(monsunLabel, manager.isMonsoonStorm ? "BADAI" : "MONSUN");

            bool hasBiohazard = manager.biohazardCargo > 0;
            SetActive(biohazardStrip, hasBiohazard);
            if (hasBiohazard)
            {
                SetText(biohazardCountdown, Mathf.CeilToInt(manager.BiohazardGraceRemaining).ToString(Invariant) + "s");
            }

            SetActive(sellLockStrip, manager.IsSellLocked);

            SetText(normalCount, manager.normalCargo.ToString(Invariant));
            SetText(medisCount, manager.medicalCargo.ToString(Invariant));
            SetText(bioCount, manager.biohazardCargo.ToString(Invariant));
            SetText(kas, "Rp " + FormatRupiah(manager.rupiah));
            SetText(muatan, manager.cargoCount.ToString(Invariant) + " / " + manager.cargoCapacity.ToString(Invariant));
            SetText(warga, manager.communityTrust.ToString(Invariant));
        }

        private void HandleToolUnlocked(ToolDefinition tool)
        {
            if (tool == null || toast == null || toastText == null) return;

            string badge = tool.GunungDamagePerSwing > 0f ? "  · BISA KERUK" : string.Empty;
            SetText(toastText, "Alat Baru: #" + tool.Index.ToString("00", Invariant) + " " + tool.DisplayName + badge);
            toast.SetActive(true);
            toastTimer = 3.5f;
        }

        private static string FormatMeters(float levelY)
        {
            string sign = levelY >= 0f ? "+" : string.Empty;
            return sign + levelY.ToString("0.00", Invariant) + "m";
        }

        private static string FormatClock(float seconds)
        {
            int total = Mathf.Max(0, Mathf.CeilToInt(seconds));
            return (total / 60).ToString("00", Invariant) + ":" + (total % 60).ToString("00", Invariant);
        }

        // Indonesian thousand separator is "." (Rp 1.250.000).
        private static string FormatRupiah(int amount)
        {
            return amount.ToString("#,0", Invariant).Replace(',', '.');
        }

        private T Find<T>(string path) where T : Component
        {
            Transform t = transform.Find(path);
            return t != null ? t.GetComponent<T>() : null;
        }

        private GameObject FindGo(string path)
        {
            Transform t = transform.Find(path);
            return t != null ? t.gameObject : null;
        }

        private static void SetText(TMP_Text target, string value)
        {
            if (target != null) target.text = value;
        }

        private static void SetActive(GameObject target, bool active)
        {
            if (target != null && target.activeSelf != active) target.SetActive(active);
        }
    }
}
