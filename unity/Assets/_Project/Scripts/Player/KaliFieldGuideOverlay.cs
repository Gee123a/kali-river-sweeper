using UnityEngine;
using KaliRiverSweeper.Core;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem;
#endif

namespace KaliRiverSweeper.Player
{
    /// <summary>
    /// Lightweight player-side alert toast and toggleable [H] controls/sorting guide.
    /// Ensures wrong-station fines, hazard warnings, and keybinds are always visible in Play Mode
    /// without modifying Niki's UI prefabs.
    /// </summary>
    public class KaliFieldGuideOverlay : MonoBehaviour
    {
        // Spec F: the controls panel is open for the first 15 s, then folds into the [H] pill (unless toggled).
        private const float AutoGuideSeconds = 15f;
        private bool showGuide = true;
        private bool autoGuide = true;
        private string toastMessage = string.Empty;
        private bool toastIsDanger;
        private float toastExpiresAt;
        private RiverGameManager subscribedManager;
        private KaliPlayerController player;
        private float autoGuideTimer;
        private bool titleControls;
        private bool nikiStartMenu;
        private bool nikiPauseMenu;
        private float nextUiScanTime;
        private CanvasGroup sdgReport;

        private GUIStyle pillStyle;
        private GUIStyle panelStyle;
        private GUIStyle titleStyle;
        private GUIStyle bodyStyle;
        private GUIStyle alertStyle;
        private GUIStyle infoStyle;
        private GUIStyle activeSlotStyle;
        private GUIStyle activeSlotTextStyle;
        private GUIStyle objectiveStyle;
        private GUIStyle menuTitleStyle;
        private GUIStyle menuButtonStyle;
        private GUIStyle dimStyle;
        private GUIStyle emptySlotTextStyle;

        private void OnEnable()
        {
            TrySubscribe();
        }

        private void OnDisable()
        {
            if (subscribedManager != null)
            {
                subscribedManager.OnHazardOrAlert -= HandleAlert;
                subscribedManager.OnStationAuditReceipt -= HandleReceipt;
                subscribedManager = null;
            }
        }

        private void Update()
        {
            TrySubscribe();
            RiverGameManager gm = subscribedManager;
            KaliGameState state = gm != null ? gm.State : KaliGameState.Playing;

            // Niki's menus take over once they exist; scan at 1 Hz (unscaled: time is frozen in Paused).
            if (Time.unscaledTime >= nextUiScanTime)
            {
                nextUiScanTime = Time.unscaledTime + 1f;
                nikiStartMenu = GameObject.Find("Canvas_StartMenu") != null;
                nikiPauseMenu = GameObject.Find("Canvas_PauseMenu") != null;
                if (sdgReport == null)
                {
                    GameObject report = GameObject.Find("Canvas_SDGImpactReport");
                    if (report != null) sdgReport = report.GetComponent<CanvasGroup>();
                }
                if (player == null) player = FindObjectOfType<KaliPlayerController>();
            }

            // ponytail: SdgImpactReportController only shows itself, so the fallback hides it again after Main Lagi / Menu.
            // TODO(Niki): listen to RiverGameManager.OnGameStateChanged in the report and drop this.
            if (sdgReport != null && state != KaliGameState.Ended && sdgReport.alpha > 0f)
            {
                sdgReport.alpha = 0f;
                sdgReport.blocksRaycasts = false;
                sdgReport.interactable = false;
            }

            if (gm != null && state == KaliGameState.Title && !nikiStartMenu && WasStartPressed()) gm.StartRun();

            if (WasHelpPressed())
            {
                showGuide = !showGuide;
                autoGuide = false;
            }
            else if (autoGuide && state == KaliGameState.Playing)
            {
                // Spec F: the controls panel stays open for the first 15 s of play, then folds into the [H] pill.
                autoGuideTimer += Time.unscaledDeltaTime;
                if (autoGuideTimer >= AutoGuideSeconds)
                {
                    showGuide = false;
                    autoGuide = false;
                }
            }
        }

        private void TrySubscribe()
        {
            if (subscribedManager != null) return;
            RiverGameManager gm = RiverGameManager.Instance;
            if (gm == null) return;
            subscribedManager = gm;
            gm.OnHazardOrAlert += HandleAlert;
            gm.OnStationAuditReceipt += HandleReceipt;
        }

