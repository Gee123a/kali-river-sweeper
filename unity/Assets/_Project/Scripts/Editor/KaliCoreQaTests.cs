#if UNITY_EDITOR
using System;
using System.Collections.Generic;
using System.Reflection;
using UnityEditor;
using UnityEngine;
using KaliRiverSweeper.Core;
using KaliRiverSweeper.Player;

namespace KaliRiverSweeper.Editor
{
    public static class KaliCoreQaTests
    {
        private sealed class QaContext : IDisposable
        {
            public readonly RiverGameManager Manager;
            private readonly RiverGameManager prevInstance;
            private readonly List<GameObject> tempObjects = new List<GameObject>();
            private readonly List<(GunungNodeController node, float health, Vector3 scale, Vector3 pos, bool active)> savedNodes =
                new List<(GunungNodeController, float, Vector3, Vector3, bool)>();

            // RestartRun() reaches scene objects via FindObjectOfType (player teleport, Gunung restore), so snapshot them all.
            private readonly List<(Transform t, Vector3 pos, Quaternion rot)> savedPlayers = new List<(Transform, Vector3, Quaternion)>();

            public QaContext(bool isolateSceneGunungNodes = false)
            {
                prevInstance = RiverGameManager.Instance;
                SetManagerInstance(null);

                foreach (GunungNodeController node in UnityEngine.Object.FindObjectsOfType<GunungNodeController>(true))
                {
                    savedNodes.Add((node, node.nodeHealth, node.transform.localScale, node.transform.position, node.gameObject.activeSelf));
                    if (isolateSceneGunungNodes) node.nodeHealth = 0f;
                }
                foreach (KaliPlayerController player in UnityEngine.Object.FindObjectsOfType<KaliPlayerController>(true))
                {
                    savedPlayers.Add((player.transform, player.transform.position, player.transform.rotation));
                }

                GameObject go = Track(new GameObject("QA_RiverGameManager"));
                Manager = go.AddComponent<RiverGameManager>();
                InvokeNonPublic(Manager, "Awake");
            }

            public GameObject Track(GameObject go)
            {
                tempObjects.Add(go);
                return go;
            }

            public void Dispose()
            {
                for (int i = tempObjects.Count - 1; i >= 0; i--)
                {
                    if (tempObjects[i] != null) UnityEngine.Object.DestroyImmediate(tempObjects[i]);
                }

                for (int i = 0; i < savedNodes.Count; i++)
                {
                    var s = savedNodes[i];
                    if (s.node == null) continue;
                    s.node.nodeHealth = s.health;
                    s.node.transform.localScale = s.scale;
                    s.node.transform.position = s.pos;
                    s.node.gameObject.SetActive(s.active);
                }

                for (int i = 0; i < savedPlayers.Count; i++)
                {
                    var s = savedPlayers[i];
                    if (s.t == null) continue;
                    s.t.SetPositionAndRotation(s.pos, s.rot);
                }

                SetManagerInstance(prevInstance);
            }

            private static void SetManagerInstance(RiverGameManager value)
            {
                PropertyInfo prop = typeof(RiverGameManager).GetProperty("Instance", BindingFlags.Public | BindingFlags.Static);
                prop?.SetValue(null, value);
            }
        }

        [MenuItem("KALI/QA/Run Core Verification")]
        public static void RunCoreVerification()
        {
            Action[] suite = new Action[]
            {
                VerifyWaterThresholdsAndAntiDeadlockDump,
                VerifyWastePickupStationsFinesAndPengepul,
                VerifyBiohazardDotAndHealthFail,
                VerifyToolCatalogAndUnlocks,
                VerifyEventsGunungBreachAndFourEndings,
                VerifyRiverMathSpawnerAndComponents,
                VerifyChildColliderLookupAndSingleEndingGuard,
                VerifyPrefabHitboxProportions,
                VerifyDermagaRiverPortLimits,
                VerifyTask4dAnd4fUxContracts,
                VerifySwimmingStaminaAndDrowning,
                VerifyDayNightCycle,
                VerifyKampungRowsAndMapEdge,
                VerifyAmbientRiverNpcs
            };

            assertCount = 0;
            for (int i = 0; i < suite.Length; i++)
            {
                suite[i]();
            }

            Debug.Log($"[KALI QA] PASS: {suite.Length}/{suite.Length} core verification suites passed ({assertCount} Assert calls).");
        }

        private static void VerifyWaterThresholdsAndAntiDeadlockDump()
        {
            using (QaContext ctx = new QaContext())
            {
                RiverGameManager gm = ctx.Manager;
                AssertApprox(-0.25f, RiverGameManager.BaseWaterLevelY, 0.0001f, "BaseWaterLevelY");
                AssertApprox(0.020f, RiverGameManager.WaterRisePerTrashUnit, 0.0001f, "WaterRisePerTrashUnit");
                Assert(gm.TotalTrashInRiver == 4, "Initial TotalTrashInRiver should be 4");
                AssertApprox(-0.17f, gm.currentWaterLevelY, 0.001f, "Initial water level");
                Assert(!gm.IsBankOverflowing && !gm.IsSellLocked, "Initial water must not overflow or lock sell");

                gm.RegisterActiveTrash(78); // 4 + 78 = 82 -> 1.39f
                AssertApprox(1.39f, gm.currentWaterLevelY, 0.001f, "82 trash water level");
                Assert(!gm.IsBankOverflowing, "82 trash must not overflow (< 1.40f)");

                gm.RegisterActiveTrash(1); // 83 -> 1.41f
                AssertApprox(1.41f, gm.currentWaterLevelY, 0.001f, "83 trash water level");
                Assert(gm.IsBankOverflowing && !gm.IsSellLocked, "83 trash must trigger IsBankOverflowing only");

                gm.RegisterActiveTrash(23); // 106 -> 1.87f >= 1.85f
                Assert(gm.IsSellLocked, "106 trash (>= 1.85f) must trigger IsSellLocked");

                Assert(gm.TryPickupWaste(WasteClass.Normal, 1), "Pickup normal under capacity");
                Assert(gm.TryPickupWaste(WasteClass.Biohazard, 1), "Pickup biohazard under capacity");
                gm.biohazardExposureTimer = 7f;
                Assert(gm.DiscardWasteAtStation(DiscardStationType.BankSampah, WasteClass.Normal) == 0, "BankSampah locked during Sell-Lock");
                Assert(gm.SellAllAtPengepul() == 0, "Pengepul locked during Sell-Lock");

                int trustBeforeDump = gm.communityTrust;
                int dropped = gm.DumpCargoOnHighGround();
                Assert(dropped == 2 && gm.cargoCount == 0, "DumpCargoOnHighGround clears all cargo");
                AssertApprox(0f, gm.biohazardExposureTimer, 0.001f, "Dump resets biohazard timer");
                Assert(gm.communityTrust == trustBeforeDump, "Emergency dump during Sell-Lock has zero trust penalty");

                gm.UnregisterActiveTrash(102); // Drop back to 4 -> safe water level
                Assert(!gm.IsSellLocked, "Water level drops below sell lock");
                gm.TryPickupWaste(WasteClass.Biohazard, 2);
                int trustBeforePenaltyDump = gm.communityTrust;
                gm.DumpCargoOnHighGround();
                Assert(gm.communityTrust == trustBeforePenaltyDump - 4, "Non-emergency hazard dump deducts 2 trust per hazard unit");

                GameEnding firedEnding = GameEnding.None;
                gm.OnEndingTriggered += e => firedEnding = e;
                gm.AddPiledTrash(131); // 4 + 131 = 135 -> 2.45000005f >= 2.45f
                Assert(gm.currentWaterLevelY >= gm.fatalFloodWaterY, "135 trash reaches fatalFloodWaterY (2.45f)");
                InvokeNonPublic(gm, "Update");
                Assert(gm.activeEnding == GameEnding.FloodFail && firedEnding == GameEnding.FloodFail, "FloodFail triggered at >= 2.45f");
            }
        }

        private static void VerifyWastePickupStationsFinesAndPengepul()
        {
            using (QaContext ctx = new QaContext())
            {
                RiverGameManager gm = ctx.Manager;
                Assert(RiverTrashItem.InferWasteClassFromName("PF_Trash_AquaBottle_600ml") == WasteClass.Normal, "Infer Normal");
                Assert(RiverTrashItem.InferWasteClassFromName("PF_Trash_MedicalBag") == WasteClass.Medical, "Infer Medical");
                Assert(RiverTrashItem.InferWasteClassFromName("PF_Trash_BiohazardDrum") == WasteClass.Biohazard, "Infer Biohazard");

                gm.cargoCapacity = 8;
                Assert(gm.TryPickupWaste(WasteClass.Normal, 2), "Pickup 2 Normal");
                Assert(gm.TryPickupWaste(WasteClass.Biohazard, 1), "Pickup 1 Biohazard");
                Assert(gm.cargoCount == 3 && gm.normalCargo == 2 && gm.biohazardCargo == 1, "3-class cargo split");

                // Correct Normal at BankSampah (Rp 4,000 * 2 = 8,000)
                int payoutNormal = gm.DiscardWasteAtStation(DiscardStationType.BankSampah, WasteClass.Normal);
                Assert(payoutNormal == 8000 && gm.rupiah == 8000 && gm.recycledKg == 10, "BankSampah normal payout");

                // Spec B auto-sort: [E] at Bank Sampah never touches Biohazard and never fines
                int trustBefore = gm.communityTrust;
                string preview = gm.GetDepositPreview(DiscardStationType.BankSampah);
                Assert(preview.Contains("Bank Sampah menerima: Normal") && preview.Contains("Biohazard ×1 → bawa ke Karantina"), "Deposit preview tells truth: " + preview);
                gm.TryPickupWaste(WasteClass.Normal, 1); // keep trust < 70 so later payouts stay at 1.0x
                Assert(gm.GetDepositPreview(DiscardStationType.BankSampah).StartsWith("Bank Sampah menerima: Normal ×1 → Rp 4.000"), "Deposit preview shows qty and Rp");
                int legalOut = gm.DiscardLegalAtStation(DiscardStationType.BankSampah);
                Assert(legalOut == 4000 && gm.normalCargo == 0 && gm.biohazardCargo == 1, "Deposit takes only Normal, Biohazard stays in cargo");
                Assert(gm.totalFinesPaid == 0 && gm.wrongDiscardCount == 0 && gm.communityTrust > trustBefore, "Auto-sort deposit has no fine or trust loss");
                Assert(gm.DiscardLegalAtStation(DiscardStationType.BankSampah) == 0 && gm.biohazardCargo == 1 && gm.totalFinesPaid == 0, "Deposit with nothing accepted is a no-op, no fine");
                gm.biohazardCargo = 0;
                InvokeNonPublic(gm, "SyncCargoTotal");

                // Correct Normal at BankSampah (Rp 4,000)
                gm.trashBoomActive = true;
                gm.TryPickupWaste(WasteClass.Normal, 1);
                Assert(gm.DiscardWasteAtStation(DiscardStationType.BankSampah, WasteClass.Normal) == 4000, "BankSampah single normal payout");

                // Correct Karantina Biohazard (Rp 14,000)
                gm.TryPickupWaste(WasteClass.Biohazard, 1);
                gm.biohazardExposureTimer = 5f;
                int payoutBio = gm.DiscardWasteAtStation(DiscardStationType.KarantinaBiohazard, WasteClass.Biohazard);
                Assert(payoutBio == 14000 && gm.biohazardWasteSecured == 1 && gm.biohazardExposureTimer == 0f, "Karantina Biohazard payout & timer reset");

                // Correct Pos Medis B3 (Rp 9,000 + 10 HP heal)
                gm.playerHealth = 70f;
                gm.TryPickupWaste(WasteClass.Medical, 1);
                float hpBeforeHeal = gm.playerHealth;
                int payoutMed = gm.DiscardWasteAtStation(DiscardStationType.PosMedisB3, WasteClass.Medical);
                Assert(payoutMed == 9000 && gm.medicalWasteSecured == 1, "Pos Medis B3 payout");
                AssertApprox(hpBeforeHeal + 10f, gm.playerHealth, 0.01f, "Pos Medis B3 +10 HP heal");

                // Pengepul bulk sell: 1 Normal (2k) + 1 Medical (3k) + 1 Biohazard (4.5k) = 9.5k, -20 Trust
                gm.TryPickupWaste(WasteClass.Normal, 1);
                gm.TryPickupWaste(WasteClass.Medical, 1);
                gm.TryPickupWaste(WasteClass.Biohazard, 1);
                int trustBeforePengepul = gm.communityTrust;
                int pengepulPay = gm.SellAllAtPengepul();
                Assert(pengepulPay == 9500 && gm.pengepulHazardDumped == 2, "SellAllAtPengepul payout & hazard counter");
                Assert(gm.communityTrust == trustBeforePengepul - 20 && gm.cargoCount == 0, "SellAllAtPengepul trust penalty & cargo clear");
                gm.TryPickupWaste(WasteClass.Medical, 1);
                Assert(gm.GetDepositPreview(DiscardStationType.GudangPengepul).Contains("-8 Trust"), "Pengepul preview warns about hazard trust loss");
                Assert(gm.DiscardLegalAtStation(DiscardStationType.GudangPengepul) == 3000 && gm.cargoCount == 0, "Pengepul still sells all");
            }
        }

