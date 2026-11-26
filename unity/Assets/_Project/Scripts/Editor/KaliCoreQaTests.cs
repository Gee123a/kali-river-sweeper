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

            public QaContext(bool isolateSceneGunungNodes = false)
            {
                prevInstance = RiverGameManager.Instance;
                SetManagerInstance(null);

                if (isolateSceneGunungNodes)
                {
                    foreach (GunungNodeController node in UnityEngine.Object.FindObjectsOfType<GunungNodeController>(true))
                    {
                        savedNodes.Add((node, node.nodeHealth, node.transform.localScale, node.transform.position, node.gameObject.activeSelf));
                        node.nodeHealth = 0f;
                    }
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
                VerifyChildColliderLookupAndSingleEndingGuard
            };

            for (int i = 0; i < suite.Length; i++)
            {
                suite[i]();
            }

            Debug.Log($"[KALI QA] PASS: {suite.Length}/{suite.Length} core verification suites passed.");
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

                // Wrong station: Biohazard at BankSampah (fine Rp 8,000, -12 Trust)
                int trustBefore = gm.communityTrust;
                int fineBio = gm.DiscardWasteAtStation(DiscardStationType.BankSampah, WasteClass.Biohazard);
                Assert(fineBio == -8000 && gm.rupiah == 0 && gm.totalFinesPaid == 8000, "Wrong station Biohazard fine");
                Assert(gm.wrongDiscardCount == 1 && gm.communityTrust == trustBefore - 12, "Wrong discard count and trust loss");

                // Sorted Pos Sortir bonus with Trash Boom (Rp 7,500)
                gm.trashBoomActive = true;
                gm.TryPickupWaste(WasteClass.Normal, 1);
                Assert(gm.DiscardWasteAtStation(DiscardStationType.BankSampah, WasteClass.Normal, sortedAtPosSortir: true) == 7500, "Pos Sortir bonus payout");

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
            }
        }

        private static void VerifyBiohazardDotAndHealthFail()
        {
            using (QaContext ctx = new QaContext())
            {
                RiverGameManager gm = ctx.Manager;

                // #10 Capitan Ular guarantees 0% medical prick risk
                InvokeNonPublic(gm, "AddEarnings", 80000);
                Assert(gm.equippedToolIndex == ToolCatalog.SnakeGrabberIndex, "80,000 Rp equips #10 Capitan Ular");
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
                Assert(gm.highestUnlockedToolIndex == 6 && gm.equippedToolIndex == 6 && gm.galahUnlocked, "30k unlocks #06 + galah");
                Assert(unlockedCount == 5 && equipChangedCount == 1, "Fired OnToolUnlocked for #2..#6");

                Assert(gm.BuyKampungBins() && gm.kampungBinsInstalled, "Spend 30k on Kampung Bins");
                Assert(gm.rupiah == 0 && gm.cumulativeEarnings == 30000 && gm.highestUnlockedToolIndex == 6, "Spending rupiah preserves tool unlocks");

                Assert(gm.SelectTool(1) && gm.equippedToolIndex == 1, "SelectTool #01");
                Assert(gm.SelectTool(20) && gm.equippedToolIndex == 6, "SelectTool clamps to highestUnlockedToolIndex");
                gm.CycleTool(-1);
                Assert(gm.equippedToolIndex == 5, "CycleTool decrements cleanly");
                gm.SelectTool(1);
                gm.CycleTool(-1);
                Assert(gm.equippedToolIndex == 6, "CycleTool wraps backwards to highest unlocked");
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

                // Unlock #13 Ganco Ganda Winch
                InvokeNonPublic(gm, "AddEarnings", 140000);
                Assert(gm.highestUnlockedToolIndex == 13, "140k unlocks #13 Ganco Ganda Winch");

                int tierBreaches = 0;
                Vector3 lastBreachPos = Vector3.zero;
                gm.OnGunungTierBreached += p => { tierBreaches++; lastBreachPos = p; };
                GameEnding victoryEnding = GameEnding.None;
                gm.OnEndingTriggered += e => victoryEnding = e;

                Vector3 hitPos = new Vector3(2f, 3f, -68f);
                node.ApplyDamage(0.30f); // 1.0 -> 0.70 (Tier 4 -> 3)
                gm.DamageGunungSampah(0.10f, hitPos);
                Assert(tierBreaches == 1 && lastBreachPos == hitPos, "OnGunungTierBreached fires with impactPos on tier drop");

                node.ApplyDamage(0.30f); // 0.70 -> 0.40 (Tier 3 -> 2)
                gm.DamageGunungSampah(0.10f, hitPos);
                Assert(tierBreaches == 2, "Second Gunung tier breach");

                node.ApplyDamage(0.40f); // 0.40 -> 0.00 (Tier 2 -> 0 -> CompleteCleanBreach)
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
                gm.RegisterActiveTrash(10);
                gm.TriggerEmergencyFlush();
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

                if (Time.deltaTime > 0f)
                {
                    GameEnding timerVictory = GameEnding.None;
                    gm.OnEndingTriggered += e => timerVictory = e;
                    gm.monsoonCountdownRemaining = Mathf.Min(0.0001f, Time.deltaTime * 0.5f);
                    InvokeNonPublic(gm, "Update");
                    Assert(gm.activeEnding == GameEnding.TrueSdgVictory && timerVictory == GameEnding.TrueSdgVictory, "Monsoon countdown 0 triggers TrueSdgVictory");
                }
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
                InvokeNonPublic(gm, "AddEarnings", 140000); // Unlock #13 Ganco Ganda Winch

                Vector3 isolatedPos = new Vector3(5000f, 5000f, 5000f);
                GameObject hubRoot = ctx.Track(new GameObject("Bank Sampah Berkah"));
                hubRoot.transform.position = isolatedPos;
                GameObject hubChild = ctx.Track(new GameObject("SM_Env_BankSampah_Mesh"));
                hubChild.transform.SetParent(hubRoot.transform, false);
                hubChild.AddComponent<BoxCollider>();

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

                MethodInfo findHub = typeof(KaliPlayerController).GetMethod("TryFindNearestHub", BindingFlags.Instance | BindingFlags.NonPublic, null, new[] { typeof(DiscardStationType).MakeByRefType(), typeof(bool).MakeByRefType(), typeof(bool).MakeByRefType() }, null);
                if (findHub == null) throw new InvalidOperationException("Missing KaliPlayerController.TryFindNearestHub");
                object[] hubArgs = new object[] { DiscardStationType.GudangPengepul, false, false };
                bool foundHub = (bool)findHub.Invoke(player, hubArgs);
                Assert(foundHub && (DiscardStationType)hubArgs[0] == DiscardStationType.BankSampah, "Child collider matches parent Bank Sampah hub");

                int hubEvents = 0;
                bool lastNear = false;
                string lastHubName = string.Empty;
                player.OnNearbyHubChanged += (near, st, sortir, toko, hubName) => { hubEvents++; lastNear = near; lastHubName = hubName; };
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
                gm.AddPiledTrash(131); // currentWaterLevelY >= fatalFloodWaterY (2.45f)
                Assert(gm.currentWaterLevelY >= gm.fatalFloodWaterY, "Flood threshold active");

                int endingCount = 0;
                GameEnding lastEnding = GameEnding.None;
                gm.OnEndingTriggered += e => { endingCount++; lastEnding = e; };

                if (Time.deltaTime > 0f)
                {
                    gm.TryPickupWaste(WasteClass.Biohazard, 1);
                    gm.biohazardExposureTimer = gm.biohazardGraceSeconds;
                    gm.playerHealth = 0.0001f;
                    InvokeNonPublic(gm, "Update");
                }
                else
                {
                    InvokeNonPublic(gm, "ApplyPlayerDamage", gm.playerHealth + 1f, true);
                    InvokeNonPublic(gm, "Update");
                }

                Assert(endingCount == 1 && gm.activeEnding == GameEnding.HealthFail && lastEnding == GameEnding.HealthFail, "HealthFail is not overwritten by FloodFail");
            }
        }

        private static void InvokeNonPublic(object target, string methodName, params object[] args)
        {
            MethodInfo mi = target.GetType().GetMethod(methodName, BindingFlags.Instance | BindingFlags.NonPublic);
            if (mi == null) throw new InvalidOperationException($"Missing method {target.GetType().Name}.{methodName}");
            mi.Invoke(target, args);
        }

        private static void Assert(bool condition, string message)
        {
            if (!condition) throw new InvalidOperationException($"[KALI QA FAIL] {message}");
        }

        private static void AssertApprox(float expected, float actual, float tol, string label)
        {
            if (Mathf.Abs(expected - actual) > tol)
            {
                throw new InvalidOperationException($"[KALI QA FAIL] {label}: expected {expected} +/- {tol}, got {actual}");
            }
        }
    }
}
#endif