        private void HandleAlert(string msg, bool isDanger)
        {
            if (string.IsNullOrEmpty(msg)) return;
            toastMessage = msg;
            toastIsDanger = isDanger;
            toastExpiresAt = Time.unscaledTime + (isDanger ? 5.0f : 3.8f);
        }

        private void HandleReceipt(StationAuditReceipt receipt)
        {
            string sign = receipt.RupiahDelta >= 0 ? "+" : "";
            string trustSign = receipt.TrustDelta >= 0 ? "+" : "";
            toastMessage = $"{receipt.Summary} ({receipt.Station}): {sign}Rp {receipt.RupiahDelta:N0} | Trust {trustSign}{receipt.TrustDelta}";
            toastIsDanger = !receipt.IsPass;
            toastExpiresAt = Time.unscaledTime + 4.5f;
        }

        private void OnGUI()
        {
            EnsureStyles();
            RiverGameManager gmState = subscribedManager != null ? subscribedManager : RiverGameManager.Instance;
            if (gmState != null && gmState.State == KaliGameState.Title)
            {
                if (!nikiStartMenu) DrawTitleMenu(gmState);
                return;
            }

            // 1. Live alert/fine toast (top-center)
            if (!string.IsNullOrEmpty(toastMessage) && Time.unscaledTime < toastExpiresAt)
            {
                float w = Mathf.Min(720f, Screen.width - 40f);
                Rect r = new Rect((Screen.width - w) * 0.5f, 18f, w, 40f);
                GUI.Box(r, toastMessage, toastIsDanger ? alertStyle : infoStyle);
            }

            // 1b. Contextual Swim Stamina gauge (only visible while swimming or recovering stamina)
            RiverGameManager gm = subscribedManager != null ? subscribedManager : RiverGameManager.Instance;
            if (gm != null && (gm.isPlayerSwimming || gm.swimStamina < gm.maxSwimStamina - 0.1f))
            {
                float pct = gm.SwimStaminaNormalized;
                Rect stamBox = new Rect(18f, Screen.height - 84f, 228f, 34f);
                GUI.Box(stamBox, GUIContent.none, panelStyle);

                Rect barBg = new Rect(stamBox.x + 8f, stamBox.y + 20f, stamBox.width - 16f, 8f);
                GUI.DrawTexture(barBg, Texture2D.whiteTexture, ScaleMode.StretchToFill, true, 0f, new Color(0.86f, 0.85f, 0.82f, 1f), 0f, 0f);
                Color barCol = gm.IsDrowning
                    ? new Color(0.71f, 0.055f, 0.435f, 1f)
                    : (pct <= 0.25f ? new Color(0.706f, 0.325f, 0.035f, 1f) : new Color(0.106f, 0.541f, 0.478f, 1f));
                Rect barFill = new Rect(barBg.x, barBg.y, barBg.width * pct, barBg.height);
                GUI.DrawTexture(barFill, Texture2D.whiteTexture, ScaleMode.StretchToFill, true, 0f, barCol, 0f, 0f);

                string stamText = gm.IsDrowning
                    ? "TENGGELAM! NAIK KE DARAT!"
                    : $"STAMINA RENANG: {Mathf.RoundToInt(pct * 100f)}%";
                GUI.Label(new Rect(stamBox.x + 8f, stamBox.y + 2f, stamBox.width - 16f, 18f), stamText, bodyStyle);
            }

            // 1c. Minimal 4-slot role hotbar (bottom-centre, above the dock sheet). Niki restyles later.
            if (gm != null) DrawHotbar(gm);

            // 1c'. Aim hint under the crosshair: which slot the aimed trash / pile / Gunung needs.
            if (player != null && !string.IsNullOrEmpty(player.AimHint) && gm != null && gm.State == KaliGameState.Playing)
            {
                float hw = Mathf.Min(460f, Screen.width - 40f);
                GUI.Box(new Rect((Screen.width - hw) * 0.5f, Screen.height * 0.5f + 28f, hw, 28f), player.AimHint, objectiveStyle);
            }

            if (gm != null && gm.State == KaliGameState.Paused && !nikiPauseMenu) DrawPauseMenu(gm);
            if (gm != null && gm.State == KaliGameState.Ended) DrawEndedBar(gm);

            // 1d. Objective pill (under Niki's top-left HUD sheets). ponytail: IMGUI polls CurrentObjective, no event needed here.
            if (gm != null && !string.IsNullOrEmpty(gm.CurrentObjective))
            {
                // Canvas_HUD CanvasScaler: ScaleWithScreenSize, 1920x1080, match 0.5 -> geometric mean of the two ratios.
                float hudScale = Mathf.Sqrt((Screen.width / 1920f) * (Screen.height / 1080f));
                float ow = Mathf.Min(520f, Screen.width - 36f);
                // Lowest top-left HUD edge: TL_ToolUnlockToast at y -184 + 64 high = 248 reference units.
                float oy = 248f * hudScale + 8f;
                GUI.Box(new Rect(36f * hudScale, oy, ow, 52f), "TUJUAN: " + gm.CurrentObjective, objectiveStyle);
            }

            // 2. Compact [H] hint pill (bottom-left)
            Rect pillRect = new Rect(18f, Screen.height - 44f, 228f, 28f);
            if (GUI.Button(pillRect, showGuide ? "[H] Tutup Panduan Kontrol" : "[H] Kontrol & Pemilahan", pillStyle))
            {
                showGuide = !showGuide;
                autoGuide = false;
            }

            if (!showGuide) return;

            // 3. Toggleable Controls & Waste-Sorting Guide
            float gw = Mathf.Min(470f, Screen.width - 36f);
            float gh = 320f;
            Rect guideRect = new Rect(18f, Screen.height - gh - 90f, gw, gh);
            GUI.Box(guideRect, GUIContent.none, panelStyle);

            GUILayout.BeginArea(new Rect(guideRect.x + 14f, guideRect.y + 10f, gw - 28f, gh - 20f));
            GUILayout.Label("PANDUAN KONTROL & PEMILAHAN SAMPAH", titleStyle);
            GUILayout.Space(4f);
            GUILayout.Label(
                "GERAK, RENANG & SEROK:\n" +
                "  WASD + Shift/Space : Jalan / Lari / Lompat / Berenang Permukaan / Perahu\n" +
                "  Berenang di Sungai  : Menguras stamina (habis = tenggelam! Pulih di darat/perahu)\n" +
                "  Klik Kanan (Tahan/Klik) : Putar & Kunci Kamera\n" +
                "  Klik Kiri : Pakai alat  |  [1]-[4] / Scroll / [ ] : Ganti slot  |  [Esc] Jeda\n" +
                "  Slot = peran: [1] SEROK sampah biasa (cepat) | [2] CAPIT limbah medis\n" +
                "  [3] GANCO drum biohazard & Gunung (#13+) | [4] GARUK tumpukan Pintu Air\n\n" +
                "STASIUN (berdiri di depan loket, hadap gedung):\n" +
                "  [E] Setor: stasiun hanya ambil jenis yg cocok, sisanya tetap di kargo\n" +
                "  Normal -> Bank Sampah [B] | Medis -> Pos Medis B3 [M] | Biohazard -> Karantina [K]\n" +
                "  Gudang Pengepul [P]: Tahan [E] 1 dtk jual semua (murah, Penalti Trust!)\n" +
                "  Kopdes: [E] buka toko alat & armada | Dermaga: [E] naik/turun perahu\n" +
                "  Tahan [Q] 0.5s : Buang Kargo Darurat  |  Tahan [Shift+X] 1.5s : Flush (Sell-Lock)\n" +
                "  [R] (Saat Ending) : Ulang Permainan",
                bodyStyle);
            GUILayout.EndArea();
        }