        private static void VerifyBiohazardDotAndHealthFail()
        {
            using (QaContext ctx = new QaContext())
            {
                RiverGameManager gm = ctx.Manager;

                // #10 Capitan Ular guarantees 0% medical prick risk once bought & equipped
                InvokeNonPublic(gm, "AddEarnings", 80000);
                Assert(gm.equippedToolIndex == 1, "AddEarnings does not auto-equip #10 Capitan Ular");
                Assert(gm.BuyTool(ToolCatalog.SnakeGrabberIndex) && gm.equippedToolIndex == ToolCatalog.SnakeGrabberIndex, "BuyTool #10 Capitan Ular equips it");
                AssertApprox(0f, gm.EquippedTool.MedicalPrickChance, 0.0001f, "#10 Capitan Ular 0% prick chance");

                gm.cargoCapacity = 25;
                Assert(gm.TryPickupWaste(WasteClass.Medical, 20), "Pickup 20 medical with Capitan Ular");
                Assert(gm.infectionIncidents == 0 && gm.playerHealth == gm.maxPlayerHealth, "Zero pricks with Capitan Ular");
                gm.DumpCargoOnHighGround();

                // SecureMedicalWaste contract
                int trustBefore = gm.communityTrust;
                Assert(gm.SecureMedicalWaste(true) && gm.medicalWasteSecured == 1 && gm.communityTrust == trustBefore + 12, "SecureMedicalWaste(true)");
                Assert(!gm.SecureMedicalWaste(false) && gm.infectionIncidents == 1, "SecureMedicalWaste(false) causes prick");

                // Biohazard DoT grace timer & HealthFail ending
                gm.TryPickupWaste(WasteClass.Biohazard, 2);
                gm.biohazardExposureTimer = 9.5f;
                Assert(!gm.IsBiohazardDotActive, "DoT inactive before 10s grace");
                AssertApprox(0.5f, gm.BiohazardGraceRemaining, 0.001f, "BiohazardGraceRemaining = 0.5s");

                gm.biohazardExposureTimer = 10.0f;
                Assert(gm.IsBiohazardDotActive, "DoT active at >= 10s grace");
                AssertApprox(0f, gm.BiohazardGraceRemaining, 0.001f, "BiohazardGraceRemaining = 0s");

                GameEnding healthEnding = GameEnding.None;
                gm.OnEndingTriggered += e => healthEnding = e;
                InvokeNonPublic(gm, "ApplyPlayerDamage", gm.playerHealth + 1f, true);
                Assert(gm.playerHealth == 0f && gm.activeEnding == GameEnding.HealthFail && healthEnding == GameEnding.HealthFail, "HealthFail triggered at 0 HP");
            }
        }

        private static void VerifyToolCatalogAndUnlocks()
        {
            var tools = ToolCatalog.AllTools;
            Assert(tools.Count == 20, "ToolCatalog must have exactly 20 tools");
            int prevCost = -1;
            for (int i = 0; i < tools.Count; i++)
            {
                Assert(tools[i].Index == i + 1, $"Tool index sequential at {i + 1}");
                Assert(tools[i].UnlockRupiah > prevCost, $"UnlockRupiah strictly increasing at #{i + 1}");
                prevCost = tools[i].UnlockRupiah;
                if (tools[i].Index < 13) Assert(tools[i].GunungDamagePerSwing == 0f, $"Tool #{i + 1} cannot chip Gunung");
                else Assert(tools[i].GunungDamagePerSwing > 0f, $"Tool #{i + 1} can chip Gunung");
            }

            Assert(ToolCatalog.GetHighestUnlockedIndex(0) == 1, "Threshold 0 -> #01");
            Assert(ToolCatalog.GetHighestUnlockedIndex(3999) == 1, "Threshold 3,999 -> #01");
            Assert(ToolCatalog.GetHighestUnlockedIndex(4000) == 2, "Threshold 4,000 -> #02");
            Assert(ToolCatalog.GetHighestUnlockedIndex(28000) == 6, "Threshold 28,000 -> #06");
            Assert(ToolCatalog.GetHighestUnlockedIndex(80000) == 10, "Threshold 80,000 -> #10");
            Assert(ToolCatalog.GetHighestUnlockedIndex(140000) == 13, "Threshold 140,000 -> #13");
            Assert(ToolCatalog.GetHighestUnlockedIndex(360000) == 20, "Threshold 360,000 -> #20");

            using (QaContext ctx = new QaContext())
            {
                RiverGameManager gm = ctx.Manager;
                int unlockedCount = 0;
                int equipChangedCount = 0;
                gm.OnToolUnlocked += _ => unlockedCount++;
                gm.OnEquippedToolChanged += _ => equipChangedCount++;

                InvokeNonPublic(gm, "AddEarnings", 30000);
                Assert(gm.highestUnlockedToolIndex == 6 && gm.equippedToolIndex == 1 && gm.galahUnlocked, "30k unlocks #06 + galah without auto-equip");
                Assert(unlockedCount == 5 && equipChangedCount == 0, "Fired OnToolUnlocked for #2..#6 without auto-equip");

                Assert(gm.BuyTool(6) && gm.equippedToolIndex == 6 && gm.IsToolOwned(6), "BuyTool #06 spends 28k and equips it");
                Assert(!gm.BuyTool(6), "BuyTool blocks duplicate purchase");
                Assert(!gm.BuyTool(20), "BuyTool blocks purchase when rupiah is insufficient");
                Assert(gm.rupiah == 2000 && gm.cumulativeEarnings == 30000 && gm.highestUnlockedToolIndex == 6, "Buying tool spends rupiah only");


                Assert(gm.SelectTool(1) && gm.equippedToolIndex == 1, "SelectTool #01");
                Assert(!gm.SelectTool(20) && gm.equippedToolIndex == 1, "SelectTool rejects unowned tool #20");
                gm.CycleTool(-1);
                Assert(gm.equippedToolIndex == 6 && gm.activeSlot == 1, "CycleTool wraps backwards over non-empty hotbar slots");
                gm.CycleTool(1);
                Assert(gm.equippedToolIndex == 1 && gm.activeSlot == 0, "CycleTool wraps forwards to slot 1 (#01)");
                int hotbarEvents = 0;
                gm.OnHotbarChanged += () => hotbarEvents++;
                Assert(gm.SelectSlot(1) && gm.equippedToolIndex == 6 && hotbarEvents == 1, "SelectSlot(1) equips #06 and fires OnHotbarChanged");
                Assert(!gm.SelectSlot(2) && !gm.SelectSlot(4) && gm.equippedToolIndex == 6, "SelectSlot rejects empty / out-of-range slots");

                InvokeNonPublic(gm, "AddEarnings", 28000);
                Assert(gm.BuyKampungBins() && gm.kampungBinsInstalled, "Spend 30k on Kampung Bins");
            }

            using (QaContext ctx = new QaContext())
            {
                RiverGameManager gm = ctx.Manager;
                InvokeNonPublic(gm, "AddEarnings", 30000);
                gm.BuyTool(6);
                // Spec C hotbar: buying fills the first empty slot at full price; when full, a chosen slot is traded in for 50%
                gm.rupiah = 500000;
                Assert(!gm.BuyTool(7), "BuyTool blocks tools not yet unlocked by cumulative earnings");
                Assert(gm.GetToolPrice(7) == 38000, "Empty-slot purchase costs the full catalog price");
                InvokeNonPublic(gm, "AddEarnings", 30000); // cumulative 60k -> #08 open
                int before = gm.rupiah;
                Assert(gm.BuyTool(7) && before - gm.rupiah == 38000 && gm.hotbar[2] == 7 && gm.activeSlot == 2, "BuyTool #07 goes into empty slot 3");
                Assert(gm.BuyTool(8) && gm.hotbar[3] == 8 && gm.IsHotbarFull, "BuyTool #08 fills slot 4");
                InvokeNonPublic(gm, "AddEarnings", 10000); // cumulative 70k -> #09 open
                before = gm.rupiah;
                Assert(!gm.BuyTool(9) && gm.rupiah == before && !gm.IsToolOwned(9), "Full hotbar: BuyTool without trade-in slot is refused");
                Assert(gm.GetTradeInCredit(1) == 14000 && gm.GetToolPrice(9, 1) == 64000 - 14000, "Trade-in credit = 50% of #06 (28k)");
                Assert(gm.BuyTool(9, 1) && before - gm.rupiah == 50000, "Trade-in charges price minus 50% credit");
                Assert(gm.hotbar[1] == 9 && !gm.IsToolOwned(6) && gm.equippedToolIndex == 9 && gm.activeSlot == 1, "Trade-in removes #06 and equips #09 in its slot");
                gm.RestartRun();
                Assert(gm.hotbar[0] == 1 && gm.hotbar[1] == 0 && gm.hotbar[2] == 0 && gm.hotbar[3] == 0 && gm.activeSlot == 0 && gm.equippedToolIndex == 1, "RestartRun resets hotbar to #01 only");

                // Task 4L: Trash Boom pays rupiah only (no milestone progress) and drains piled trash
                int cumBefore = gm.cumulativeEarnings;
                int piledBefore = gm.piledRiverTrashCount;
                gm.trashBoomActive = true;
                before = gm.rupiah;
                InvokeNonPublic(gm, "Tick", RiverGameManager.BoomIntervalSeconds + 0.01f);
                Assert(gm.rupiah - before == RiverGameManager.BoomPayoutRupiah && gm.cumulativeEarnings == cumBefore, "Trash Boom payout is rupiah-only");
                Assert(gm.piledRiverTrashCount == Mathf.Max(0, piledBefore - 1), "Trash Boom drains one piled unit per cycle");
            }

            // Task 4L: monsoon surge adds upstream piled trash during the storm and escalates
            using (QaContext ctx = new QaContext())
            {
                RiverGameManager gm = ctx.Manager;
                gm.monsoonCountdownRemaining = gm.monsoonStormTriggerRemaining - 0.01f;
                int piled0 = gm.piledRiverTrashCount;
                for (int i = 0; i < 90; i++) InvokeNonPublic(gm, "Tick", 0.1f); // early storm: 9s
                int earlyAdded = gm.piledRiverTrashCount - piled0;
                Assert(gm.isMonsoonStorm && earlyAdded == 1, "Early storm surge adds ~1 unit per 8s (got " + earlyAdded + ")");
                gm.monsoonCountdownRemaining = 10f;
                int piled1 = gm.piledRiverTrashCount;
                for (int i = 0; i < 90; i++) InvokeNonPublic(gm, "Tick", 0.1f); // late storm: 9s
                int lateAdded = gm.piledRiverTrashCount - piled1;
                Assert(lateAdded >= 2, "Late storm surge escalates (got " + lateAdded + " in 9s)");
            }

            // Shop / economy API
            Assert(RiverGameManager.KampungBinsCost == 30000, "Kampung Bins cost is 30,000");
            Assert(RiverGameManager.GetUpgradeCost(UpgradeTier.Galah4m) == 20000, "Galah 4m upgrade cost 20,000");
            Assert(RiverGameManager.GetUpgradeCost(UpgradeTier.WoodenSampan) == 40000, "Wooden Sampan upgrade cost 40,000");
            Assert(RiverGameManager.GetUpgradeCost(UpgradeTier.TrashBoom) == 75000, "Trash Boom upgrade cost 75,000");
            Assert(RiverGameManager.GetUpgradeCost(UpgradeTier.AmphibiousExcavator) == 120000, "Amphibious Excavator upgrade cost 120,000");

            using (QaContext shopCtx = new QaContext())
            {
                RiverGameManager gm = shopCtx.Manager;
                Assert(gm.IsToolUnlocked(1) && !gm.IsToolUnlocked(20), "IsToolUnlocked: #01 open, #20 locked at 0 earnings");

                Vector3 kopdesPos = new Vector3(6000f, 6000f, 6000f);
                MakeStation(shopCtx, "Koperasi Desa (Kopdes)", kopdesPos);

                GameObject shopPlayerGo = shopCtx.Track(new GameObject("QA_ShopPlayer"));
                shopPlayerGo.AddComponent<CharacterController>();
                KaliPlayerController shopPlayer = shopPlayerGo.AddComponent<KaliPlayerController>();
                PlaceAtServicePoint(shopPlayerGo, kopdesPos);

                gm.rupiah = 50000;
                int shopEvents = 0;
                int shopClosed = 0;
                shopPlayer.OnShopRequested += () => shopEvents++;
                shopPlayer.OnShopClosed += () => shopClosed++;
                InvokeNonPublic(shopPlayer, "TryInteractWithNearbyHub");
                Assert(shopEvents == 1 && shopPlayer.IsShopOpen && gm.rupiah == 50000, "Kopdes [E] at service point opens the shop without spending rupiah");
                shopPlayer.CloseShop();
                Assert(!shopPlayer.IsShopOpen && shopClosed == 1, "CloseShop closes and fires OnShopClosed");
            }
        }

