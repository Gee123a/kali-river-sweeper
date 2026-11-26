using System.Globalization;
using KaliRiverSweeper.Core;
using TMPro;
using UnityEngine;

namespace KaliRiverSweeper.UI
{
    /// <summary>
    /// Shows Canvas_SDGImpactReport when RiverGameManager.OnEndingTriggered fires. The report reads
    /// the end-of-run stats at that moment, so it shows what happened in the run. Copy is Bahasa Indonesia.
    /// Hidden at rest. Subscription retries in Update until the manager exists; there is no per-frame gameplay poll.
    /// </summary>
    public sealed class SdgImpactReportController : MonoBehaviour
    {
        private static readonly CultureInfo Invariant = CultureInfo.InvariantCulture;

        private RiverGameManager manager;
        private CanvasGroup group;
        private TMP_Text headline;
        private TMP_Text body;
        private TMP_Text sdg63;
        private TMP_Text sdg115;
        private TMP_Text sdg141;
        private TMP_Text[] statValues;

        private void Awake()
        {
            group = GetComponent<CanvasGroup>();
            headline = Find<TMP_Text>("Card/TMP_EndingHeadline");
            body = Find<TMP_Text>("Card/TMP_EndingBody");
            sdg63 = Find<TMP_Text>("Card/TMP_Sdg63");
            sdg115 = Find<TMP_Text>("Card/TMP_Sdg115");
            sdg141 = Find<TMP_Text>("Card/TMP_Sdg141");

            statValues = new TMP_Text[7];
            for (int i = 0; i < statValues.Length; i++)
            {
                statValues[i] = Find<TMP_Text>("Card/Stats/Row_" + i + "/TMP_Value");
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
        }

        private void HandleEnding(GameEnding ending)
        {
            if (ending == GameEnding.None || manager == null) return;

            FillCopy(ending);
            FillStats();
            SetVisible(true);
        }

        private void FillCopy(GameEnding ending)
        {
            switch (ending)
            {
                case GameEnding.TrueSdgVictory:
                    SetText(headline, "SUNGAI KEMBALI BERSIH");
                    SetText(body, "Gunung Sampah habis, atau kamu bertahan sampai monsun selesai tanpa banjir fatal.");
                    SetText(sdg63, "SDG 6.3 · Air Bersih: TERCAPAI");
                    SetText(sdg115, "SDG 11.5 · Banjir Terkendali: TERCAPAI");
                    SetText(sdg141, "SDG 14.1 · Kehidupan Bawah Air: TERCAPAI");
                    break;
                case GameEnding.CompromisedOceanFlush:
                    SetText(headline, "PINTU AIR DIBUKA");
                    SetText(body, "Kampung selamat dari banjir, tapi sampah dibuang ke laut dan merusak ekosistem.");
                    SetText(sdg63, "SDG 6.3 · Air Bersih: SEBAGIAN");
                    SetText(sdg115, "SDG 11.5 · Banjir Terkendali: TERCAPAI");
                    SetText(sdg141, "SDG 14.1 · Kehidupan Bawah Air: GAGAL");
                    break;
                case GameEnding.FloodFail:
                    SetText(headline, "KAMPUNG TERENDAM");
                    SetText(body, "Air sungai melewati batas fatal sebelum sungai sempat dibersihkan.");
                    SetText(sdg63, "SDG 6.3 · Air Bersih: GAGAL");
                    SetText(sdg115, "SDG 11.5 · Banjir Terkendali: GAGAL");
                    SetText(sdg141, "SDG 14.1 · Kehidupan Bawah Air: BELUM SELESAI");
                    break;
                case GameEnding.HealthFail:
                    SetText(headline, "KAMU TUMBANG");
                    SetText(body, "HP habis sebelum sungai selesai dibersihkan. Coba lagi dan jaga kesehatanmu.");
                    SetText(sdg63, "SDG 6.3 · Air Bersih: BELUM SELESAI");
                    SetText(sdg115, "SDG 11.5 · Banjir Terkendali: BELUM SELESAI");
                    SetText(sdg141, "SDG 14.1 · Kehidupan Bawah Air: BELUM SELESAI");
                    break;
            }
        }

        // Stat order matches the rows built in KaliHudPrefabBuilder.BuildSdgReport.
        private void FillStats()
        {
            SetText(statValues[0], manager.recycledKg.ToString(Invariant) + " kg");
            SetText(statValues[1], manager.flushedKg.ToString(Invariant) + " kg");
            SetText(statValues[2], manager.medicalWasteSecured.ToString(Invariant));
            SetText(statValues[3], manager.biohazardWasteSecured.ToString(Invariant));
            SetText(statValues[4], "Rp " + FormatRupiah(manager.totalFinesPaid));
            SetText(statValues[5], manager.pengepulHazardDumped.ToString(Invariant));
            SetText(statValues[6], manager.communityTrust.ToString(Invariant));
        }

        private void SetVisible(bool visible)
        {
            if (group == null) return;
            group.alpha = visible ? 1f : 0f;
            group.blocksRaycasts = visible;
            group.interactable = visible;
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