        private void DrawHotbar(RiverGameManager gm)
        {
            const float boxW = 150f, boxH = 46f, gap = 6f;
            float totalW = RiverGameManager.HotbarSize * boxW + (RiverGameManager.HotbarSize - 1) * gap;
            float x0 = (Screen.width - totalW) * 0.5f;
            float y = Screen.height - Screen.height * (160f / 1080f) - boxH;
            for (int i = 0; i < RiverGameManager.HotbarSize; i++)
            {
                int toolIndex = gm.hotbar[i];
                bool active = i == gm.activeSlot && toolIndex > 0;
                Rect r = new Rect(x0 + i * (boxW + gap), y, boxW, boxH);
                GUI.Box(r, GUIContent.none, active ? activeSlotStyle : panelStyle);
                string role = ToolCatalog.RoleName((ToolRole)i);
                string name = "Beli di Kopdes";
                if (toolIndex > 0)
                {
                    ToolDefinition tool = ToolCatalog.GetTool(toolIndex);
                    name = tool.DisplayName.Length > 20 ? tool.DisplayName.Substring(0, 19) + "." : tool.DisplayName;
                    if (tool.Role == ToolRole.Capit) name += $" · tusuk {Mathf.RoundToInt(tool.MedicalPrickChance * 100f)}%";
                }
                GUIStyle txt = active ? activeSlotTextStyle : (toolIndex > 0 ? bodyStyle : emptySlotTextStyle);
                GUI.Label(new Rect(r.x + 6f, r.y + 2f, r.width - 10f, 20f), $"{i + 1}  {role}", txt);
                GUI.Label(new Rect(r.x + 6f, r.y + 22f, r.width - 10f, 20f), name, txt);
            }
        }