        private static void VerifyEventsGunungBreachAndFourEndings()
        {
            // 1. OnWaterSplash, OnGunungTierBreached, and TrueSdgVictory via Clean Breach
            using (QaContext ctx = new QaContext(isolateSceneGunungNodes: true))
            {
                RiverGameManager gm = ctx.Manager;
                Vector3 splashPos = Vector3.zero;
                int splashCount = 0;
                gm.OnWaterSplash += p => { splashCount++; splashPos = p; };
                Vector3 expectedSplash = new Vector3(1.5f, -0.17f, -12f);
                gm.NotifyWaterSplash(expectedSplash);
                Assert(splashCount == 1 && splashPos == expectedSplash, "OnWaterSplash forwards worldPos");

                // Create one isolated GunungNodeController
                GameObject gunungGo = ctx.Track(new GameObject("QA_GunungNode"));
                gunungGo.transform.position = new Vector3(0f, 5f, -70f);
                gunungGo.transform.localScale = new Vector3(10f, 10f, 10f);
                GunungNodeController node = gunungGo.AddComponent<GunungNodeController>();
                InvokeNonPublic(node, "Awake");
                AssertApprox(0f, node.baseY, 0.001f, "GunungNode baseY anchored at 0");

                // Tool #01 cannot dredge
                gm.DamageGunungSampah(0.30f, gunungGo.transform.position);
                AssertApprox(1f, gm.gunungSampahHealth, 0.001f, "Starter tool cannot damage Gunung");

                // Unlock & buy #13 Ganco Ganda Winch
                InvokeNonPublic(gm, "AddEarnings", 140000);
                Assert(gm.highestUnlockedToolIndex == 13, "140k unlocks #13 Ganco Ganda Winch");
                Assert(gm.BuyTool(13), "BuyTool #13 Ganco Ganda Winch");

                int tierBreaches = 0;
                Vector3 lastBreachPos = Vector3.zero;
                gm.OnGunungTierBreached += p => { tierBreaches++; lastBreachPos = p; };
                GameEnding victoryEnding = GameEnding.None;
                gm.OnEndingTriggered += e => victoryEnding = e;

                Vector3 hitPos = new Vector3(2f, 3f, -68f);
                GunungNodeController[] allNodes = UnityEngine.Object.FindObjectsOfType<GunungNodeController>(true);
                for (int i = 0; i < allNodes.Length; i++) { allNodes[i].Restore(); allNodes[i].ApplyDamage(0.30f); } // 1.0 -> 0.70 (Tier 4 -> 3)
                gm.DamageGunungSampah(0.10f, hitPos);
                Assert(tierBreaches == 1 && lastBreachPos == hitPos, "OnGunungTierBreached fires with impactPos on tier drop");

                for (int i = 0; i < allNodes.Length; i++) allNodes[i].ApplyDamage(0.30f); // 0.70 -> 0.40 (Tier 3 -> 2)
                gm.DamageGunungSampah(0.10f, hitPos);
                Assert(tierBreaches == 2, "Second Gunung tier breach");

                for (int i = 0; i < allNodes.Length; i++) allNodes[i].ApplyDamage(0.40f); // 0.40 -> 0.00 (Tier 2 -> 0 -> CompleteCleanBreach)
                gm.DamageGunungSampah(0.10f, hitPos);
                Assert(tierBreaches == 3, "Final Gunung tier breach");
                Assert(gm.activeEnding == GameEnding.TrueSdgVictory && victoryEnding == GameEnding.TrueSdgVictory, "Clean breach triggers TrueSdgVictory");
                AssertApprox(1f, gm.waterClarity, 0.001f, "TrueSdgVictory restores waterClarity to 1.0");
                AssertApprox(RiverGameManager.BaseWaterLevelY, gm.currentWaterLevelY, 0.001f, "TrueSdgVictory resets water to BaseWaterLevelY");
            }

            // 2. CompromisedOceanFlush ending
            using (QaContext ctx = new QaContext())
            {
                RiverGameManager gm = ctx.Manager;
                GameEnding flushEnding = GameEnding.None;
                gm.OnEndingTriggered += e => flushEnding = e;
                gm.RegisterActiveTrash(120);
                gm.TriggerEmergencyFlush(confirmed: true);
                Assert(gm.activeEnding == GameEnding.CompromisedOceanFlush && flushEnding == GameEnding.CompromisedOceanFlush, "CompromisedOceanFlush ending");
                Assert(gm.flushedKg > 0 && gm.TotalTrashInRiver == 0 && gm.gunungSampahHealth == 0f, "Emergency flush clears river and records flushedKg");
            }

            // 3. Weather trigger & Monsoon Survival TrueSdgVictory via Update
            using (QaContext ctx = new QaContext())
            {
                RiverGameManager gm = ctx.Manager;
                bool weatherFlag = false;
                int weatherEvents = 0;
                gm.OnWeatherChanged += w => { weatherEvents++; weatherFlag = w; };
                gm.SetWeather(true);
                Assert(weatherEvents == 1 && weatherFlag && gm.isMonsoonStorm, "OnWeatherChanged fires on storm toggle");

                GameEnding timerVictory = GameEnding.None;
                gm.OnEndingTriggered += e => timerVictory = e;
                gm.monsoonCountdownRemaining = 0.0001f;
                InvokeNonPublic(gm, "Tick", 0.1f);
                Assert(gm.activeEnding == GameEnding.PartialSurvival && timerVictory == GameEnding.PartialSurvival, "Monsoon countdown 0 with Gunung intact triggers PartialSurvival");
            }
        }

        private static void VerifyRiverMathSpawnerAndComponents()
        {
            AssertApprox(-65f, RiverMath.MinWorldX, 0.001f, "RiverMath MinWorldX");
            AssertApprox(65f, RiverMath.MaxWorldX, 0.001f, "RiverMath MaxWorldX");
            AssertApprox(-90f, RiverMath.MinWorldZ, 0.001f, "RiverMath MinWorldZ");
            AssertApprox(90f, RiverMath.MaxWorldZ, 0.001f, "RiverMath MaxWorldZ");
            AssertApprox(0f, RiverMath.ToWorld3D(520f, 720f).x, 0.001f, "RiverMath center X");
            AssertApprox(0f, RiverMath.ToWorld3D(520f, 720f).z, 0.001f, "RiverMath center Z");
            Vector3 midChannel = RiverMath.ToWorld3D(RiverMath.RiverCenterMapX(720f), 720f);
            Assert(RiverMath.IsInRiver(midChannel), "Centerline point is in river");
            Assert(!RiverMath.IsInRiver(new Vector3(-55f, 0f, 0f)), "Far west bank is outside river");

            using (QaContext ctx = new QaContext())
            {
                RiverGameManager gm = ctx.Manager;
                GameObject dummyPrefab = ctx.Track(new GameObject("QA_TrashTemplate"));
                GameObject spawnerGo = ctx.Track(new GameObject("QA_Spawner"));
                RiverTrashSpawner spawner = spawnerGo.AddComponent<RiverTrashSpawner>();
                spawner.biohazardPrefabs = new[] { dummyPrefab };
                spawner.normalPrefabs = new[] { dummyPrefab };

                int beforeActive = gm.activeRiverTrashCount;
                GameObject spawned = ctx.Track(spawner.SpawnTrashAt(midChannel, WasteClass.Biohazard));
                RiverTrashItem item = spawned.GetComponent<RiverTrashItem>();
                Assert(item != null && item.wasteClass == WasteClass.Biohazard, "SpawnTrashAt sets WasteClass");
                Assert(spawned.GetComponent<RiverFlowBuoyancy>() != null && spawned.GetComponent<Collider>() != null, "Spawned trash has buoyancy + collider");
                Assert(gm.activeRiverTrashCount == beforeActive + 1, "Spawned trash registers active count");

                item.TryUnregister();
                Assert(gm.activeRiverTrashCount == beforeActive, "TryUnregister decrements active count");

                // Barrier pile conversion and visual absorption threshold (>= 22)
                gm.piledRiverTrashCount = 21;
                Assert(!gm.ShouldAbsorbVisualBarrierProp(), "ShouldAbsorbVisualBarrierProp false below 22");
                gm.piledRiverTrashCount = 22;
                Assert(gm.ShouldAbsorbVisualBarrierProp(), "ShouldAbsorbVisualBarrierProp true at 22");

                GameObject barrierTrash = ctx.Track(spawner.SpawnTrashAt(midChannel, WasteClass.Normal));
                RiverTrashItem barrierItem = barrierTrash.GetComponent<RiverTrashItem>();
                int activeBeforePile = gm.activeRiverTrashCount;
                int piledBeforePile = gm.piledRiverTrashCount;
                barrierItem.MarkPiledAtBarrier();
                Assert(barrierItem.isPiledAtBarrier, "MarkPiledAtBarrier sets flag");
                Assert(gm.activeRiverTrashCount == activeBeforePile - 1, "MarkPiledAtBarrier decrements active count");
                Assert(gm.piledRiverTrashCount == piledBeforePile + 1, "MarkPiledAtBarrier increments piled count");
            }
        }

