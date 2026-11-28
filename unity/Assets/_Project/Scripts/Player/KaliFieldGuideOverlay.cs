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
        private bool showGuide;
        private string toastMessage = string.Empty;
        private bool toastIsDanger;
        private float toastExpiresAt;
        private RiverGameManager subscribedManager;

        private GUIStyle pillStyle;
        private GUIStyle panelStyle;
        private GUIStyle titleStyle;
        private GUIStyle bodyStyle;
        private GUIStyle alertStyle;
        private GUIStyle infoStyle;

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
            if (WasHelpPressed())
            {
                showGuide = !showGuide;
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

            // 2. Compact [H] hint pill (bottom-left)
            Rect pillRect = new Rect(18f, Screen.height - 44f, 228f, 28f);
            if (GUI.Button(pillRect, showGuide ? "[H] Tutup Panduan Kontrol" : "[H] Kontrol & Pemilahan", pillStyle))
            {
                showGuide = !showGuide;
            }

            if (!showGuide) return;

            // 3. Toggleable Controls & Waste-Sorting Guide
            float gw = Mathf.Min(470f, Screen.width - 36f);
            float gh = 300f;
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
                "  Klik Kiri : Serok Sampah / Keruk Gunung (#13+ / Excavator)\n" +
                "  Scroll / [ ] : Ganti Alat Terbeli (#01-#20)\n\n" +
                "STASIUN & PEMILAHAN (SALAH STASIUN = DENDA!):\n" +
                "  [E] Setor Aman (otomatis jenis yg cocok) / Naik-Turun Perahu di Dermaga / Kopdes\n" +
                "  [1] Normal -> Bank Sampah [B]   |   [2] Medis -> Pos Medis B3 [M]\n" +
                "  [3] Biohazard -> Karantina [K]  |   Gudang Pengepul [P]: Beli semua (Penalti Trust!)\n" +
                "  Tahan [Q] 0.5s : Buang Kargo Darurat  |  Tahan [Shift+X] 1.5s : Flush (Sell-Lock)\n" +
                "  [R] (Saat Ending) : Ulang Permainan",
                bodyStyle);
            GUILayout.EndArea();
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
        }

        private static Texture2D MakeTex(Color c)
        {
            Texture2D tex = new Texture2D(1, 1);
            tex.SetPixel(0, 0, c);
            tex.Apply();
            return tex;
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
