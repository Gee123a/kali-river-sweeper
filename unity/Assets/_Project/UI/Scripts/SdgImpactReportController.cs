using System.Globalization;
using KaliRiverSweeper.Core;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace KaliRiverSweeper.UI
{
    /// <summary>
    /// Shows Canvas_SDGImpactReport when RiverGameManager.OnEndingTriggered fires and auto-hides
    /// when a new run starts (activeEnding == GameEnding.None). Copy is Bahasa Indonesia.
    /// Hidden at rest. Subscription retries in Update until the manager exists; there is no per-frame gameplay poll.
    /// </summary>
    public sealed class SdgImpactReportController : MonoBehaviour
    {
        private static readonly CultureInfo Invariant = CultureInfo.InvariantCulture;

        private RiverGameManager manager;
        private CanvasGroup group;
        private TMP_Text headline;
        private TMP_Text body;
        private TMP_Text scoreRank;
        private TMP_Text sdg63;
        private TMP_Text sdg115;
        private TMP_Text sdg141;
        private TMP_Text[] statValues;
        private Button playAgainButton;

        private void Awake()
        {
            group = GetComponent<CanvasGroup>();
            headline = Find<TMP_Text>("Card/TMP_EndingHeadline");
            body = Find<TMP_Text>("Card/TMP_EndingBody");
            scoreRank = Find<TMP_Text>("Card/TMP_ScoreRank");
            sdg63 = Find<TMP_Text>("Card/TMP_Sdg63");
            sdg115 = Find<TMP_Text>("Card/TMP_Sdg115");
            sdg141 = Find<TMP_Text>("Card/TMP_Sdg141");

            statValues = new TMP_Text[10];
            for (int i = 0; i < statValues.Length; i++)
            {
                statValues[i] = Find<TMP_Text>("Card/Stats/Row_" + i + "/TMP_Value");
            }

            playAgainButton = Find<Button>("Card/Btn_PlayAgain");
            if (playAgainButton != null)
            {
                playAgainButton.onClick.AddListener(OnPlayAgainClicked);
            }

            SetVisible(false);
        }

        private void OnEnable()
        {
            TrySubscribe();
        }

        private void Start()
        {
            TrySubscribe();
        }

        private void OnDisable()
        {
            if (manager == null) return;

            manager.OnEndingTriggered -= HandleEnding;
            manager.OnStateChanged -= HandleStateChanged;
            manager = null;
        }

        private void Update()
        {
            if (manager == null) TrySubscribe();
        }

        private void TrySubscribe()
        {
            if (manager != null || RiverGameManager.Instance == null) return;

            manager = RiverGameManager.Instance;
            manager.OnEndingTriggered += HandleEnding;
            manager.OnStateChanged += HandleStateChanged;
            HandleStateChanged();
        }

        private void HandleStateChanged()
        {
            if (manager == null) return;
            if (manager.activeEnding == GameEnding.None && group != null && group.alpha > 0f)
            {
                SetVisible(false);
            }
        }

        private void HandleEnding(GameEnding ending)
        {
            if (manager == null) return;
            if (ending == GameEnding.None)
            {
                SetVisible(false);
                return;
            }

            FillCopy(ending);
            FillStats();
            SetVisible(true);
        }

        public void OnPlayAgainClicked()
        {
            SetVisible(false);
            if (manager != null)
            {
                manager.RestartRun();
            }
        }

        private void FillCopy(GameEnding ending)
        {
            SdgScorecard scorecard = manager.ComputeSdgScorecard();
            SetText(scoreRank, "RANK " + scorecard.Rank);

            switch (ending)
            {
                case GameEnding.TrueSdgVictory:
                    SetText(headline, "SUNGAI KEMBALI BERSIH");
                    SetText(body, "Gunung Sampah habis, atau kamu bertahan sampai monsun selesai tanpa banjir fatal.");
                    break;
                case GameEnding.PartialSurvival:
                    SetText(headline, "BADAI TERLEWATI · GUNUNG TERSISA");
                    SetText(body, "Kampung bertahan melewati badai monsun, tetapi Gunung Sampah di hulu masih tersisa.");
                    break;
                case GameEnding.CompromisedOceanFlush:
                    SetText(headline, "PINTU AIR DIBUKA");
                    SetText(body, "Kampung selamat dari banjir, tapi sampah dibuang ke laut dan merusak ekosistem.");
                    break;
                case GameEnding.FloodFail:
                    SetText(headline, "KAMPUNG TERENDAM");
                    SetText(body, "Air sungai melewati batas fatal sebelum sungai sempat dibersihkan.");
                    break;
                case GameEnding.HealthFail:
                    SetText(headline, "KAMU TUMBANG");
                    SetText(body, "HP habis sebelum sungai selesai dibersihkan. Coba lagi dan jaga kesehatanmu.");
                    break;
            }

            SetText(sdg63, "SDG 6.3 · Air Bersih: " + (scorecard.Sdg63Pass ? "TERCAPAI" : "BELUM TERCAPAI"));
            SetText(sdg115, "SDG 11.5 · Banjir Terkendali: " + (scorecard.Sdg115Pass ? "TERCAPAI" : "BELUM TERCAPAI"));
            SetText(sdg141, "SDG 14.1 · Ekosistem Laut: " + (scorecard.Sdg141Pass ? "TERCAPAI" : "BELUM TERCAPAI"));
        }

        // Stat order matches the rows built in KaliHudPrefabBuilder.BuildSdgReport.
        private void FillStats()
        {
            int ownedTools = 0;
            for (int i = 1; i <= 20; i++)
            {
                if (manager.IsToolOwned(i)) ownedTools++;
            }

            SetText(statValues[0], manager.recycledKg.ToString(Invariant) + " kg");
            SetText(statValues[1], manager.flushedKg.ToString(Invariant) + " kg");
            SetText(statValues[2], manager.medicalWasteSecured.ToString(Invariant));
            SetText(statValues[3], manager.biohazardWasteSecured.ToString(Invariant));
            SetText(statValues[4], "Rp " + FormatRupiah(manager.totalFinesPaid));
            SetText(statValues[5], manager.pengepulHazardDumped.ToString(Invariant));
            SetText(statValues[6], manager.communityTrust.ToString(Invariant));
            SetText(statValues[7], "Rp " + FormatRupiah(manager.rupiah));
            SetText(statValues[8], ownedTools.ToString(Invariant) + " / 20");
            SetText(statValues[9], manager.infectionIncidents.ToString(Invariant));
        }

        private void SetVisible(bool visible)
        {
            if (group == null) return;
            group.alpha = visible ? 1f : 0f;
            group.blocksRaycasts = visible;
            group.interactable = visible;
            if (visible)
            {
                Cursor.lockState = CursorLockMode.None;
                Cursor.visible = true;
            }
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

        private static void SetText(TMP_Text target, string value)
        {
            if (target != null) target.text = value;
        }
    }
}