        private static void VerifyChildColliderLookupAndSingleEndingGuard()
        {
            // 1. Child-collider hierarchy matching for hubs and GunungNodeController
            using (QaContext ctx = new QaContext(isolateSceneGunungNodes: true))
            {
                RiverGameManager gm = ctx.Manager;
                InvokeNonPublic(gm, "AddEarnings", 140000);
                Assert(gm.BuyTool(13), "BuyTool #13 Ganco Ganda Winch");

                Vector3 isolatedPos = new Vector3(5000f, 5000f, 5000f);
                GameObject hubRoot = MakeStation(ctx, "Bank Sampah Berkah", isolatedPos);
                GameObject hubChild = ctx.Track(new GameObject("SM_Env_BankSampah_Mesh"));
                hubChild.transform.SetParent(hubRoot.transform, false);
                hubChild.transform.localScale = new Vector3(6f, 4f, 6f);
                hubChild.AddComponent<BoxCollider>();
                // The old river dock box must never enable selling.
                GameObject dockBox = ctx.Track(new GameObject("Bank Sampah Berkah_RiverDockTrigger"));
                dockBox.transform.SetParent(hubRoot.transform, false);
                dockBox.transform.localPosition = new Vector3(12f, 0f, 0f);
                BoxCollider dockCol = dockBox.AddComponent<BoxCollider>();
                dockCol.isTrigger = true;
                dockCol.size = new Vector3(20f, 4.5f, 8f);

                GameObject playerGo = ctx.Track(new GameObject("QA_Player"));
                playerGo.transform.position = isolatedPos;
                playerGo.AddComponent<CharacterController>();
                KaliPlayerController player = playerGo.AddComponent<KaliPlayerController>();

                GameObject gunungRoot = ctx.Track(new GameObject("Puncak Gunung Sampah"));
                gunungRoot.transform.position = new Vector3(0f, 5f, -70f);
                GunungNodeController node = gunungRoot.AddComponent<GunungNodeController>();
                InvokeNonPublic(node, "Awake");
                GameObject gunungChild = ctx.Track(new GameObject("SM_Env_Gunung_Child"));
                gunungChild.transform.SetParent(gunungRoot.transform, false);
                BoxCollider gunungCol = gunungChild.AddComponent<BoxCollider>();

                Physics.SyncTransforms();

                MethodInfo findHub = typeof(KaliPlayerController).GetMethod("TryFindNearestHub", BindingFlags.Instance | BindingFlags.NonPublic, null, new[] { typeof(DiscardStationType).MakeByRefType(), typeof(bool).MakeByRefType() }, null);
                if (findHub == null) throw new InvalidOperationException("Missing KaliPlayerController.TryFindNearestHub");
                object[] hubArgs = new object[] { DiscardStationType.GudangPengepul, false };
                Assert(!(bool)findHub.Invoke(player, hubArgs), "Touching the building (outside its service point) does not enable the station");
                playerGo.transform.position = isolatedPos + new Vector3(14f, 0f, 0f);
                playerGo.transform.rotation = Quaternion.LookRotation(Vector3.left);
                Physics.SyncTransforms();
                Assert(!(bool)findHub.Invoke(player, hubArgs), "Standing in the river dock trigger does not enable selling");
                PlaceAtServicePoint(playerGo, isolatedPos);
                bool foundHub = (bool)findHub.Invoke(player, hubArgs);
                Assert(foundHub && (DiscardStationType)hubArgs[0] == DiscardStationType.BankSampah, "Service point resolves to Bank Sampah");
                playerGo.transform.rotation = Quaternion.LookRotation(Vector3.right);
                Assert(!(bool)findHub.Invoke(player, hubArgs), "Facing away from the counter is not valid");
                PlaceAtServicePoint(playerGo, isolatedPos);
                player.isSwimming = true;
                Assert(!(bool)findHub.Invoke(player, hubArgs), "Swimming player cannot use a station");
                player.isSwimming = false;

                // Pure service-point math (spec A): radius + 0.3 slack, facing dot >= 0.5
                Vector3 pt = new Vector3(4f, 0f, 0f);
                Assert(KaliPlayerController.IsAtServicePoint(new Vector3(6.25f, 1f, 0f), Vector3.left, pt, 2f, Vector3.zero, false), "Inside r+0.3 (2.25 m) facing counter is valid");
                Assert(!KaliPlayerController.IsAtServicePoint(new Vector3(6.4f, 1f, 0f), Vector3.left, pt, 2f, Vector3.zero, false), "Beyond r+0.3 (2.4 m) is invalid");
                Assert(!KaliPlayerController.IsAtServicePoint(new Vector3(5f, 1f, 0f), new Vector3(0f, 0f, 1f), pt, 2f, Vector3.zero, false), "Facing sideways (dot 0) is invalid");
                Assert(!KaliPlayerController.IsAtServicePoint(new Vector3(5f, 1f, 0f), Vector3.left, pt, 2f, Vector3.zero, true), "Swimming is invalid");

                // Every hub token in HubRules resolves to its station + shop flag (hubs spaced 50m apart so each is the only one in range)
                (string name, DiscardStationType station, bool isKopdes)[] allHubs =
                {
                    ("Pos Medis B3", DiscardStationType.PosMedisB3, false),
                    ("Karantina Biohazard", DiscardStationType.KarantinaBiohazard, false),
                    ("Gudang Pengepul", DiscardStationType.GudangPengepul, false),
                    ("Koperasi Desa (Kopdes)", DiscardStationType.BankSampah, true),
                    ("Kopdes", DiscardStationType.BankSampah, true)
                };
                for (int h = 0; h < allHubs.Length; h++)
                {
                    Vector3 hubPos = isolatedPos + new Vector3(0f, 0f, 50f * (h + 1)); // along Z so the +X hub-exit check below stays empty
                    MakeStation(ctx, allHubs[h].name, hubPos);
                    PlaceAtServicePoint(playerGo, hubPos);

                    object[] extraArgs = new object[] { DiscardStationType.GudangPengepul, false };
                    bool foundExtra = (bool)findHub.Invoke(player, extraArgs);
                    Assert(foundExtra && (DiscardStationType)extraArgs[0] == allHubs[h].station && (bool)extraArgs[1] == allHubs[h].isKopdes,
                        $"Hub '{allHubs[h].name}' resolves to {allHubs[h].station} (kopdes={allHubs[h].isKopdes})");
                }
                PlaceAtServicePoint(playerGo, isolatedPos);

                int hubEvents = 0;
                bool lastNear = false;
                string lastHubName = string.Empty;
                player.OnNearbyHubChanged += (near, st, kopdes, hubName) => { hubEvents++; lastNear = near; lastHubName = hubName; };
                player.RefreshNearbyHub();
                Assert(hubEvents == 1 && lastNear && player.HasNearbyHub && lastHubName == "Bank Sampah Berkah", "OnNearbyHubChanged emits on hub enter");
                player.RefreshNearbyHub();
                Assert(hubEvents == 1, "OnNearbyHubChanged does not spam when unchanged");
                playerGo.transform.position = isolatedPos + new Vector3(100f, 0f, 0f);
                Physics.SyncTransforms();
                player.RefreshNearbyHub();
                Assert(hubEvents == 2 && !lastNear && !player.HasNearbyHub && lastHubName == string.Empty, "OnNearbyHubChanged emits on hub exit");

                MethodInfo dmgGunung = typeof(KaliPlayerController).GetMethod("TryDamageGunungCollider", BindingFlags.Static | BindingFlags.NonPublic);
                if (dmgGunung == null) throw new InvalidOperationException("Missing KaliPlayerController.TryDamageGunungCollider");
                bool damaged = (bool)dmgGunung.Invoke(null, new object[] { gunungCol, gm, gm.EquippedTool });
                Assert(damaged && node.nodeHealth < 1f && gm.gunungSampahHealth < 1f, "Child collider damages parent GunungNodeController");

                MethodInfo hasName = typeof(KaliPlayerController).GetMethod("HasHierarchyName", BindingFlags.Static | BindingFlags.NonPublic);
                if (hasName == null) throw new InvalidOperationException("Missing KaliPlayerController.HasHierarchyName");
                Assert((bool)hasName.Invoke(null, new object[] { gunungChild.transform, "Gunung Sampah" }), "HasHierarchyName finds ancestor token");
            }

            // 2. Single-ending guard: HealthFail must not be overwritten by FloodFail in Update()
            using (QaContext ctx = new QaContext())
            {
                RiverGameManager gm = ctx.Manager;

                int endingCount = 0;
                GameEnding lastEnding = GameEnding.None;
                gm.OnEndingTriggered += e => { endingCount++; lastEnding = e; };

                InvokeNonPublic(gm, "ApplyPlayerDamage", gm.playerHealth + 1f, true);
                Assert(gm.activeEnding == GameEnding.HealthFail, "HealthFail set before flood check");

                gm.AddPiledTrash(131); // currentWaterLevelY >= fatalFloodWaterY (2.45f)
                Assert(gm.currentWaterLevelY >= gm.fatalFloodWaterY, "Flood threshold active");
                InvokeNonPublic(gm, "Tick", 0.1f);

                Assert(endingCount == 1 && gm.activeEnding == GameEnding.HealthFail && lastEnding == GameEnding.HealthFail, "HealthFail is not overwritten by FloodFail");
            }
        }

