using System.Globalization;
using KaliRiverSweeper.Core;
using KaliRiverSweeper.Player;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace KaliRiverSweeper.UI
{
    /// <summary>
    /// Canvas_ShopBankSampah controller. Opens while the player is inside the Toko Alat trigger
    /// (KaliPlayerController.OnNearbyHubChanged with isTokoAlat) and closes when they leave.
    /// Buying and selecting call RiverGameManager directly, so the shop does not add gameplay logic.
    /// Refreshes on RiverGameManager.OnStateChanged, OnToolUnlocked and OnEquippedToolChanged.
    /// Child elements are found by name, so Canvas_ShopBankSampah.prefab must keep the names from KaliShopPrefabBuilder.
    /// </summary>
    public sealed class KaliShopController : MonoBehaviour
    {
        private static readonly CultureInfo Invariant = CultureInfo.InvariantCulture;

        private static readonly Color Ink = new Color32(0x1E, 0x1F, 0x1D, 255);
        private static readonly Color InkSecondary = new Color32(0x54, 0x53, 0x4E, 255);
        private static readonly Color Vellum = new Color32(0xF4, 0xF2, 0xEC, 255);
        private static readonly Color Zone0 = new Color32(0x11, 0x12, 0x11, 255);
        private static readonly Color Teal = new Color32(0x1B, 0x8A, 0x7A, 255);
        private static readonly Color Alert = new Color32(0xB5, 0x0E, 0x6F, 255);
        private static readonly Color Track = new Color32(0xDC, 0xDA, 0xD2, 255);

        public const int BinsPrice = 30000;
        public const int ToolCount = 20;

        private RiverGameManager manager;
        private KaliPlayerController player;
        private CanvasGroup group;
        private float subscribeRetryTimer;

        private TMP_Text rupiahValue;
        private TMP_Text trustValue;
        private Button binsButton;
        private TMP_Text binsStatus;
        private Button[] tierButtons;
        private TMP_Text[] tierStatus;
        private Button[] toolButtons;
        private TMP_Text[] toolStatus;
        private Image[] toolBg;
        private TMP_Text footer;

        // Tiers in the order the armada row is built: Galah 4m, Sampan, Trash Boom, Excavator.
        private static readonly UpgradeTier[] Tiers =
        {
            UpgradeTier.Galah4m,
            UpgradeTier.WoodenSampan,
            UpgradeTier.TrashBoomAndPosSortir,
            UpgradeTier.AmphibiousExcavator,
        };

        private void Awake()
        {
            group = GetComponent<CanvasGroup>();

            rupiahValue = Find<TMP_Text>("Header/TMP_RupiahValue");
            trustValue = Find<TMP_Text>("Header/TMP_TrustValue");
            binsButton = Find<Button>("Bins/Btn_BuyBins");
            binsStatus = Find<TMP_Text>("Bins/TMP_BinsStatus");

            tierButtons = new Button[Tiers.Length];
            tierStatus = new TMP_Text[Tiers.Length];
            for (int i = 0; i < Tiers.Length; i++)
            {
                tierButtons[i] = Find<Button>("Armada/Tier_" + i + "/Btn_Buy");
                tierStatus[i] = Find<TMP_Text>("Armada/Tier_" + i + "/TMP_Status");
            }

            toolButtons = new Button[ToolCount];
            toolStatus = new TMP_Text[ToolCount];
            toolBg = new Image[ToolCount];
            for (int i = 0; i < ToolCount; i++)
            {
                toolButtons[i] = Find<Button>("Tools/Grid/Tool_" + (i + 1).ToString("00", Invariant) + "/Btn_Select");
                toolStatus[i] = Find<TMP_Text>("Tools/Grid/Tool_" + (i + 1).ToString("00", Invariant) + "/TMP_Status");
                toolBg[i] = Find<Image>("Tools/Grid/Tool_" + (i + 1).ToString("00", Invariant));
            }

            footer = Find<TMP_Text>("Footer/TMP_Hint");

            WireButtons();
            SetOpen(false);
        }

        private void OnEnable()
        {
            TrySubscribeManager();
            TrySubscribePlayer();
        }

        private void Start()
        {
            TrySubscribeManager();
            TrySubscribePlayer();
        }

        private void OnDisable()
        {
            if (manager != null)
            {
                manager.OnStateChanged -= Refresh;
                manager.OnToolUnlocked -= HandleToolEvent;
                manager.OnEquippedToolChanged -= HandleEquippedEvent;
                manager = null;
            }

            if (player != null)
            {
                player.OnNearbyHubChanged -= HandleNearbyHubChanged;
                player = null;
            }
        }

        private void Update()
        {
            // Subscription retry at 2 Hz. Not a gameplay poll.
            subscribeRetryTimer -= Time.unscaledDeltaTime;
            if (subscribeRetryTimer <= 0f)
            {
                subscribeRetryTimer = 0.5f;
                TrySubscribeManager();
                TrySubscribePlayer();
            }
        }

        private void TrySubscribeManager()
        {
            if (manager != null || RiverGameManager.Instance == null) return;

            manager = RiverGameManager.Instance;
            manager.OnStateChanged += Refresh;
            manager.OnToolUnlocked += HandleToolEvent;
            manager.OnEquippedToolChanged += HandleEquippedEvent;
            Refresh();
        }

        private void TrySubscribePlayer()
        {
            if (player != null) return;

            player = FindObjectOfType<KaliPlayerController>();
            if (player == null) return;

            player.OnNearbyHubChanged += HandleNearbyHubChanged;
        }

        private void HandleNearbyHubChanged(bool near, DiscardStationType station, bool isPosSortir, bool isTokoAlat, string hubName)
        {
            SetOpen(near && isTokoAlat);
        }

        private void HandleToolEvent(ToolDefinition tool)
        {
            Refresh();
        }

        private void HandleEquippedEvent(ToolDefinition tool)
        {
            Refresh();
        }

        private void WireButtons()
        {
            if (binsButton != null) binsButton.onClick.AddListener(OnBuyBins);
            for (int i = 0; i < Tiers.Length; i++)
            {
                if (tierButtons[i] == null) continue;
                int slot = i;
                tierButtons[i].onClick.AddListener(() => OnBuyTier(slot));
            }

            for (int i = 0; i < ToolCount; i++)
            {
                if (toolButtons[i] == null) continue;
                int toolIndex = i + 1;
                toolButtons[i].onClick.AddListener(() => OnSelectTool(toolIndex));
            }
        }

        public void OnBuyBins()
        {
            if (manager == null) return;
            manager.BuyKampungBins();
            Refresh();
        }

        public void OnBuyTier(int slot)
        {
            if (manager == null || slot < 0 || slot >= Tiers.Length) return;
            manager.BuyUpgrade(Tiers[slot]);
            Refresh();
        }

        public void OnSelectTool(int toolIndex)
        {
            if (manager == null) return;
            manager.SelectTool(toolIndex);
            Refresh();
        }

        private void SetOpen(bool open)
        {
            if (group == null) return;
            group.alpha = open ? 1f : 0f;
            group.blocksRaycasts = open;
            group.interactable = open;
            if (open) Refresh();
        }

        private void Refresh()
        {
            if (manager == null || group == null) return;
            if (group.alpha <= 0f) return;

            SetText(rupiahValue, "Rp " + FormatRupiah(manager.rupiah));
            SetText(trustValue, "Kepercayaan warga " + manager.communityTrust.ToString(Invariant));

            // Bins: one-time install.
            bool binsOwned = manager.kampungBinsInstalled;
            bool binsAffordable = manager.rupiah >= BinsPrice;
            SetButton(binsButton, !binsOwned && binsAffordable);
            SetText(binsStatus, binsOwned ? "TERPASANG" : (binsAffordable ? "BELI  Rp " + FormatRupiah(BinsPrice) : "Rp " + FormatRupiah(BinsPrice)));

            // Armada tiers: owned, affordable, or locked by price.
            for (int i = 0; i < Tiers.Length; i++)
            {
                bool owned = TierOwned(Tiers[i]);
                int cost = TierCost(Tiers[i]);
                bool affordable = manager.rupiah >= cost;
                SetButton(tierButtons[i], !owned && affordable);
                SetText(tierStatus[i], owned ? "DIMILIKI" : (affordable ? "BELI  Rp " + FormatRupiah(cost) : "Rp " + FormatRupiah(cost)));
            }

            // Tools: unlocked tools are selectable; the equipped tool is marked.
            for (int i = 0; i < ToolCount; i++)
            {
                int index = i + 1;
                bool unlocked = index <= manager.highestUnlockedToolIndex;
                bool equipped = index == manager.equippedToolIndex;
                SetButton(toolButtons[i], unlocked && !equipped);
                if (toolBg[i] != null) toolBg[i].color = equipped ? Zone0 : (unlocked ? Vellum : Track);
                string status = equipped ? "DIPAKAI" : (unlocked ? "PILIH" : "TERKUNCI");
                SetText(toolStatus[i], status);
                if (toolStatus[i] != null) toolStatus[i].color = equipped ? Vellum : (unlocked ? Ink : InkSecondary);
            }

            SetText(footer, "Klik kartu untuk membeli. Tutup dengan keluar dari Toko Alat.");
        }

        private bool TierOwned(UpgradeTier tier)
        {
            switch (tier)
            {
                case UpgradeTier.Galah4m: return manager.galahUnlocked;
                case UpgradeTier.WoodenSampan: return manager.sampanUnlocked;
                case UpgradeTier.TrashBoomAndPosSortir: return manager.trashBoomActive;
                case UpgradeTier.AmphibiousExcavator: return manager.excavatorUnlocked;
                default: return false;
            }
        }

        // Prices match RiverGameManager.BuyUpgrade.
        private static int TierCost(UpgradeTier tier)
        {
            switch (tier)
            {
                case UpgradeTier.Galah4m: return 20000;
                case UpgradeTier.WoodenSampan: return 40000;
                case UpgradeTier.TrashBoomAndPosSortir: return 75000;
                case UpgradeTier.AmphibiousExcavator: return 120000;
                default: return 999999;
            }
        }

        private static void SetButton(Button button, bool interactable)
        {
            if (button != null) button.interactable = interactable;
        }

        private static string FormatRupiah(int amount)
        {
            return amount.ToString("#,0", Invariant).Replace(',', '.');
        }

        private T Find<T>(string path) where T : Component
        {
            Transform t = transform.Find(path);
            return t != null ? t.GetComponent<T>() : null;
        }

        private static void SetText(TMP_Text target, string value)
        {
            if (target != null) target.text = value;
        }
    }
}
