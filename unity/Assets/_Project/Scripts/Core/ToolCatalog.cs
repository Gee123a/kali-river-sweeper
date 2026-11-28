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

    // Spec C2: one hotbar slot per role (slot index = (int)role); each role is the only way to handle one kind of trash.
    public enum ToolRole
    {
        Serok = 0, // scoop/net: floating Normal bundles, batch grows with tier
        Capit = 1, // grabber: the only role that can pick up Medical
        Ganco = 2, // hook: the only role that can haul Biohazard; from #13 also dredges Gunung
        Garuk = 3  // rake/pump: the only role that can clear the Pintu Air barrier pile
    }

    [Serializable]
    public sealed class ToolDefinition
    {
        public int Index;
        public ToolRole Role;
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
            ToolRole role,
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
            Role = role;
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
    /// A tool unlocks at Kopdes once cumulative Rupiah reaches its UnlockRupiah (also its price; bought via RiverGameManager.BuyTool).
    /// </summary>
    public static class ToolCatalog
    {
        public const int SnakeGrabberIndex = 10;
        // Spec E: every tool's medical prick chance is halved from the table values below (#10 stays 0).
        public const float PrickChanceScale = 0.5f;

        // Spec C2 role ladders (indices kept 1..20). Prick only on Capit tools (per tier, #10 = 0%); Gunung dredge only on Ganco #13+.
        // Serok #1 2 5 6 7 9 12 14 · Capit #3 4 10 · Ganco #8 13 16 17 · Garuk #11 15 18 19 20. Each role has a Tier-0 starter <= Rp 6.000.
        private static readonly ToolDefinition[] Tools = new[]
        {
            new ToolDefinition(1,  ToolRole.Serok, "SM_Tool_SendokMakanBengkok",    "Sendok Makan Bengkok",     0, 0,      4.2f, 1, 0.45f, 0.00f, 0.00f, "+Z", "Starter improvised spoon: one bundle at a time."),
            new ToolDefinition(2,  ToolRole.Serok, "SM_Tool_GayungMandi",           "Gayung Mandi",             0, 3000,   4.5f, 2, 0.42f, 0.00f, 0.00f, "+Z", "Bath dipper for small bottles and cups."),
            new ToolDefinition(3,  ToolRole.Capit, "SM_Tool_CentongNasi",           "Centong Nasi",             0, 5000,   4.8f, 1, 0.39f, 0.50f, 0.00f, "+Z", "Rice paddle pinch for medical waste (high prick risk)."),
            new ToolDefinition(4,  ToolRole.Capit, "SM_Tool_GarpuTaman",            "Garpu Taman",              1, 22000,  5.0f, 1, 0.38f, 0.24f, 0.00f, "+Z", "Three-prong hand fork, safer medical pickup."),
            new ToolDefinition(5,  ToolRole.Serok, "SM_Tool_EmberCat5L",            "Ember Cat 5L",             0, 9000,   5.2f, 2, 0.36f, 0.00f, 0.00f, "-Z", "Wire-bailed 5L paint pail for shallow clusters."),
            new ToolDefinition(6,  ToolRole.Serok, "SM_Tool_GayungSaringanBambu",  "Gayung Saringan Bambu",    1, 18000,  6.2f, 3, 0.34f, 0.00f, 0.00f, "+Z", "Perforated dipper on 3m bamboo pole."),
            new ToolDefinition(7,  ToolRole.Serok, "SM_Tool_SerokanWaring3m",       "Serokan Waring 3m",        1, 30000,  6.8f, 3, 0.32f, 0.00f, 0.00f, "+Z", "Woven nylon hand net for bottle clusters."),
            new ToolDefinition(8,  ToolRole.Ganco, "SM_Tool_GancoBesi1Mata",        "Ganco Besi 1-Mata",        0, 6000,   7.0f, 1, 0.34f, 0.00f, 0.00f, "+Z", "Forged single-spike hook for biohazard drums."),
            new ToolDefinition(9,  ToolRole.Serok, "SM_Tool_EmberCat20L",           "Ember Cat 20L",            1, 45000,  7.4f, 4, 0.32f, 0.00f, 0.00f, "-Z", "Weighted 20L bucket on rope for eddy pockets."),
            new ToolDefinition(10, ToolRole.Capit, "SM_Tool_CapitanUlar",           "Capitan Ular",             1, 55000,  7.8f, 2, 0.28f, 0.00f, 0.00f, "+Z", "Long B3 snake grabber (0% medical prick risk!)."),
            new ToolDefinition(11, ToolRole.Garuk, "SM_Tool_AritSabitPanjang",      "Arit Sabit Panjang",       0, 6000,   5.5f, 2, 0.40f, 0.00f, 0.00f, "+Z", "Long sickle hacking the jammed Pintu Air pile."),
            new ToolDefinition(12, ToolRole.Serok, "SM_Tool_SerokanJumbo4_5m",      "Serokan Jumbo 4.5m",       2, 75000,  8.8f, 5, 0.26f, 0.00f, 0.00f, "+Z", "4.5m Petung bamboo jumbo net for dense drift."),
            new ToolDefinition(13, ToolRole.Ganco, "SM_Tool_GancoGandaWinch",       "Ganco Ganda Winch",        2, 65000,  9.0f, 2, 0.30f, 0.00f, 0.06f, "+Z", "Twin grappling hook + winch; can chip Gunung Sampah."),
            new ToolDefinition(14, ToolRole.Serok, "SM_Tool_JalaCincinLempar",      "Jala Cincin Lempar",       2, 120000, 9.6f, 6, 0.25f, 0.00f, 0.00f, "-Z", "Weighted cast ring net sweeping wide trash zones."),
            new ToolDefinition(15, ToolRole.Garuk, "SM_Tool_PompaSiphonManual",     "Pompa Siphon Manual",      2, 50000,  9.8f, 4, 0.24f, 0.00f, 0.00f, "-Z", "Manual PVC siphon lifting the barrier sludge."),
            new ToolDefinition(16, ToolRole.Ganco, "SM_Tool_BlokMagnet50kg",        "Blok Magnet 50kg",         3, 150000, 10.4f, 2, 0.24f, 0.00f, 0.08f, "-Z", "50kg salvage magnet hauling drums and Gunung scrap."),
            new ToolDefinition(17, ToolRole.Ganco, "SM_Tool_SenapanPanahTali",      "Senapan Panah Tali",       3, 210000, 11.2f, 3, 0.22f, 0.00f, 0.10f, "+Z", "Pneumatic tethered harpoon snaring fast drums."),
            new ToolDefinition(18, ToolRole.Garuk, "SM_Tool_PompaMesinRumput49cc",  "Pompa Mesin Rumput 49cc",  2, 110000, 11.6f, 5, 0.20f, 0.00f, 0.00f, "-Z", "49cc motorized vacuum pump for the barrier pile."),
            new ToolDefinition(19, ToolRole.Garuk, "SM_Tool_PenebasGergajiGanda",   "Penebas Gergaji Ganda",    3, 180000, 12.2f, 6, 0.18f, 0.00f, 0.00f, "+Z", "Twin reciprocating saw slasher clearing choke."),
            new ToolDefinition(20, ToolRole.Garuk, "SM_Tool_GarukSkimmerHidrolik",  "Garuk Skimmer Hidrolik",   3, 280000, 13.0f, 8, 0.16f, 0.00f, 0.00f, "+Z", "Hydraulic bow skimmer rake for mass cleanup.")
        };

        public static IReadOnlyList<ToolDefinition> AllTools => Tools;

        public static ToolDefinition GetTool(int index)
        {
            if (index < 1) return Tools[0];
            if (index > Tools.Length) return Tools[Tools.Length - 1];
            return Tools[index - 1];
        }

        // Highest index whose price is reached. Role ladders are not sorted by index, so use IsToolUnlocked for "can buy".
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

        public static string RoleName(ToolRole role) => role switch
        {
            ToolRole.Capit => "CAPIT",
            ToolRole.Ganco => "GANCO",
            ToolRole.Garuk => "GARUK",
            _ => "SEROK"
        };

        // Role that waste class needs (Normal: any role works, Serok is just much better at it).
        public static ToolRole RoleFor(WasteClass wc) => wc switch
        {
            WasteClass.Medical => ToolRole.Capit,
            WasteClass.Biohazard => ToolRole.Ganco,
            _ => ToolRole.Serok
        };
    }
}