        // Fallback menus (spec I). Hidden once Niki's Canvas_StartMenu / Canvas_PauseMenu exist.
        private void DrawTitleMenu(RiverGameManager gm)
        {
            GUI.Box(new Rect(0f, 0f, Screen.width, Screen.height), GUIContent.none, dimStyle);
            float w = Mathf.Min(420f, Screen.width - 40f);
            float x = (Screen.width - w) * 0.5f;
            float y = Screen.height * 0.28f;
            GUI.Label(new Rect(x - 100f, y, w + 200f, 56f), "KALI — Penyapu Sungai", menuTitleStyle);
            y += 80f;
            if (GUI.Button(new Rect(x, y, w, 44f), "Mulai  [Enter]", menuButtonStyle)) gm.StartRun();
            y += 52f;
            if (GUI.Button(new Rect(x, y, w, 44f), titleControls ? "Tutup Kontrol" : "Kontrol", menuButtonStyle)) titleControls = !titleControls;
            y += 52f;
            if (GUI.Button(new Rect(x, y, w, 44f), "Keluar", menuButtonStyle)) Application.Quit();
            if (!titleControls) return;
            y += 60f;
            GUI.Box(new Rect(x - 40f, y, w + 80f, 128f),
                "WASD jalan · Klik kanan kunci kamera · Klik kiri pakai alat · [E] stasiun/Kopdes · [Esc] jeda\n" +
                "Slot = peran: [1] SEROK sampah biasa · [2] CAPIT limbah medis\n" +
                "[3] GANCO drum biohazard & Gunung (#13+) · [4] GARUK tumpukan Pintu Air\n" +
                "Normal → Bank Sampah · Medis → Pos Medis · Biohazard → Karantina", objectiveStyle);
        }

        private void DrawPauseMenu(RiverGameManager gm)
        {
            GUI.Box(new Rect(0f, 0f, Screen.width, Screen.height), GUIContent.none, dimStyle);
            float w = Mathf.Min(360f, Screen.width - 40f);
            float x = (Screen.width - w) * 0.5f;
            float y = Screen.height * 0.32f;
            GUI.Label(new Rect(x - 60f, y, w + 120f, 50f), "JEDA", menuTitleStyle);
            y += 70f;
            if (GUI.Button(new Rect(x, y, w, 44f), "Lanjut  [Esc]", menuButtonStyle)) gm.TogglePause();
            y += 52f;
            if (GUI.Button(new Rect(x, y, w, 44f), "Ulang", menuButtonStyle)) gm.RestartRun();
            y += 52f;
            if (GUI.Button(new Rect(x, y, w, 44f), "Keluar ke Menu", menuButtonStyle)) gm.ReturnToTitle();
        }

        // Canvas_SDGImpactReport shows the result; these buttons are its Main Lagi / Menu path until Niki adds them.
        private void DrawEndedBar(RiverGameManager gm)
        {
            float w = 220f;
            float y = Screen.height - 64f;
            // Niki's Canvas_SDGImpactReport has its own Main Lagi (Card/Btn_PlayAgain): then draw only Menu Utama, centred.
            bool reportHasRestart = sdgReport != null && sdgReport.transform.Find("Card/Btn_PlayAgain") != null;
            if (!reportHasRestart && GUI.Button(new Rect(Screen.width * 0.5f - w - 8f, y, w, 44f), "Main Lagi  [R]", menuButtonStyle)) gm.RestartRun();
            float menuX = reportHasRestart ? Screen.width * 0.5f - w * 0.5f : Screen.width * 0.5f + 8f;
            if (GUI.Button(new Rect(menuX, y, w, 44f), "Menu Utama", menuButtonStyle)) gm.ReturnToTitle();
        }