        private static void VerifyPrefabHitboxProportions()
        {
            string[] guids = AssetDatabase.FindAssets("t:Prefab", new[] { "Assets/_Project/Props", "Assets/_Project/Rigging" });
            Assert(guids.Length > 0, "Hitbox audit finds Props/Rigging prefabs");

            for (int i = 0; i < guids.Length; i++)
            {
                string path = AssetDatabase.GUIDToAssetPath(guids[i]);
                string prefabName = System.IO.Path.GetFileNameWithoutExtension(path);
                GameObject prefab = AssetDatabase.LoadAssetAtPath<GameObject>(path);
                Assert(prefab != null, $"Load prefab {path}");

                GameObject instance = (GameObject)PrefabUtility.InstantiatePrefab(prefab);
                try
                {
                    Physics.SyncTransforms();
                    Collider[] colliders = instance.GetComponentsInChildren<Collider>(true);
                    Assert(colliders.Length > 0, $"{prefabName} has at least one collider");

                    Bounds colliderBounds = colliders[0].bounds;
                    bool anyNonTrigger = false;
                    for (int c = 0; c < colliders.Length; c++)
                    {
                        colliderBounds.Encapsulate(colliders[c].bounds);
                        if (!colliders[c].isTrigger) anyNonTrigger = true;
                    }

                    bool hasRenderer = false;
                    Bounds rendererBounds = default;
                    Renderer[] renderers = instance.GetComponentsInChildren<Renderer>(true);
                    for (int r = 0; r < renderers.Length; r++)
                    {
                        if (renderers[r] is ParticleSystemRenderer) continue;
                        if (!hasRenderer)
                        {
                            rendererBounds = renderers[r].bounds;
                            hasRenderer = true;
                        }
                        else
                        {
                            rendererBounds.Encapsulate(renderers[r].bounds);
                        }
                    }
                    Assert(hasRenderer, $"{prefabName} has a renderer to measure");

                    for (int axis = 0; axis < 3; axis++)
                    {
                        float rendererSize = rendererBounds.size[axis];
                        if (rendererSize < 0.0001f) continue;
                        float ratio = colliderBounds.size[axis] / rendererSize;
                        Assert(ratio >= 0.8f && ratio <= 1.25f, $"{prefabName} collider/renderer ratio on axis {axis} is {ratio:F2}, expected 0.80-1.25");
                    }

                    if (prefabName.StartsWith("PF_Tool_", StringComparison.Ordinal))
                    {
                        for (int c = 0; c < colliders.Length; c++)
                        {
                            Assert(colliders[c].isTrigger, $"{prefabName} collider must be a trigger");
                        }
                    }
                    else if (prefabName.StartsWith("PF_Trash_", StringComparison.Ordinal))
                    {
                        Assert(anyNonTrigger, $"{prefabName} needs a solid (non-trigger) collider");
                        Assert(instance.GetComponent<RiverTrashItem>() != null, $"{prefabName} needs RiverTrashItem");
                        Assert(instance.GetComponent<RiverFlowBuoyancy>() != null, $"{prefabName} needs RiverFlowBuoyancy");
                    }
                }
                finally
                {
                    UnityEngine.Object.DestroyImmediate(instance);
                }
            }
        }

        private static void VerifyDermagaRiverPortLimits()
        {
            using (QaContext ctx = new QaContext())
            {
                RiverGameManager gm = ctx.Manager;
                // Place isolated Dermaga on West bank at Z = 45m (mapY = 1080, clear of Main.unity Dermaga Awal Z=61.25 and Dermaga Tengah Z=-13.125)
                const float testMapY = 1080f;
                float cx = RiverMath.RiverCenterMapX(testMapY);
                float hw = RiverMath.RiverHalfWidthMap(testMapY);
                Vector3 dockCenter = RiverMath.ToWorld3D(cx - hw, testMapY, 0.625f);

                GameObject dockGo = ctx.Track(new GameObject("Dermaga QA Port"));
                dockGo.transform.position = dockCenter;
                BoxCollider dockBox = dockGo.AddComponent<BoxCollider>();
                dockBox.size = new Vector3(9f, 1.25f, 4.5f);

                GameObject playerGo = ctx.Track(new GameObject("QA_DermagaPlayer"));
                playerGo.AddComponent<CharacterController>();
                KaliPlayerController player = playerGo.AddComponent<KaliPlayerController>();

                MethodInfo toggleBoat = typeof(KaliPlayerController).GetMethod("TryToggleBoat", BindingFlags.Instance | BindingFlags.NonPublic);
                MethodInfo resolveFoot = typeof(KaliPlayerController).GetMethod("ResolvePermittedMoveOnFoot", BindingFlags.Instance | BindingFlags.NonPublic);
                if (toggleBoat == null || resolveFoot == null) throw new InvalidOperationException("Missing Dermaga methods on KaliPlayerController");

                // 1. Off-dock bank edge (Z = 25m, far from any Dermaga): boarding MUST be blocked
                Vector3 offDockBank = RiverMath.ToWorld3D(RiverMath.RiverCenterMapX(920f) - RiverMath.RiverHalfWidthMap(920f) - 12f, 920f, 2.4f);
                playerGo.transform.position = offDockBank;
                Physics.SyncTransforms();
                bool offDockBoard = (bool)toggleBoat.Invoke(player, new object[] { gm });
                Assert(!offDockBoard && !player.isInBoat, "Cannot board boat off-dock along riverbank");

                // 2. Foot entry into river: walking or jumping off bank into RiverMath.IsInRiver IS permitted (triggers swimming instead of invisible wall)
                Vector3 stepIntoRiver = new Vector3(5.0f, 0f, 0f);
                Vector3 permittedStep = (Vector3)resolveFoot.Invoke(player, new object[] { offDockBank, stepIntoRiver, gm });
                Assert(permittedStep.x > 4.9f, "Foot movement can enter river off-dock to swim");

                Vector3 midAirOffDock = new Vector3(offDockBank.x, 3.5f, offDockBank.z);
                Vector3 jumpStep = (Vector3)resolveFoot.Invoke(player, new object[] { midAirOffDock, stepIntoRiver, gm });
                Assert(jumpStep.x > 4.9f, "Jumping off-dock bank can enter river to swim");

                // 2b. Jembatan crossing: walking across an elevated bridge over RiverMath.IsInRiver IS permitted
                const float bridgeMapY = 740f;
                Vector3 bridgeCenter = RiverMath.ToWorld3D(RiverMath.RiverCenterMapX(bridgeMapY), bridgeMapY, 3.6f);
                GameObject bridgeGo = ctx.Track(new GameObject("Jembatan QA Bridge"));
                bridgeGo.transform.position = bridgeCenter;
                BoxCollider bridgeCol = bridgeGo.AddComponent<BoxCollider>();
                bridgeCol.size = new Vector3(28f, 0.45f, 8f);
                Physics.SyncTransforms();

                Vector3 onBridgePos = new Vector3(bridgeCenter.x - 2.0f, 4.7f, bridgeCenter.z);
                Vector3 bridgeStep = (Vector3)resolveFoot.Invoke(player, new object[] { onBridgePos, stepIntoRiver, gm });
                Assert(bridgeStep.x > 4.9f, "Foot movement across Jembatan over river is permitted");

                // 2c. Dermaga pier: walking on pier AND stepping off pier into water on foot is permitted (boats remain Dermaga-only)
                Vector3 onPierPos = new Vector3(dockCenter.x + 3.5f, 2.25f, dockCenter.z);
                Vector3 stepToPierTip = new Vector3(0.5f, 0f, 0f);
                Vector3 stepPastPier = new Vector3(4.0f, 0f, 0f);
                Vector3 ontoPierStep = (Vector3)resolveFoot.Invoke(player, new object[] { onPierPos, stepToPierTip, gm });
                Vector3 offPierStep = (Vector3)resolveFoot.Invoke(player, new object[] { onPierPos, stepPastPier, gm });
                Assert(ontoPierStep.x > 0.4f, "Walking onto Dermaga pier is permitted");
                Assert(offPierStep.x > 3.9f, "Walking off Dermaga pier into river to swim is permitted");

                // 3. On Dermaga: OnNearbyDermagaChanged emits and boarding succeeds into RiverMath.IsInRiver
                int dockEvents = 0;
                bool lastNearDock = false;
                bool lastBoatState = false;
                player.OnNearbyDermagaChanged += (near, inBoat, name) => { dockEvents++; lastNearDock = near; lastBoatState = inBoat; };

                playerGo.transform.position = new Vector3(dockCenter.x, 2.25f, dockCenter.z);
                Physics.SyncTransforms();
                player.RefreshNearbyHub();
                Assert(dockEvents == 1 && lastNearDock && !lastBoatState && player.HasNearbyDermaga, "OnNearbyDermagaChanged emits on Dermaga approach");

                bool onDockBoard = (bool)toggleBoat.Invoke(player, new object[] { gm });
                Assert(onDockBoard && player.isInBoat && RiverMath.IsInRiver(playerGo.transform.position), "Boarding at Dermaga places boat inside river channel");
                Assert(lastBoatState && player.NearbyDermagaIsInBoat, "Dermaga prompt updates to in-boat state after boarding");

                // 4. Mid-river far from any Dermaga: disembarking MUST be blocked
                playerGo.transform.position = new Vector3(0f, gm.currentWaterLevelY + player.boatRideHeight, 25f);
                Physics.SyncTransforms();
                bool offDockDisembark = (bool)toggleBoat.Invoke(player, new object[] { gm });
                Assert(!offDockDisembark && player.isInBoat, "Cannot disembark in mid-river away from Dermaga");

                // 5. Return to Dermaga: disembarking succeeds onto dry bank above BankTopY
                playerGo.transform.position = new Vector3(dockCenter.x + 5.5f, gm.currentWaterLevelY + player.boatRideHeight, dockCenter.z);
                Physics.SyncTransforms();
                bool onDockDisembark = (bool)toggleBoat.Invoke(player, new object[] { gm });
                Assert(onDockDisembark && !player.isInBoat && !RiverMath.IsInRiver(playerGo.transform.position) && playerGo.transform.position.y >= 1.40f,
                    "Disembarking at Dermaga lifts player onto dry land above BankTopY");
            }
        }

        private static void VerifyTask4dAnd4fUxContracts()
        {
            using (QaContext ctx = new QaContext())
            {
                RiverGameManager gm = ctx.Manager;
                Assert(!gm.IsToolUnlocked(0) && gm.IsToolUnlocked(1), "IsToolUnlocked must be 1-based");

                // 1. #11-#20 Medical prick safety lock once #10 Capitan Ular is unlocked
                gm.TryPickupWaste(WasteClass.Normal, 2);
                for (int i = 0; i < 20; i++)
                {
                    gm.TryPickupWaste(WasteClass.Normal, 1);
                    gm.DiscardLegalAtStation(DiscardStationType.BankSampah);
                }
                // Bring cumulative earnings past 140k (#13 Ganco Ganda Winch)
                while (gm.highestUnlockedToolIndex < 13)
                {
                    gm.TryPickupWaste(WasteClass.Normal, 4);
                    gm.DiscardLegalAtStation(DiscardStationType.BankSampah);
                }
                AssertApprox(0f, gm.GetEffectiveMedicalPrickChance(), 0.0001f, "#13+ Medical prick chance locked at 0% after #10 unlock");

                // 2. Duplicate BuyUpgrade guard
                int preRupiah = gm.rupiah;
                bool firstBuy = gm.BuyUpgrade(UpgradeTier.WoodenSampan);
                int postFirst = gm.rupiah;
                bool secondBuy = gm.BuyUpgrade(UpgradeTier.WoodenSampan);
                Assert(firstBuy && !secondBuy && postFirst == preRupiah - RiverGameManager.GetUpgradeCost(UpgradeTier.WoodenSampan) && gm.rupiah == postFirst,
                    "BuyUpgrade must block duplicate purchase spend");

                // 3. Safe [E] DiscardLegalAtStation leaves Medical/Biohazard untouched with 0 fines
                int receipts = 0;
                gm.OnStationAuditReceipt += _ => receipts++;
                gm.TryPickupWaste(WasteClass.Normal, 2);
                gm.TryPickupWaste(WasteClass.Medical, 1);
                int legalOut = gm.DiscardLegalAtStation(DiscardStationType.BankSampah);
                Assert(legalOut > 0 && gm.normalCargo == 0 && gm.medicalCargo == 1 && gm.wrongDiscardCount == 0 && receipts > 0,
                    "DiscardLegalAtStation deposits only legal class with 0 accidental fines and emits audit receipt");

                // 4. EmergencyFlush Sell-Lock + confirm guard
                Assert(!gm.TriggerEmergencyFlush(confirmed: true), "EmergencyFlush blocked when not Sell-Locked");
                gm.RegisterActiveTrash(120); // >= 1.85m
                Assert(gm.IsSellLocked, "120+ trash triggers Sell-Lock");
                Assert(!gm.TriggerEmergencyFlush(confirmed: false), "EmergencyFlush blocked without confirmation");

                // 5. ComputeSdgScorecard + RestartRun full reset
                SdgScorecard card = gm.ComputeSdgScorecard();
                Assert(!string.IsNullOrEmpty(card.Rank), "ComputeSdgScorecard returns valid rank");
                Assert(gm.TriggerEmergencyFlush(confirmed: true) && gm.activeEnding == GameEnding.CompromisedOceanFlush,
                    "Confirmed EmergencyFlush during Sell-Lock triggers CompromisedOceanFlush");

                GameObject rsTemplate = ctx.Track(new GameObject("QA_RestartTrashTemplate"));
                RiverTrashSpawner rsSpawner = ctx.Track(new GameObject("QA_RestartSpawner")).AddComponent<RiverTrashSpawner>();
                rsSpawner.normalPrefabs = new[] { rsTemplate };
                ctx.Track(rsSpawner.SpawnTrashAt(Vector3.zero, WasteClass.Normal));
                gm.RestartRun();
                Assert(gm.activeRiverTrashCount == 0, "RestartRun leaves no registered RiverTrashItem");
                Assert(gm.activeEnding == GameEnding.None && gm.rupiah == 0 && gm.wrongDiscardCount == 0 && gm.unpaidFineDebt == 0 && gm.communityTrust == 40,
                    "RestartRun resets ending, economy, audit debt, and trust");
            }
        }

