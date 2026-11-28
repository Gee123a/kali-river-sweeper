using System.Globalization;
using KaliRiverSweeper.Core;
using KaliRiverSweeper.Player;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace KaliRiverSweeper.UI
{
    /// <summary>
    /// Canvas_ShopBankSampah controller. Opens when the player presses [E] at the Kopdes service point
    /// (KaliPlayerController.OnShopRequested) and closes on KaliPlayerController.OnShopClosed (Esc / [E]).
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
            UpgradeTier.TrashBoom,
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
                player.OnShopRequested -= HandleShopRequested;
                player.OnShopClosed -= HandleShopClosed;
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

            player.OnShopRequested += HandleShopRequested;
            player.OnShopClosed += HandleShopClosed;
            SetOpen(player.IsShopOpen);
        }

        private void HandleShopRequested()
        {
            SetOpen(true);
        }

        private void HandleShopClosed()
        {
            SetOpen(false);
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
            // Slot = role: buying goes into the tool's role slot and auto trades in the old one (50% credit).
            if (manager.IsToolOwned(toolIndex)) manager.SelectTool(toolIndex);
            else manager.BuyTool(toolIndex);
            Refresh();
        }

        private void SetOpen(bool open)
        {
            if (group == null) return;
            group.alpha = open ? 1f : 0f;
            group.blocksRaycasts = open;
            group.interactable = open;
            if (open)
            {
                Cursor.lockState = CursorLockMode.None;
                Cursor.visible = true;
                Refresh();
            }
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

            // Tools (grouped by role rows in the prefab): owned tools are selectable; unlocked ones show the net price
            // after the automatic 50% trade-in of the tool already in that role slot.
            // TODO(Niki): restyle the role rows / cards (DESIGN.md vellum panels, role icons).
            for (int i = 0; i < ToolCount; i++)
            {
                int index = i + 1;
                bool unlocked = manager.IsToolUnlocked(index);
                bool owned = manager.IsToolOwned(index);
                bool equipped = index == manager.equippedToolIndex;
                int price = manager.GetToolPrice(index);
                bool canBuy = unlocked && !owned && manager.rupiah >= price;
                SetButton(toolButtons[i], (owned && !equipped) || canBuy);
                if (toolBg[i] != null) toolBg[i].color = equipped ? Zone0 : (owned ? Vellum : Track);
                string status = equipped ? "DIPAKAI" : (owned ? "PILIH" : (unlocked
                    ? (manager.GetTradeInCredit(index) > 0 ? "TUKAR " : "BELI ") + (price >= 0 ? "Rp " + FormatRupiah(price) : "+Rp " + FormatRupiah(-price))
                    : "TERKUNCI"));
                SetText(toolStatus[i], status);
                if (toolStatus[i] != null) toolStatus[i].color = equipped ? Vellum : (owned ? Ink : InkSecondary);
            }

            SetText(footer, "Satu slot = satu peran. Beli → masuk slot perannya; alat lama ditukar otomatis (kredit 50%). [E] / Esc untuk menutup.");
        }

        private bool TierOwned(UpgradeTier tier)
        {
            switch (tier)
            {
                case UpgradeTier.Galah4m: return manager.galahUnlocked;
                case UpgradeTier.WoodenSampan: return manager.sampanUnlocked;
                case UpgradeTier.TrashBoom: return manager.trashBoomActive;
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
                case UpgradeTier.TrashBoom: return 75000;
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
            // The builder parents everything under Card, so try that too.
            Transform t = transform.Find(path);
            if (t == null) t = transform.Find("Card/" + path);
            return t != null ? t.GetComponent<T>() : null;
        }

        private static void SetText(TMP_Text target, string value)
        {
            if (target != null) target.text = value;
        }
    }
}