        private void EnsureStyles()
        {
            if (pillStyle != null) return;

            Texture2D vellumTex = MakeTex(new Color(0.957f, 0.949f, 0.925f, 0.94f));
            Texture2D dangerTex = MakeTex(new Color(0.710f, 0.055f, 0.435f, 0.95f));
            Texture2D tealTex = MakeTex(new Color(0.055f, 0.486f, 0.482f, 0.95f));
            Color ink = new Color(0.122f, 0.141f, 0.169f, 1f);

            pillStyle = new GUIStyle(GUI.skin.button)
            {
                fontSize = 12,
                fontStyle = FontStyle.Bold,
                alignment = TextAnchor.MiddleCenter
            };
            pillStyle.normal.background = vellumTex;
            pillStyle.normal.textColor = ink;
            pillStyle.hover.background = vellumTex;
            pillStyle.hover.textColor = ink;

            panelStyle = new GUIStyle(GUI.skin.box);
            panelStyle.normal.background = vellumTex;

            titleStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = 13,
                fontStyle = FontStyle.Bold
            };
            titleStyle.normal.textColor = ink;

            bodyStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = 11,
                wordWrap = true
            };
            bodyStyle.normal.textColor = ink;

            alertStyle = new GUIStyle(GUI.skin.box)
            {
                fontSize = 13,
                fontStyle = FontStyle.Bold,
                alignment = TextAnchor.MiddleCenter,
                wordWrap = true
            };
            alertStyle.normal.background = dangerTex;
            alertStyle.normal.textColor = Color.white;

            infoStyle = new GUIStyle(alertStyle);
            infoStyle.normal.background = tealTex;

            activeSlotStyle = new GUIStyle(GUI.skin.box);
            activeSlotStyle.normal.background = MakeTex(new Color(0.067f, 0.071f, 0.067f, 0.95f));
            activeSlotTextStyle = new GUIStyle(bodyStyle);
            activeSlotTextStyle.normal.textColor = new Color(0.957f, 0.949f, 0.925f, 1f);

            objectiveStyle = new GUIStyle(GUI.skin.box)
            {
                fontSize = 13,
                fontStyle = FontStyle.Bold,
                alignment = TextAnchor.MiddleLeft,
                wordWrap = true,
                padding = new RectOffset(10, 10, 4, 4)
            };
            objectiveStyle.normal.background = vellumTex;
            objectiveStyle.normal.textColor = ink;

            emptySlotTextStyle = new GUIStyle(bodyStyle);
            emptySlotTextStyle.normal.textColor = new Color(0.55f, 0.55f, 0.53f, 1f);

            dimStyle = new GUIStyle(GUI.skin.box);
            dimStyle.normal.background = MakeTex(new Color(0.067f, 0.071f, 0.067f, 0.72f));

            menuTitleStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = 34,
                fontStyle = FontStyle.Bold,
                alignment = TextAnchor.MiddleCenter
            };
            menuTitleStyle.normal.textColor = new Color(0.957f, 0.949f, 0.925f, 1f);

            menuButtonStyle = new GUIStyle(pillStyle) { fontSize = 16 };
        }

        private static Texture2D MakeTex(Color c)
        {
            Texture2D tex = new Texture2D(1, 1);
            tex.SetPixel(0, 0, c);
            tex.Apply();
            return tex;
        }

        private static bool WasStartPressed()
        {
#if ENABLE_INPUT_SYSTEM
            if (Keyboard.current != null && (Keyboard.current.enterKey.wasPressedThisFrame || Keyboard.current.numpadEnterKey.wasPressedThisFrame)) return true;
#endif
#if ENABLE_LEGACY_INPUT_MANAGER
            if (Input.GetKeyDown(KeyCode.Return) || Input.GetKeyDown(KeyCode.KeypadEnter)) return true;
#endif
            return false;
        }

        private static bool WasHelpPressed()
        {
#if ENABLE_INPUT_SYSTEM
            if (Keyboard.current != null && (Keyboard.current.hKey.wasPressedThisFrame || Keyboard.current.f1Key.wasPressedThisFrame)) return true;
#endif
#if ENABLE_LEGACY_INPUT_MANAGER
            if (Input.GetKeyDown(KeyCode.H) || Input.GetKeyDown(KeyCode.F1)) return true;
#endif
            return false;
        }
    }
}
