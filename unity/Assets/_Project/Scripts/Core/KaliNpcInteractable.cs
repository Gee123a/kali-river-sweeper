using System.Collections.Generic;
using UnityEngine;
using KaliRiverSweeper.Player;

namespace KaliRiverSweeper.Core
{
    /// <summary>
    /// [E] talk to a kampung villager. Picks a state-based line, optionally sells es teh,
    /// and draws a fallback IMGUI speech box and "[E] Bicara" prompt.
    /// ponytail: IMGUI fallback only; a real UI can subscribe to OnSpoke.
    /// </summary>
    public sealed class KaliNpcInteractable : MonoBehaviour
    {
        public const float TalkRange = 2.5f;
        private const float MaxVerticalGap = 3f;
        private const float SpeechSeconds = 4f;

        public string npcName = "Warga";
        public bool isEsTehSeller;

        public static event System.Action<KaliNpcInteractable, string> OnSpoke;

        private static readonly List<KaliNpcInteractable> Registry = new List<KaliNpcInteractable>();
        private static KaliPlayerController player;
        private static float nextPlayerLookup;
        private static Camera cachedCamera;
        private static GUIStyle bubbleStyle;
        private static GUIStyle promptStyle;

        private readonly GUIContent speechContent = new GUIContent();
        private float speechUntil = -1f;

        private void OnEnable()
        {
            if (!Registry.Contains(this)) Registry.Add(this);
        }

        private void OnDisable()
        {
            Registry.Remove(this);
            speechUntil = -1f;
        }

        public static bool TryTalkNearest(Transform playerTf)
        {
            RiverGameManager gm = RiverGameManager.Instance;
            if (gm == null || gm.State != KaliGameState.Playing || playerTf == null) return false;

            KaliNpcInteractable npc = FindNearest(playerTf.position);
            if (npc == null) return false;

            npc.Talk(gm);
            return true;
        }

        public static string PickLine(RiverGameManager gm)
        {
            if (gm.isMonsoonStorm) return "Cepat naik! Banjir!";
            if (gm.communityTrust < 30) return "Jangan buang limbah ke Pengepul lagi ya.";
            if (gm.waterClarity < 0.4f) return "Bau sekali sungainya...";
            if (gm.communityTrust >= 70) return "Ini dia pahlawan kali kita.";
            return "Airnya mulai jernih, Nak!";
        }

        // Nearest enabled instance within TalkRange horizontally and MaxVerticalGap vertically.
        private static KaliNpcInteractable FindNearest(Vector3 from)
        {
            KaliNpcInteractable best = null;
            float bestSqr = TalkRange * TalkRange;
            for (int i = 0; i < Registry.Count; i++)
            {
                KaliNpcInteractable npc = Registry[i];
                Vector3 d = npc.transform.position - from;
                if (Mathf.Abs(d.y) > MaxVerticalGap) continue;
                d.y = 0f;
                float sqr = d.sqrMagnitude;
                if (sqr <= bestSqr)
                {
                    bestSqr = sqr;
                    best = npc;
                }
            }
            return best;
        }

        private void Talk(RiverGameManager gm)
        {
            string line;
            if (isEsTehSeller && !gm.isMonsoonStorm)
            {
                line = gm.TryBuyEsTeh()
                    ? "Ini es tehnya, segar! (-Rp 5.000, +30 HP)"
                    : "Es teh Rp 5.000, kalau lelah mampir ya.";
            }
            else
            {
                line = PickLine(gm);
            }

            speechContent.text = npcName + ": " + line;
            speechUntil = Time.unscaledTime + SpeechSeconds;
            OnSpoke?.Invoke(this, line);
        }

        private void OnGUI()
        {
            if (Event.current.type != EventType.Repaint) return;

            if (bubbleStyle == null)
            {
                bubbleStyle = new GUIStyle(GUI.skin.box) { fontSize = 16, wordWrap = true };
                bubbleStyle.normal.textColor = Color.white;
                promptStyle = new GUIStyle(GUI.skin.label) { fontSize = 18, alignment = TextAnchor.MiddleCenter };
                promptStyle.normal.textColor = Color.white;
            }

            if (speechUntil > Time.unscaledTime) DrawSpeechBubble();
            if (IsPromptTarget()) DrawPrompt();
        }

        private void DrawSpeechBubble()
        {
            Camera cam = GetCamera();
            if (cam == null) return;

            Vector3 sp = cam.WorldToScreenPoint(transform.position + Vector3.up * 2.1f);
            if (sp.z <= 0f) return;

            float w = Mathf.Min(bubbleStyle.CalcSize(speechContent).x + 12f, 320f);
            float h = bubbleStyle.CalcHeight(speechContent, w) + 4f;
            GUI.Box(new Rect(sp.x - w * 0.5f, Screen.height - sp.y - h, w, h), speechContent, bubbleStyle);
        }

        private bool IsPromptTarget()
        {
            RiverGameManager gm = RiverGameManager.Instance;
            if (gm == null || gm.State != KaliGameState.Playing) return false;

            if (player == null && Time.unscaledTime >= nextPlayerLookup)
            {
                player = FindObjectOfType<KaliPlayerController>();
                nextPlayerLookup = Time.unscaledTime + 1f;
            }
            if (player == null || player.IsInBoat || player.IsSwimming || player.HasNearbyHub) return false;

            return FindNearest(player.transform.position) == this;
        }

        private void DrawPrompt()
        {
            string label = isEsTehSeller
                ? "[E] Beli Es Teh Rp 5.000"
                : "[E] Bicara dengan " + npcName;
            GUI.Label(new Rect(Screen.width * 0.5f - 180f, Screen.height * 0.8f, 360f, 32f), label, promptStyle);
        }

        private static Camera GetCamera()
        {
            if (cachedCamera == null) cachedCamera = Camera.main;
            return cachedCamera;
        }
    }
}