        private static void VerifySwimmingStaminaAndDrowning()
        {
            using (QaContext ctx = new QaContext())
            {
                RiverGameManager gm = ctx.Manager;
                AssertApprox(gm.maxSwimStamina, gm.swimStamina, 0.001f, "Initial swimStamina is full");
                Assert(!gm.IsSwimming && !gm.IsDrowning, "Initially not swimming or drowning");

                // 1. Setup dry bank ground and player controller
                GameObject bankGo = ctx.Track(new GameObject("QA_DryBank"));
                bankGo.transform.position = new Vector3(-45f, 0.9f, 0f);
                BoxCollider bankCol = bankGo.AddComponent<BoxCollider>();
                bankCol.size = new Vector3(30f, 1.0f, 40f); // top at Y = 1.40f

                GameObject playerGo = ctx.Track(new GameObject("QA_SwimPlayer"));
                playerGo.transform.position = new Vector3(-45f, 2.30f, 0f);
                CharacterController cc = playerGo.AddComponent<CharacterController>();
                cc.height = 1.8f;
                cc.radius = 0.4f;
                KaliPlayerController player = playerGo.AddComponent<KaliPlayerController>();
                InvokeNonPublic(player, "Awake");
                Physics.SyncTransforms();

                int swimEvents = 0;
                bool lastSwimEvent = false;
                player.OnSwimStateChanged += sw => { swimEvents++; lastSwimEvent = sw; };

                // 2. Walking & sprinting on dry land preserves running/sprinting and never drains swimStamina
                Vector3 beforeLandWalk = playerGo.transform.position;
                InvokeNonPublic(player, "StepMovement", new Vector2(0f, 1f), true, false, 0.2f);
                Assert(!player.isSwimming && !gm.IsSwimming, "Sprinting on dry bank stays out of swim mode");
                Assert(playerGo.transform.position.z > beforeLandWalk.z + 1.5f, "Running/sprinting moves player along dry bank");
                InvokeNonPublic(gm, "Tick", 1.0f);
                AssertApprox(gm.maxSwimStamina, gm.swimStamina, 0.001f, "Dry land sprinting does not drain swimStamina");

                // 3. Entering open river water at surface triggers surface-only swimming + OnSwimStateChanged
                Vector3 riverCenter = RiverMath.ToWorld3D(RiverMath.RiverCenterMapX(720f), 720f);
                float expectedSurfaceY = gm.currentWaterLevelY + player.swimSurfaceOffset;
                playerGo.transform.position = new Vector3(riverCenter.x, expectedSurfaceY - 0.5f, riverCenter.z);
                Physics.SyncTransforms();

                InvokeNonPublic(player, "StepMovement", new Vector2(0f, 1f), false, true, 0.1f);
                Assert(player.isSwimming && gm.IsSwimming && swimEvents == 1 && lastSwimEvent,
                    "Entering RiverMath.IsInRiver off-bridge/dock triggers surface swimming and OnSwimStateChanged(true)");
                Assert(playerGo.transform.position.y >= expectedSurfaceY - 0.06f,
                    "Surface-only swimming clamps swimmer up to water surface (never underwater)");

                // Pressing jump mid-river must NOT launch out of water or dive below surface
                float zBeforeSwim = playerGo.transform.position.z;
                InvokeNonPublic(player, "StepMovement", Vector2.zero, false, true, 0.25f);
                Assert(player.isSwimming && playerGo.transform.position.y <= expectedSurfaceY + 0.15f && playerGo.transform.position.y >= expectedSurfaceY - 0.06f,
                    "Mid-river jump stays strictly surface-only");
                Assert(playerGo.transform.position.z > zBeforeSwim, "River current drifts surface swimmer toward +Z downstream");

                // Shore climb-out assist near bank exits swim state cleanly and lifts swimmer toward bank top
                float westShoreX = (RiverMath.RiverCenterMapX(720f) - RiverMath.RiverHalfWidthMap(720f) - RiverMath.WorldW * 0.5f) * RiverMath.MapScale + 0.5f;
                playerGo.transform.position = new Vector3(westShoreX, expectedSurfaceY, 0f);
                Physics.SyncTransforms();
                InvokeNonPublic(player, "StepMovement", new Vector2(-1f, 0f), false, true, 0.15f);
                Assert(!player.isSwimming && playerGo.transform.position.y > expectedSurfaceY + 0.3f,
                    "Pressing jump while swimming into shoreline triggers climb-out lift");
                for (int step = 0; step < 6; step++)
                {
                    InvokeNonPublic(player, "StepMovement", new Vector2(-1f, 0f), false, false, 0.12f);
                }
                Assert(!RiverMath.IsInRiver(playerGo.transform.position) && !player.isSwimming,
                    "Climb-out finishes onto riverbank out of swim state");

                // 4. Swim stamina drain rates: treading (4/s), moving (8/s), sprinting (16/s)
                gm.swimStamina = 100f;
                gm.SetPlayerSwimming(true, movingInWater: false, sprintingInWater: false);
                InvokeNonPublic(gm, "Tick", 1.0f);
                AssertApprox(96f, gm.swimStamina, 0.01f, "Treading water drains 4 swimStamina/s");

                gm.SetPlayerSwimming(true, movingInWater: true, sprintingInWater: false);
                InvokeNonPublic(gm, "Tick", 1.0f);
                AssertApprox(88f, gm.swimStamina, 0.01f, "Swimming drains 8 swimStamina/s");

                gm.SetPlayerSwimming(true, movingInWater: true, sprintingInWater: true);
                InvokeNonPublic(gm, "Tick", 2.0f);
                AssertApprox(56f, gm.swimStamina, 0.01f, "Sprint-swimming drains 16 swimStamina/s");

                // 5. Exiting water onto dry land/bridge/Dermaga/boat recovers swimStamina
                playerGo.transform.position = new Vector3(-45f, 2.30f, 0f);
                Physics.SyncTransforms();
                InvokeNonPublic(player, "StepMovement", Vector2.zero, false, false, 0.1f);
                Assert(!player.isSwimming && !gm.IsSwimming && !lastSwimEvent, "Returning to dry bank exits swimming");
                float staminaBeforeRegen = gm.swimStamina;
                InvokeNonPublic(gm, "Tick", 2.0f);
                AssertApprox(Mathf.Min(gm.maxSwimStamina, staminaBeforeRegen + 36f), gm.swimStamina, 0.01f,
                    "Swim stamina regenerates at 18/s out of water");

                // Boarding a boat while swimming clears swim state immediately
                playerGo.transform.position = new Vector3(riverCenter.x, expectedSurfaceY, riverCenter.z);
                Physics.SyncTransforms();
                InvokeNonPublic(player, "StepMovement", new Vector2(0f, 1f), false, false, 0.1f);
                Assert(player.isSwimming, "Back in river swimming before boarding boat");
                Vector3 dockPos = RiverMath.ToWorld3D(RiverMath.RiverCenterMapX(1000f) - RiverMath.RiverHalfWidthMap(1000f), 1000f, 0.625f);
                GameObject swimDock = ctx.Track(new GameObject("Dermaga SwimQA"));
                swimDock.transform.position = dockPos;
                swimDock.AddComponent<BoxCollider>().size = new Vector3(8f, 1.25f, 4f);
                playerGo.transform.position = new Vector3(dockPos.x + 2f, expectedSurfaceY, dockPos.z);
                Physics.SyncTransforms();
                MethodInfo toggleBoat = typeof(KaliPlayerController).GetMethod("TryToggleBoat", BindingFlags.Instance | BindingFlags.NonPublic);
                bool boarded = (bool)toggleBoat.Invoke(player, new object[] { gm });
                Assert(boarded && player.isInBoat && !player.isSwimming && !gm.IsSwimming,
                    "Boarding boat at Dermaga clears swimming state");
                InvokeNonPublic(player, "StepMovement", Vector2.zero, false, false, 0.1f);
                Assert(!player.isSwimming && !gm.IsSwimming, "Boat ride stays non-swimming");

                // 6. Exhausting swim stamina triggers drowning alerts, blocks passive HP regen, and causes HealthFail with drowning diagnosis
                player.ResetToInitialSpawn();
                gm.swimStamina = 10f;
                gm.playerHealth = 50f;
                int dangerAlerts = 0;
                string lastAlert = string.Empty;
                gm.OnHazardOrAlert += (msg, danger) => { if (danger) { dangerAlerts++; lastAlert = msg; } };
                gm.SetPlayerSwimming(true, movingInWater: true, sprintingInWater: true); // drains 16/s
                InvokeNonPublic(gm, "Tick", 1.0f); // 10 - 16 -> 0 stamina
                Assert(gm.swimStamina == 0f && gm.IsDrowning && dangerAlerts >= 1,
                    "Exhausting swim stamina triggers IsDrowning and danger alert");
                Assert(lastAlert.Contains("TENGGELAM"), "Drowning alert warns player");

                // Subsequent tick deals drowning damage (14 HP/s) without passive HP recovery
                InvokeNonPublic(gm, "Tick", 2.0f); // 50 - 28 = 22 HP
                AssertApprox(22f, gm.playerHealth, 0.05f, "Drowning deals 14 HP/s without passive HP regen");

                InvokeNonPublic(gm, "Tick", 2.0f); // 22 - 28 -> 0 HP -> HealthFail
                Assert(gm.playerHealth == 0f && gm.activeEnding == GameEnding.HealthFail,
                    "Drowning to 0 HP triggers HealthFail");
                Assert(gm.LastEndingDiagnosis.Contains("tenggelam"),
                    "HealthFail caused by drowning records drowning-specific diagnosis");

                // 7. RestartRun restores full swimStamina and clears swim/drowning state
                gm.RestartRun();
                AssertApprox(gm.maxSwimStamina, gm.swimStamina, 0.001f, "RestartRun restores full swimStamina");
                Assert(!gm.IsSwimming && !gm.IsDrowning, "RestartRun clears swimming and drowning state");
            }
        }

