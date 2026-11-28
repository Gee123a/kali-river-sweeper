using System;
using System.Collections.Generic;

namespace KaliRiverSweeper.Core
{
    public enum WasteClass
    {
        Normal = 0,
        Medical = 1,
        Biohazard = 2
    }

    public enum DiscardStationType
    {
        BankSampah = 0,
        PosMedisB3 = 1,
        KarantinaBiohazard = 2,
        GudangPengepul = 3
    }

    [Serializable]
    public sealed class ToolDefinition
    {
        public int Index;
        public string MeshName;
        public string PrefabName;
        public string DisplayName;
        public int Tier;
        public int UnlockRupiah;
        public float Reach;
        public int BatchCount;
        public float Cooldown;
        public float MedicalPrickChance;
        public float GunungDamagePerSwing;
        public string HeadDir;
        public string RoleSummary;

        public ToolDefinition(
            int index,
            string meshName,
            string displayName,
            int tier,
            int unlockRupiah,
            float reach,
            int batchCount,
            float cooldown,
            float medicalPrickChance,
            float gunungDamagePerSwing,
            string headDir,
            string roleSummary)
        {
            Index = index;
            MeshName = meshName;
            PrefabName = meshName.StartsWith("SM_Tool_") ? "PF_Tool_" + meshName.Substring("SM_Tool_".Length) : "PF_" + meshName;
            DisplayName = displayName;
            Tier = tier;
            UnlockRupiah = unlockRupiah;
            Reach = reach;
            BatchCount = batchCount;
            Cooldown = cooldown;
            MedicalPrickChance = medicalPrickChance * ToolCatalog.PrickChanceScale;
            GunungDamagePerSwing = gunungDamagePerSwing;
            HeadDir = headDir;
            RoleSummary = roleSummary;
        }
    }

    /// <summary>
    /// Authoritative catalog of all 20 official JC tools matching origin/jc-excavator-tools SM_Tool_* specs.
    /// Cumulative Rupiah milestones unlock purchase availability at Kopdes (bought via RiverGameManager.BuyTool).
    /// </summary>
    public static class ToolCatalog
    {
        public const int SnakeGrabberIndex = 10;
        // Spec E: every tool's medical prick chance is halved from the table values below (#10 stays 0).
        public const float PrickChanceScale = 0.5f;

