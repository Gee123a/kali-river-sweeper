using System.Globalization;
using KaliRiverSweeper.Core;
using KaliRiverSweeper.Player;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace KaliRiverSweeper.UI
{
    /// <summary>
    /// Drives Canvas_HUD from RiverGameManager events (OnStateChanged, OnToolUnlocked, OnWeatherChanged,
    /// OnHazardOrAlert). Gameplay values are read inside handlers. The only timed work is the toast
    /// timer and the map refresh at mapRefreshHz, which keeps the chevron on the player.
    /// Child elements are found by name at Awake, so Canvas_HUD.prefab must keep the names from
    /// docs/HUD_SPEC_NIKI.md section 3.
    /// </summary>
    public sealed class KaliHudController : MonoBehaviour
    {
        private static readonly CultureInfo Invariant = CultureInfo.InvariantCulture;

        // Filtration dot colors per docs/HUD_SPEC_NIKI.md section 4.
        private static readonly Color SiagaGreen = new Color32(0x15, 0x80, 0x3D, 255);
        private static readonly Color SiagaAmber = new Color32(0xC9, 0x7A, 0x0A, 255);
        private static readonly Color SiagaOrange = new Color32(0xEA, 0x58, 0x0C, 255);
        private static readonly Color SiagaRed = new Color32(0xE1, 0x1D, 0x8F, 255);
        private static readonly Color Ink = new Color32(0x1E, 0x1F, 0x1D, 255);
        private static readonly Color Alert = new Color32(0xB5, 0x0E, 0x6F, 255);
        private static readonly Color Track = new Color32(0xDC, 0xDA, 0xD2, 255);

        [Header("Map bounds (world X/Z), matched to the river extent")]
        [SerializeField] private float mapMinX = -65f;
        [SerializeField] private float mapMaxX = 65f;
        [SerializeField] private float mapMinZ = -90f;
        [SerializeField] private float mapMaxZ = 90f;
        [SerializeField] private float mapRefreshHz = 15f;

        private RiverGameManager manager;
        private KaliPlayerController player;
        private float mapTimer;
        private float toastTimer;

        private Image[] rampCells;
        private Image filtrationDot;
        private RectTransform ruler;
        private RectTransform clarityFill;
        private RectTransform contour;
        private RectTransform chevron;
        private TMP_Text damLabel;
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

        private void Awake()
        {
            rampCells = new Image[10];
            for (int i = 0; i < rampCells.Length; i++)
            {
                rampCells[i] = Find<Image>("TL_SurvivalFloodSheet/Row_HP/Cell_Ramp_" + i);
            }

            filtrationDot = Find<Image>("TL_SurvivalFloodSheet/Row_SiagaWater/Img_FiltrationDot");
            ruler = Find<RectTransform>("TL_SurvivalFloodSheet/Row_SiagaWater/RulerNeedle");
            clarityFill = Find<RectTransform>("TC_EcologicalHydroRail/Cell_Kejernihan/Img_ClarityFill");
            contour = Find<RectTransform>("BR_VellumHydroMap/Img_ContourCanalBase");
            chevron = Find<RectTransform>("BR_VellumHydroMap/Icon_PlayerSampan");
            damLabel = Find<TMP_Text>("BR_VellumHydroMap/TMP_DamLabel");

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
            manager.OnWeatherChanged -= HandleWeatherChanged;
            manager.OnHazardOrAlert -= HandleHazardOrAlert;
            manager = null;
        }

        private void Update()
        {
            // Subscription retry: covers a manager spawned after the HUD. Not a gameplay poll.
            if (manager == null)
            {
                TrySubscribe();
            }

            UpdateToast();
            UpdateMap();
        }

        private void TrySubscribe()
        {
            if (manager != null || RiverGameManager.Instance == null) return;

            manager = RiverGameManager.Instance;
            manager.OnStateChanged += Refresh;
            manager.OnToolUnlocked += HandleToolUnlocked;
            manager.OnWeatherChanged += HandleWeatherChanged;
            manager.OnHazardOrAlert += HandleHazardOrAlert;
            Refresh();
        }

        private void HandleWeatherChanged(bool isMonsoonStorm)
        {
            Refresh();
        }

        private void HandleHazardOrAlert(string message, bool isAlert)
        {
            Refresh();
        }

        private void UpdateToast()
        {
            if (toast == null || !toast.activeSelf) return;

            toastTimer -= Time.unscaledDeltaTime;
            if (toastTimer <= 0f) toast.SetActive(false);
        }

        // Throttled to mapRefreshHz. Map +Z points up; the chevron tip points along the player's heading.
        private void UpdateMap()
        {
            if (chevron == null || contour == null) return;

            mapTimer -= Time.unscaledDeltaTime;
            if (mapTimer > 0f) return;
            mapTimer = 1f / Mathf.Max(1f, mapRefreshHz);

            if (player == null)
            {
                player = FindObjectOfType<KaliPlayerController>();
                if (player == null) return;
            }

            Vector3 p = player.transform.position;
            float nx = Mathf.Clamp01(Mathf.InverseLerp(mapMinX, mapMaxX, p.x));
            float nz = Mathf.Clamp01(Mathf.InverseLerp(mapMinZ, mapMaxZ, p.z));

            // Contour and chevron share the map's top-left anchor. Clamp the chevron inside the contour area.
            Vector2 origin = contour.anchoredPosition;
            Vector2 area = contour.sizeDelta;
            chevron.anchoredPosition = new Vector2(origin.x + nx * area.x, origin.y - (1f - nz) * area.y);
            chevron.localRotation = Quaternion.Euler(0f, 0f, -player.transform.eulerAngles.y);
        }

        private void Refresh()
        {
            if (manager == null) return;

            float hpRatio = manager.maxPlayerHealth > 0f ? Mathf.Clamp01(manager.playerHealth / manager.maxPlayerHealth) : 0f;
            int filled = Mathf.RoundToInt(hpRatio * rampCells.Length);
            Color filledColor = manager.playerHealth <= 40f ? Alert : Ink;
            for (int i = 0; i < rampCells.Length; i++)
            {
                if (rampCells[i] != null) rampCells[i].color = i < filled ? filledColor : Track;
            }

            SetText(hpValue, Mathf.RoundToInt(manager.playerHealth).ToString(Invariant));
            SetText(siagaLevel, "SIAGA " + manager.SiagaLevel.ToString(Invariant));
            SetText(waterMeters, FormatMeters(manager.currentWaterLevelY));
            if (filtrationDot != null) filtrationDot.color = SiagaDotColor(manager.SiagaLevel);
            if (ruler != null)
            {
                float t = Mathf.Clamp01(Mathf.InverseLerp(-0.25f, 2.45f, manager.currentWaterLevelY));
                ruler.anchoredPosition = new Vector2(200f + t * 120f, ruler.anchoredPosition.y);
            }

            SetText(gunungPercent, Mathf.RoundToInt(manager.gunungSampahHealth * 100f).ToString(Invariant) + "%");
            SetText(clarityPercent, Mathf.RoundToInt(manager.waterClarity * 100f).ToString(Invariant) + "%");
            if (clarityFill != null)
            {
                clarityFill.sizeDelta = new Vector2(240f * Mathf.Clamp01(manager.waterClarity), clarityFill.sizeDelta.y);
            }

            SetText(monsunTimer, FormatClock(manager.monsoonCountdownRemaining));
            SetText(monsunLabel, manager.isMonsoonStorm ? "BADAI" : "MONSUN");
            SetText(damLabel, "DAM " + Mathf.RoundToInt(manager.gunungSampahHealth * 100f).ToString(Invariant) + "%");

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

        private static Color SiagaDotColor(int siagaLevel)
        {
            switch (siagaLevel)
            {
                case 1: return SiagaRed;
                case 2: return SiagaOrange;
                case 3: return SiagaAmber;
                default: return SiagaGreen;
            }
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