        private static void VerifyDayNightCycle()
        {
            KaliDayNightCycle prevCycle = KaliDayNightCycle.Instance;
            PropertyInfo cycleInstProp = typeof(KaliDayNightCycle).GetProperty("Instance", BindingFlags.Public | BindingFlags.Static);
            cycleInstProp?.SetValue(null, null);

            try
            {
                using (QaContext ctx = new QaContext())
                {
                    RiverGameManager gm = ctx.Manager;
                    GameObject rig = ctx.Track(new GameObject("QA_DayNightRig"));
                    GameObject sunGo = ctx.Track(new GameObject("Sun"));
                    sunGo.transform.SetParent(rig.transform, false);
                    sunGo.AddComponent<Light>().type = LightType.Directional;
                    KaliDayNightCycle cycle = rig.AddComponent<KaliDayNightCycle>();
                    InvokeNonPublic(cycle, "Awake");

                    // 1. Sunrise (+Z) and Noon elevation
                    cycle.SetHour(6f);
                    Assert(Mathf.Abs(cycle.SunDirection.y) < 0.1f && cycle.SunDirection.z > 0.9f,
                        "Hour 6 sun sits near horizon toward +Z (Pintu Air)");

                    cycle.SetHour(12f);
                    Assert(cycle.SunDirection.y > 0.9f * Mathf.Sin(72f * Mathf.Deg2Rad),
                        "Hour 12 sun reaches high noon elevation");

                    // 2. StartHour (evening golden hour) toward -Z at 3.5-7.5 deg
                    cycle.SetHour(cycle.startHour);
                    float elevDeg = Mathf.Asin(Mathf.Clamp(cycle.SunDirection.y, -1f, 1f)) * Mathf.Rad2Deg;
                    Assert(cycle.SunDirection.z < 0f && elevDeg >= 3.5f && elevDeg <= 7.5f,
                        $"StartHour {cycle.startHour:F2} sun sits toward -Z at 3.5-7.5 deg (got {elevDeg:F2} deg)");

                    // 3. Night moonlit sky & stars
                    cycle.SetHour(23f);
                    Assert(cycle.MoonDirection.y > 0.1f && cycle.CurrentStars > 0.5f,
                        "Hour 23 moon is above horizon and stars are visible");

                    // 4. ClockText formatting & proportional Step + 24h wrap
                    cycle.SetHour(17.4f);
                    Assert(cycle.ClockText == "17:24", $"Expected ClockText 17:24, got {cycle.ClockText}");

                    cycle.Step(cycle.dayLengthSeconds * 0.25f);
                    AssertApprox(23.4f, cycle.CurrentHour, 0.01f, "Step(0.25 day) advances +6h");
                    cycle.Step(cycle.dayLengthSeconds);
                    AssertApprox(23.4f, cycle.CurrentHour, 0.02f, "Step(1.0 day) wraps cleanly modulo 24h");

                    // 5. SkipToNextPhase sequence from startHour: Dusk -> Night -> Dawn -> Noon -> Golden Hour
                    cycle.SetHour(cycle.startHour);
                    cycle.SkipToNextPhase();
                    AssertApprox(18f + 40f / 60f, cycle.CurrentHour, 0.02f, "Skip 1 -> Dusk 18:40");
                    cycle.SkipToNextPhase();
                    AssertApprox(22f, cycle.CurrentHour, 0.02f, "Skip 2 -> Night 22:00");
                    cycle.SkipToNextPhase();
                    AssertApprox(5f + 50f / 60f, cycle.CurrentHour, 0.02f, "Skip 3 -> Dawn 05:50");
                    cycle.SkipToNextPhase();
                    AssertApprox(12f, cycle.CurrentHour, 0.02f, "Skip 4 -> Noon 12:00");
                    cycle.SkipToNextPhase();
                    AssertApprox(cycle.startHour, cycle.CurrentHour, 0.02f, "Skip 5 -> Golden Hour");

                    // 6. Storm blend (~6s smoothing -> ~1 within 10s) and Smog curve
                    gm.isMonsoonStorm = true;
                    cycle.Step(10f);
                    Assert(cycle.StormBlend >= 0.99f, $"StormBlend reaches ~1 after 10s (got {cycle.StormBlend:F3})");
                    gm.isMonsoonStorm = false;
                    cycle.Step(10f);
                    Assert(cycle.StormBlend <= 0.01f, $"StormBlend clears after 10s (got {cycle.StormBlend:F3})");

                    gm.waterClarity = 0.65f;
                    cycle.Step(0.1f);
                    AssertApprox(0f, cycle.SmogFactor, 0.001f, "Smog is 0 at waterClarity 0.65");
                    gm.waterClarity = 0.12f;
                    cycle.Step(0.1f);
                    Assert(cycle.SmogFactor > 0.8f, $"Smog > 0.8 at waterClarity 0.12 (got {cycle.SmogFactor:F3})");
                }
            }
            finally
            {
                cycleInstProp?.SetValue(null, prevCycle);
            }
        }

        private static void VerifyKampungRowsAndMapEdge()
        {
            AssertApprox(1040f, RiverMath.WorldW, 0.0001f, "RiverMath.WorldW");
            AssertApprox(1440f, RiverMath.WorldH, 0.0001f, "RiverMath.WorldH");
            AssertApprox(0.125f, RiverMath.MapScale, 0.0001f, "RiverMath.MapScale");

            var runA = MapJsonImporter.ExpandDefaultMapKampungRows();
            var runB = MapJsonImporter.ExpandDefaultMapKampungRows();

            Assert(runA.Count >= 60, $"kampung_row expansion produces >= 60 buildings (got {runA.Count})");
            Assert(runA.Count == runB.Count, $"kampung_row expansion count is deterministic ({runA.Count} vs {runB.Count})");

            Vector2[] protectedMapPoints = new Vector2[]
            {
                new Vector2(195f, 1185f), // Bank Sampah
                new Vector2(195f, 1085f), // Koperasi Desa
                new Vector2(285f, 1280f), // Gudang Pengepul
                new Vector2(220f, 720f),  // Pos Medis B3
                new Vector2(760f, 475f),  // Karantina Biohazard
                new Vector2(378f, 1210f), // Dermaga Awal
                new Vector2(645f, 615f),  // Dermaga Tengah
                new Vector2(310f, 1210f)  // Spawn
            };
            Vector2[] protectedWorldXZ = new Vector2[protectedMapPoints.Length];
            for (int p = 0; p < protectedMapPoints.Length; p++)
            {
                Vector3 wp = RiverMath.ToWorld3D(protectedMapPoints[p].x, protectedMapPoints[p].y, 0f);
                protectedWorldXZ[p] = new Vector2(wp.x, wp.z);
            }

            int westCount = 0;
            int eastCount = 0;

            for (int i = 0; i < runA.Count; i++)
            {
                KaliKampungBuilder.ExpandedBuilding a = runA[i];
                KaliKampungBuilder.ExpandedBuilding b = runB[i];

                Assert(a.rowId == b.rowId, $"Deterministic rowId at index {i}");
                Assert(a.buildingType == b.buildingType, $"Deterministic buildingType at index {i}");
                Assert(Vector3.Distance(a.worldPos, b.worldPos) < 0.0001f, $"Deterministic worldPos at index {i}");
                Assert(Mathf.Abs(a.yawDeg - b.yawDeg) < 0.0001f, $"Deterministic yawDeg at index {i}");
                Assert(a.hasJetty == b.hasJetty, $"Deterministic hasJetty at index {i}");

                Assert(!RiverMath.IsInRiver(a.worldPos), $"Expanded building {i} ({a.rowId}) must not be inside river");

                if (a.isEastBank) eastCount++;
                else westCount++;

                float mapY = a.worldPos.z / RiverMath.MapScale + RiverMath.WorldH * 0.5f;
                float riverCxWorld = (RiverMath.RiverCenterMapX(mapY) - RiverMath.WorldW * 0.5f) * RiverMath.MapScale;
                Vector2 toRiver = new Vector2(riverCxWorld - a.worldPos.x, 0f).normalized;
                float yawRad = a.yawDeg * Mathf.Deg2Rad;
                Vector2 localPlusX = new Vector2(Mathf.Cos(yawRad), -Mathf.Sin(yawRad));
                float dot = Vector2.Dot(localPlusX, toRiver);
                Assert(dot > 0.70f, $"Building {i} ({a.rowId}) must face river (dot={dot:F3})");

                Vector2 posXZ = new Vector2(a.worldPos.x, a.worldPos.z);
                for (int p = 0; p < protectedWorldXZ.Length; p++)
                {
                    float dist = Vector2.Distance(posXZ, protectedWorldXZ[p]);
                    Assert(dist >= 6.0f, $"Building {i} ({a.rowId}) too close to protected hub/dermaga/spawn #{p} ({dist:F2}m < 6.0m)");
                }
            }

            Assert(westCount >= 20 && eastCount >= 20, $"Both banks populated (west={westCount}, east={eastCount})");
        }