        private static readonly ToolDefinition[] Tools = new[]
        {
            new ToolDefinition(1,  "SM_Tool_SendokMakanBengkok",    "Sendok Makan Bengkok",     0, 0,      4.2f, 1, 0.45f, 0.60f, 0.00f, "+Z", "Starter improvised spoon (high medical prick risk)."),
            new ToolDefinition(2,  "SM_Tool_GayungMandi",           "Gayung Mandi",             0, 4000,   4.5f, 1, 0.42f, 0.55f, 0.00f, "+Z", "Bath dipper for small bottles and cups."),
            new ToolDefinition(3,  "SM_Tool_CentongNasi",           "Centong Nasi",             0, 8000,   4.8f, 1, 0.39f, 0.50f, 0.00f, "+Z", "Flat rice paddle skimming surface wrappers."),
            new ToolDefinition(4,  "SM_Tool_GarpuTaman",            "Garpu Taman",              0, 14000,  5.0f, 2, 0.38f, 0.45f, 0.00f, "+Z", "Three-prong hand fork snagging tangled bags."),
            new ToolDefinition(5,  "SM_Tool_EmberCat5L",            "Ember Cat 5L",             0, 20000,  5.2f, 2, 0.36f, 0.42f, 0.00f, "-Z", "Wire-bailed 5L paint pail for shallow clusters."),
            new ToolDefinition(6,  "SM_Tool_GayungSaringanBambu",  "Gayung Saringan Bambu",    1, 28000,  6.2f, 2, 0.34f, 0.35f, 0.00f, "+Z", "Perforated dipper on 3m bamboo pole."),
            new ToolDefinition(7,  "SM_Tool_SerokanWaring3m",       "Serokan Waring 3m",        1, 38000,  6.8f, 3, 0.32f, 0.30f, 0.00f, "+Z", "Woven nylon hand net for bottle clusters."),
            new ToolDefinition(8,  "SM_Tool_GancoBesi1Mata",        "Ganco Besi 1-Mata",        1, 50000,  7.0f, 2, 0.34f, 0.25f, 0.00f, "+Z", "Forged single-spike iron hook for heavy clumps."),
            new ToolDefinition(9,  "SM_Tool_EmberCat20L",           "Ember Cat 20L",            1, 64000,  7.4f, 3, 0.32f, 0.22f, 0.00f, "-Z", "Weighted 20L bucket on rope for eddy pockets."),
            new ToolDefinition(10, "SM_Tool_CapitanUlar",           "Capitan Ular",             1, 80000,  7.8f, 2, 0.28f, 0.00f, 0.00f, "+Z", "Long B3 snake grabber (0% medical prick risk!)."),
            new ToolDefinition(11, "SM_Tool_AritSabitPanjang",      "Arit Sabit Panjang",       2, 98000,  8.2f, 3, 0.28f, 0.14f, 0.00f, "+Z", "Long steel sickle slashing water hyacinth mats."),
            new ToolDefinition(12, "SM_Tool_SerokanJumbo4_5m",      "Serokan Jumbo 4.5m",       2, 118000, 8.8f, 4, 0.26f, 0.12f, 0.00f, "+Z", "4.5m Petung bamboo jumbo net for dense drift."),
            new ToolDefinition(13, "SM_Tool_GancoGandaWinch",       "Ganco Ganda Winch",        2, 140000, 9.0f, 3, 0.30f, 0.08f, 0.06f, "+Z", "Twin grappling hook + winch; can chip Gunung Sampah."),
            new ToolDefinition(14, "SM_Tool_JalaCincinLempar",      "Jala Cincin Lempar",       2, 165000, 9.6f, 4, 0.25f, 0.10f, 0.04f, "-Z", "Weighted cast ring net sweeping wide trash zones."),
            new ToolDefinition(15, "SM_Tool_PompaSiphonManual",     "Pompa Siphon Manual",      2, 192000, 9.8f, 4, 0.24f, 0.06f, 0.05f, "-Z", "Manual PVC bilge siphon lifting dense sludge."),
            new ToolDefinition(16, "SM_Tool_BlokMagnet50kg",        "Blok Magnet 50kg",         3, 222000, 10.4f, 4, 0.24f, 0.06f, 0.06f, "-Z", "50kg salvage magnet hauling submerged metal."),
            new ToolDefinition(17, "SM_Tool_SenapanPanahTali",      "Senapan Panah Tali",       3, 254000, 11.2f, 3, 0.22f, 0.04f, 0.08f, "+Z", "Pneumatic tethered harpoon snaring fast drums."),
            new ToolDefinition(18, "SM_Tool_PompaMesinRumput49cc",  "Pompa Mesin Rumput 49cc",  3, 288000, 11.6f, 5, 0.20f, 0.05f, 0.10f, "-Z", "49cc motorized vacuum impeller pump."),
            new ToolDefinition(19, "SM_Tool_PenebasGergajiGanda",   "Penebas Gergaji Ganda",    3, 324000, 12.2f, 5, 0.18f, 0.05f, 0.12f, "+Z", "Twin reciprocating saw slasher clearing choke."),
            new ToolDefinition(20, "SM_Tool_GarukSkimmerHidrolik",  "Garuk Skimmer Hidrolik",   3, 360000, 13.0f, 6, 0.16f, 0.03f, 0.18f, "+Z", "Hydraulic bow skimmer rake for mass cleanup.")
        };

        public static IReadOnlyList<ToolDefinition> AllTools => Tools;

        public static ToolDefinition GetTool(int index)
        {
            if (index < 1) return Tools[0];
            if (index > Tools.Length) return Tools[Tools.Length - 1];
            return Tools[index - 1];
        }

        public static int GetHighestUnlockedIndex(int cumulativeRupiah)
        {
            int highest = 1;
            for (int i = 0; i < Tools.Length; i++)
            {
                if (cumulativeRupiah >= Tools[i].UnlockRupiah)
                {
                    highest = Tools[i].Index;
                }
            }
            return highest;
        }

        public static bool IsSnakeGrabber(int index) => index == SnakeGrabberIndex;

        public static float GetEffectiveMedicalPrickChance(int equippedIndex, int highestUnlockedIndex)
        {
            if (highestUnlockedIndex >= SnakeGrabberIndex) return 0f;
            return GetTool(equippedIndex).MedicalPrickChance;
        }
    }
}