        private static void VerifyAmbientRiverNpcs()
        {
            var runA = MapJsonImporter.ExpandDefaultMapNpcGroups();
            var runB = MapJsonImporter.ExpandDefaultMapNpcGroups();

            Assert(runA.Count > 0, "npc_group expansion produces ambient NPCs");
            Assert(runA.Count == runB.Count, $"npc_group expansion count is deterministic ({runA.Count} vs {runB.Count})");

            int kidsCount = 0;
            int fisherCount = 0;
            int washerCount = 0;
            int chatterCount = 0;

            Vector2[] protectedMapPoints = new Vector2[]
            {
                new Vector2(195f, 1185f), // Bank Sampah
                new Vector2(195f, 1085f), // Koperasi Desa
                new Vector2(285f, 1280f), // Gudang Pengepul
                new Vector2(220f, 720f),  // Pos Medis B3
                new Vector2(760f, 475f),  // Karantina Biohazard
                new Vector2(378f, 1210f), // Dermaga Awal
                new Vector2(645f, 615f),  // Dermaga Tengah
                new Vector2(310f, 1210f)  // Spawn
            };
            Vector2[] protectedWorldXZ = new Vector2[protectedMapPoints.Length];
            for (int p = 0; p < protectedMapPoints.Length; p++)
            {
                Vector3 wp = RiverMath.ToWorld3D(protectedMapPoints[p].x, protectedMapPoints[p].y, 0f);
                protectedWorldXZ[p] = new Vector2(wp.x, wp.z);
            }

            for (int i = 0; i < runA.Count; i++)
            {
                KaliNpcBuilder.ExpandedNpc a = runA[i];
                KaliNpcBuilder.ExpandedNpc b = runB[i];

                Assert(a.groupId == b.groupId, $"Deterministic NPC groupId at index {i}");
                Assert(a.role == b.role, $"Deterministic NPC role at index {i}");
                Assert(a.subBehavior == b.subBehavior, $"Deterministic NPC subBehavior at index {i}");
                Assert(Vector3.Distance(a.worldPos, b.worldPos) < 0.0001f, $"Deterministic NPC worldPos at index {i}");
                Assert(Mathf.Abs(a.yawDeg - b.yawDeg) < 0.0001f, $"Deterministic NPC yawDeg at index {i}");
                Assert(Mathf.Abs(a.uniformScale - b.uniformScale) < 0.0001f, $"Deterministic NPC scale at index {i}");

                switch (a.role)
                {
                    case AmbientNpcRole.Kids:
                        kidsCount++;
                        Assert(a.uniformScale >= 0.58f && a.uniformScale <= 0.72f, $"Kid uniform scale in ~0.6-0.7 range (got {a.uniformScale:F2})");
                        if (a.subBehavior == AmbientNpcSubBehavior.KidWader)
                        {
                            Assert(!a.onJetty, $"KidWader {a.groupId} must be in shallow water, not on dry jetty deck");
                        }
                        if (a.subBehavior == AmbientNpcSubBehavior.KidJettyJumper)
                        {
                            Assert(!KaliNpcBuilder.IsInBoatLane(a.jumpWaterPos), $"KidJettyJumper {a.groupId} jumpWaterPos must stay clear of boat lane");
                        }
                        if (a.subBehavior == AmbientNpcSubBehavior.KidChaser)
                        {
                            Vector3 pPlus = a.worldPos + a.chaseAxisWorld * a.chaseRadius;
                            Vector3 pMinus = a.worldPos - a.chaseAxisWorld * a.chaseRadius;
                            Assert(!KaliNpcBuilder.IsInBoatLane(pPlus) && !KaliNpcBuilder.IsInBoatLane(pMinus),
                                $"KidChaser {a.groupId} run track must stay out of boat lane");
                        }
                        if (!a.onJetty)
                        {
                            float mapX = a.worldPos.x / RiverMath.MapScale + RiverMath.WorldW * 0.5f;
                            float mapY = a.worldPos.z / RiverMath.MapScale + RiverMath.WorldH * 0.5f;
                            float cx = RiverMath.RiverCenterMapX(mapY);
                            float hw = RiverMath.RiverHalfWidthMap(mapY);
                            Assert(Mathf.Abs(mapX - cx) >= hw - 8f, $"Shallow kid {a.groupId} must stay near shallow edge, not deep channel");
                        }
                        break;
                    case AmbientNpcRole.Fisher:
                        fisherCount++;
                        break;
                    case AmbientNpcRole.Washer:
                        washerCount++;
                        break;
                    case AmbientNpcRole.Chatter:
                        chatterCount++;
                        break;
                }

                if (!a.onJetty)
                {
                    Assert(!KaliNpcBuilder.IsInBoatLane(a.worldPos), $"NPC {i} ({a.groupId}) must not sit inside boat lane");
                }

                Vector2 posXZ = new Vector2(a.worldPos.x, a.worldPos.z);
                for (int p = 0; p < protectedWorldXZ.Length; p++)
                {
                    float dist = Vector2.Distance(posXZ, protectedWorldXZ[p]);
                    Assert(dist >= 4.0f, $"NPC {i} ({a.groupId}) too close to protected hub/dermaga/spawn #{p} ({dist:F2}m < 4.0m)");
                }
            }

            Assert(kidsCount >= 6 && kidsCount <= 10, $"Kids count 6-10 (got {kidsCount})");
            Assert(fisherCount >= 4 && fisherCount <= 6, $"Fisher count 4-6 (got {fisherCount})");
            Assert(washerCount >= 4 && washerCount <= 6, $"Washer count 4-6 (got {washerCount})");
            Assert(chatterCount >= 3 && chatterCount <= 5, $"Chatter count 3-5 (got {chatterCount})");

            // Scene validation when _KALI_World/NPCs is baked
            GameObject npcsRoot = GameObject.Find("_KALI_World/NPCs");
            if (npcsRoot != null)
            {
                KaliAmbientNpc[] sceneNpcs = npcsRoot.GetComponentsInChildren<KaliAmbientNpc>(true);
                Assert(sceneNpcs.Length == runA.Count, $"Scene NPC count matches expansion ({sceneNpcs.Length} vs {runA.Count})");
                for (int i = 0; i < sceneNpcs.Length; i++)
                {
                    Collider[] cols = sceneNpcs[i].GetComponentsInChildren<Collider>(true);
                    for (int c = 0; c < cols.Length; c++)
                    {
                        Assert(cols[c].isTrigger, $"NPC {sceneNpcs[i].name} must not have blocking collider ({cols[c].name})");
                    }
                    Animator anim = sceneNpcs[i].GetComponent<Animator>();
                    if (anim != null)
                    {
                        Assert(anim.cullingMode == AnimatorCullingMode.CullUpdateTransforms, $"NPC {sceneNpcs[i].name} must use CullUpdateTransforms");
                    }
                    if (sceneNpcs[i].role == AmbientNpcRole.Fisher && sceneNpcs[i].rodBobber != null)
                    {
                        Vector3 bobPos = sceneNpcs[i].rodBobber.position;
                        Assert(bobPos.y >= -0.35f && bobPos.y <= 0.05f,
                            $"Fisher {sceneNpcs[i].name} bobber must rest on water surface (got y={bobPos.y:F2})");
                        Assert(RiverMath.IsInRiver(bobPos),
                            $"Fisher {sceneNpcs[i].name} bobber must hang over river water (got {bobPos:F2})");
                    }
                }
            }

            // Runtime day/night fade + monsoon evacuation verification
            KaliDayNightCycle prevCycle = KaliDayNightCycle.Instance;
            PropertyInfo cycleInstProp = typeof(KaliDayNightCycle).GetProperty("Instance", BindingFlags.Public | BindingFlags.Static);
            cycleInstProp?.SetValue(null, null);
            try
            {
                using (QaContext ctx = new QaContext())
                {
                    RiverGameManager gm = ctx.Manager;
                    GameObject rig = ctx.Track(new GameObject("QA_NpcDayNightRig"));
                    GameObject sunGo = ctx.Track(new GameObject("Sun"));
                    sunGo.transform.SetParent(rig.transform, false);
                    sunGo.AddComponent<Light>().type = LightType.Directional;
                    KaliDayNightCycle cycle = rig.AddComponent<KaliDayNightCycle>();
                    InvokeNonPublic(cycle, "Awake");

                    GameObject kidGo = ctx.Track(GameObject.CreatePrimitive(PrimitiveType.Capsule));
                    UnityEngine.Object.DestroyImmediate(kidGo.GetComponent<Collider>());
                    Renderer kidR = kidGo.GetComponent<Renderer>();
                    KaliAmbientNpc kidNpc = kidGo.AddComponent<KaliAmbientNpc>();
                    kidNpc.role = AmbientNpcRole.Kids;
                    kidNpc.subBehavior = AmbientNpcSubBehavior.KidWader;
                    kidNpc.anchorWorldPos = Vector3.zero;
                    kidNpc.anchorWorldRot = Quaternion.identity;
                    kidNpc.baseUniformScale = 0.65f;
                    InvokeNonPublic(kidNpc, "Awake");

                    GameObject washerGo = ctx.Track(GameObject.CreatePrimitive(PrimitiveType.Capsule));
                    UnityEngine.Object.DestroyImmediate(washerGo.GetComponent<Collider>());
                    Renderer washerR = washerGo.GetComponent<Renderer>();
                    KaliAmbientNpc washerNpc = washerGo.AddComponent<KaliAmbientNpc>();
                    washerNpc.role = AmbientNpcRole.Washer;
                    washerNpc.subBehavior = AmbientNpcSubBehavior.CrouchedWasher;
                    washerNpc.anchorWorldPos = Vector3.zero;
                    washerNpc.anchorWorldRot = Quaternion.identity;
                    washerNpc.baseUniformScale = 1f;
                    InvokeNonPublic(washerNpc, "Awake");

                    GameObject fisherGo = ctx.Track(GameObject.CreatePrimitive(PrimitiveType.Capsule));
                    UnityEngine.Object.DestroyImmediate(fisherGo.GetComponent<Collider>());
                    Renderer fisherR = fisherGo.GetComponent<Renderer>();
                    KaliAmbientNpc fisherNpc = fisherGo.AddComponent<KaliAmbientNpc>();
                    fisherNpc.role = AmbientNpcRole.Fisher;
                    fisherNpc.subBehavior = AmbientNpcSubBehavior.StandingFisher;
                    fisherNpc.anchorWorldPos = Vector3.zero;
                    fisherNpc.anchorWorldRot = Quaternion.identity;
                    fisherNpc.baseUniformScale = 1f;
                    InvokeNonPublic(fisherNpc, "Awake");

                    cycle.SetHour(12f);
                    kidNpc.StepSimulation(2f);
                    washerNpc.StepSimulation(2f);
                    fisherNpc.StepSimulation(2f);
                    Assert(kidR.enabled && washerR.enabled && fisherR.enabled, "Ambient NPCs stay visible at noon");

                    cycle.SetHour(22.5f);
                    kidNpc.StepSimulation(2f);
                    washerNpc.StepSimulation(2f);
                    fisherNpc.StepSimulation(2f);
                    Assert(!kidR.enabled && !washerR.enabled && !fisherR.enabled, "Ambient NPCs hide/fade out at night (22:30)");

                    cycle.SetHour(12f);
                    kidNpc.StepSimulation(2f);
                    washerNpc.StepSimulation(2f);
                    fisherNpc.StepSimulation(2f);
                    Assert(kidR.enabled && washerR.enabled && fisherR.enabled, "Ambient NPCs return in daytime");

                    gm.isMonsoonStorm = true;
                    kidNpc.StepSimulation(2f);
                    washerNpc.StepSimulation(2f);
                    fisherNpc.StepSimulation(2f);
                    Assert(!kidR.enabled && !washerR.enabled, "Kids and washers leave water during monsoon storm");
                    Assert(fisherR.enabled, "Bank/jetty fisher stays outside monsoon water evacuation rule");
                }
            }
            finally
            {
                cycleInstProp?.SetValue(null, prevCycle);
            }
        }

        // Station root at pos with its <name>_ServicePoint (r = 2 m trigger) 4 m out on +X, like MapJsonImporter.
        private static GameObject MakeStation(QaContext ctx, string name, Vector3 pos)
        {
            GameObject root = ctx.Track(new GameObject(name));
            root.transform.position = pos;
            GameObject sp = new GameObject(name + KaliPlayerController.ServicePointSuffix);
            sp.transform.SetParent(root.transform, false);
            sp.transform.localPosition = new Vector3(4f, 0f, 0f);
            SphereCollider sc = sp.AddComponent<SphereCollider>();
            sc.isTrigger = true;
            sc.radius = 2f;
            Physics.SyncTransforms();
            return root;
        }

        // Stands the player just inside the service point, facing the station counter (-X).
        private static void PlaceAtServicePoint(GameObject playerGo, Vector3 stationPos)
        {
            playerGo.transform.position = stationPos + new Vector3(5f, 1f, 0f);
            playerGo.transform.rotation = Quaternion.LookRotation(Vector3.left);
            Physics.SyncTransforms();
        }

        private static void InvokeNonPublic(object target, string methodName, params object[] args)
        {
            MethodInfo mi = target.GetType().GetMethod(methodName, BindingFlags.Instance | BindingFlags.NonPublic);
            if (mi == null) throw new InvalidOperationException($"Missing method {target.GetType().Name}.{methodName}");
            mi.Invoke(target, args);
        }

        private static int assertCount;

        private static void Assert(bool condition, string message)
        {
            assertCount++;
            if (!condition) throw new InvalidOperationException($"[KALI QA FAIL] {message}");
        }

        private static void AssertApprox(float expected, float actual, float tol, string label)
        {
            assertCount++;
            if (Mathf.Abs(expected - actual) > tol)
            {
                throw new InvalidOperationException($"[KALI QA FAIL] {label}: expected {expected} +/- {tol}, got {actual}");
            }
        }
    }
}
#endif
