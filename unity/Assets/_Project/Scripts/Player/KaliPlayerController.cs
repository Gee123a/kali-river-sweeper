using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.EventSystems;
using KaliRiverSweeper.Core;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem;
#endif

namespace KaliRiverSweeper.Player
{
    [RequireComponent(typeof(CharacterController))]
    public class KaliPlayerController : MonoBehaviour
    {
        [Header("Movement & Boat")]
        public float walkSpeed = 6.5f;
        public float sprintSpeed = 10.5f;
        public float boatSpeed = 10.0f;
        public float boatRideHeight = 0.80f;
        public float freeCamSpeed = 18f;
        public float mouseSensitivity = 2.2f;
        public float interactRange = 7.5f;
        public float dockInteractRange = 8.5f;

        [Header("Tool Socket (Optional)")]
        public Transform toolSocket;
        public GameObject[] toolPrefabs;

        [Header("State")]
        public bool isInBoat;
        public bool isFreeCam;

        public event Action<bool, DiscardStationType, bool, string> OnNearbyHubChanged;
        public event Action<bool, bool, string> OnNearbyDermagaChanged;
        public event Action OnShopRequested;
        public event Action<bool> OnBoatStateChanged;
        public event Action<bool> OnFreeCamStateChanged;
        public event Action<bool, WasteClass, bool, float> OnAimTargetChanged;

        public bool IsInBoat => isInBoat;
        public bool IsFreeCam => isFreeCam;
        public float NextScoopTime => nextScoopTime;
        public float ScoopCooldownProgress
        {
            get
            {
                float rem = nextScoopTime - Time.time;
                if (rem <= 0f) return 1f;
                float cd = RiverGameManager.Instance != null ? Mathf.Max(0.05f, RiverGameManager.Instance.EquippedTool.Cooldown) : 0.45f;
                return Mathf.Clamp01(1f - (rem / cd));
            }
        }

        public bool HasNearbyHub { get; private set; }
        public DiscardStationType NearbyStationType { get; private set; }
        public bool NearbyIsKopdes { get; private set; }
        public string NearbyHubName { get; private set; } = string.Empty;
        public bool HasNearbyDermaga { get; private set; }
        public bool NearbyDermagaIsInBoat { get; private set; }
        public string NearbyDermagaName { get; private set; } = string.Empty;

        private const float HubPollInterval = 0.1f;

        private CharacterController controller;
        private Camera cam;
        private Vector3 initialSpawnPos;
        private float initialYaw;
        private float yaw;
        private float pitch;
        private float verticalVel;
        private float nextScoopTime;
        private float nextPaddleSplashTime;
        private float nextHubPollTime;
        private float nextRiverGuardAlertTime;
        private float qHoldTimer;
        private bool qHoldWarned;
        private float flushHoldTimer;
        private bool flushHoldWarned;
        private bool lastAimHasTarget;
        private WasteClass lastAimClass;
        private bool lastAimInReach;
        private float lastAimPrick = -1f;
        private int lastEquippedVisualIndex = -1;
        private GameObject activeToolVisual;
        private Quaternion toolSocketBaseRot = Quaternion.identity;
        private float toolSwingTimer;

        private void Awake()
        {
            controller = GetComponent<CharacterController>();
            cam = GetComponentInChildren<Camera>();
            initialSpawnPos = transform.position;
            yaw = transform.eulerAngles.y;
            initialYaw = yaw;

#if !ENABLE_INPUT_SYSTEM && !ENABLE_LEGACY_INPUT_MANAGER
            Debug.LogWarning("[KALI] Neither Unity Input System nor Legacy Input Manager is active in Player Settings. Player controls will be disabled.");
#endif
        }

        public void ResetToInitialSpawn()
        {
            isInBoat = false;
            if (isFreeCam)
            {
                isFreeCam = false;
                OnFreeCamStateChanged?.Invoke(false);
            }
            OnBoatStateChanged?.Invoke(false);
            verticalVel = 0f;
            yaw = initialYaw;
            pitch = 0f;
            qHoldTimer = 0f;
            flushHoldTimer = 0f;
            transform.rotation = Quaternion.Euler(0f, yaw, 0f);
            if (cam != null) cam.transform.localRotation = Quaternion.identity;
            TeleportPlayer(initialSpawnPos);
            RefreshNearbyHub();
        }

        private void Start()
        {
            if (toolSocket != null) toolSocketBaseRot = toolSocket.localRotation;
            if (RiverGameManager.Instance != null)
            {
                RiverGameManager.Instance.OnEquippedToolChanged += OnEquippedToolChanged;
                OnEquippedToolChanged(RiverGameManager.Instance.EquippedTool);
            }
            RefreshNearbyHub();
        }

        private void OnDestroy()
        {
            if (RiverGameManager.Instance != null)
            {
                RiverGameManager.Instance.OnEquippedToolChanged -= OnEquippedToolChanged;
            }
        }

        private void Update()
        {
            RiverGameManager gm = RiverGameManager.Instance;
            if (gm != null && gm.activeEnding != GameEnding.None)
            {
                if (WasKeyPressed(KeyAction.R))
                {
                    gm.RestartRun();
                }
                return;
            }

            if (toolSwingTimer > 0f && toolSocket != null)
            {
                toolSwingTimer = Mathf.Max(0f, toolSwingTimer - Time.deltaTime * 4f);
                toolSocket.localRotation = toolSocketBaseRot * Quaternion.Euler(Mathf.Sin(toolSwingTimer * Mathf.PI) * 32f, 0f, 0f);
            }

            HandleLook();
            HandleActions();
            HandleMove();
            if (Time.unscaledTime >= nextHubPollTime)
            {
                nextHubPollTime = Time.unscaledTime + HubPollInterval;
                RefreshNearbyHub();
                RefreshAimTarget();
            }
        }

        private void HandleLook()
        {
            if (WasRightMousePressed())
            {
                Cursor.lockState = Cursor.lockState == CursorLockMode.Locked ? CursorLockMode.None : CursorLockMode.Locked;
            }

            if (Cursor.lockState == CursorLockMode.Locked || IsRightMouseHeld())
            {
                Vector2 look = GetLookDelta();
                yaw += look.x * mouseSensitivity;
                pitch = Mathf.Clamp(pitch - look.y * mouseSensitivity, -80f, 80f);
                transform.rotation = Quaternion.Euler(0f, yaw, 0f);
                if (cam != null) cam.transform.localRotation = Quaternion.Euler(pitch, 0f, 0f);
            }
        }

        private void HandleMove()
        {
            Vector2 moveAxis = GetMoveAxis();
            Vector3 dir = (transform.right * moveAxis.x + transform.forward * moveAxis.y).normalized;

            if (isFreeCam)
            {
                float up = (IsKeyHeld(KeyAction.E) ? 1f : 0f) - (IsKeyHeld(KeyAction.Q) ? 1f : 0f);
                Vector3 nextFree = transform.position + (dir * freeCamSpeed + Vector3.up * (up * freeCamSpeed)) * Time.deltaTime;
                nextFree.x = Mathf.Clamp(nextFree.x, -64f, 64f);
                nextFree.y = Mathf.Clamp(nextFree.y, 0.5f, 55f);
                nextFree.z = Mathf.Clamp(nextFree.z, -88f, 88f);
                transform.position = nextFree;
                return;
            }

            RiverGameManager gm = RiverGameManager.Instance;
            float waterY = gm != null ? gm.currentWaterLevelY : 0f;
            float speed = isInBoat ? boatSpeed : (IsShiftHeld() ? sprintSpeed : walkSpeed);

            Vector3 horizMove;
            if (!isInBoat)
            {
                if (transform.position.y < waterY - 0.35f)
                {
                    // Wading/flooded slow-down without trapping player
                    speed *= 0.65f;
                }
                if (controller.isGrounded)
                {
                    verticalVel = WasKeyPressed(KeyAction.Space) ? 6.5f : -1f;
                }
                else
                {
                    verticalVel -= 18f * Time.deltaTime;
                }

                // Bank climb-out recovery: if player slipped into riverbed on foot, lift gently when moving toward bank
                if (!IsFootPositionPermitted(transform.position) && transform.position.y < 1.35f && dir.sqrMagnitude > 0.01f)
                {
                    verticalVel = Mathf.Max(verticalVel, 4.2f);
                }

                Vector3 rawStep = dir * (speed * Time.deltaTime);
                horizMove = ResolvePermittedMoveOnFoot(transform.position, rawStep, gm);
            }
            else
            {
                float targetBoatY = waterY + boatRideHeight;
                verticalVel = (targetBoatY - transform.position.y) * 5.0f;
                float stormMult = gm != null && gm.isMonsoonStorm ? 2.2f : 1f;
                Vector3 rawStep = (dir * speed + Vector3.forward * (0.45f * stormMult)) * Time.deltaTime;
                horizMove = ResolvePermittedMoveInBoat(transform.position, rawStep, gm);
            }

            Vector3 move = horizMove + Vector3.up * (verticalVel * Time.deltaTime);
            controller.Move(move);

            if (isInBoat && gm != null && dir.sqrMagnitude > 0.05f && Time.time >= nextPaddleSplashTime)
            {
                nextPaddleSplashTime = Time.time + 0.45f;
                gm.NotifyWaterSplash(new Vector3(transform.position.x, waterY, transform.position.z));
            }
        }

        private void HandleActions()
        {
            RiverGameManager gm = RiverGameManager.Instance;

            if (WasKeyPressed(KeyAction.F) && (isFreeCam || (gm != null && gm.demoHotkeysArmed)))
            {
                isFreeCam = !isFreeCam;
                OnFreeCamStateChanged?.Invoke(isFreeCam);
                gm?.NotifyInfo(isFreeCam ? "Free-Cam Demo aktif (dibatasi di area sungai)." : "Kembali ke kamera gameplay.");
            }

            if (WasKeyPressed(KeyAction.R) && gm != null && gm.demoHotkeysArmed)
            {
                gm.SetWeather(!gm.isMonsoonStorm);
            }

            // Tool switching via Mouse Scroll or [ / ]
            if (gm != null)
            {
                float scroll = GetScrollDelta();
                if (scroll > 0.01f || WasKeyPressed(KeyAction.BracketRight))
                {
                    gm.CycleTool(1);
                }
                else if (scroll < -0.01f || WasKeyPressed(KeyAction.BracketLeft))
                {
                    gm.CycleTool(-1);
                }
            }

            // High-ground cargo dump (0.5s hold on Q) when not in Free-Cam
            if (!isFreeCam && gm != null && IsKeyHeld(KeyAction.Q))
            {
                if (gm.cargoCount > 0)
                {
                    if (!qHoldWarned)
                    {
                        qHoldWarned = true;
                        int hazardQty = gm.medicalCargo + gm.biohazardCargo;
                        if (!gm.IsSellLocked && hazardQty > 0)
                        {
                            gm.NotifyInfo($"Tahan [Q] 0.5 detik untuk buang kargo (penalti -{hazardQty * 2} Trust sebelum Sell-Lock)...", true);
                        }
                        else
                        {
                            gm.NotifyInfo("Tahan [Q] 0.5 detik untuk buang kargo di daratan tinggi...");
                        }
                    }
                    qHoldTimer += Time.deltaTime;
                    if (qHoldTimer >= 0.5f)
                    {
                        qHoldTimer = 0f;
                        qHoldWarned = false;
                        gm.DumpCargoOnHighGround();
                    }
                }
            }
            else
            {
                qHoldTimer = 0f;
                qHoldWarned = false;
            }

            // Emergency Flush hotkey (1.5s hold on Shift + X) during flood Sell-Lock crisis
            if (!isFreeCam && gm != null && IsShiftHeld() && IsKeyHeld(KeyAction.X))
            {
                if (!gm.IsSellLocked)
                {
                    if (!flushHoldWarned)
                    {
                        flushHoldWarned = true;
                        gm.TriggerEmergencyFlush(confirmed: false);
                    }
                }
                else
                {
                    if (!flushHoldWarned)
                    {
                        flushHoldWarned = true;
                        gm.NotifyInfo("TAHAN [Shift + X] 1.5 detik untuk konfirmasi Emergency Flush ke laut!", true);
                    }
                    flushHoldTimer += Time.deltaTime;
                    if (flushHoldTimer >= 1.5f)
                    {
                        flushHoldTimer = 0f;
                        flushHoldWarned = false;
                        gm.TriggerEmergencyFlush(confirmed: true);
                    }
                }
            }
            else
            {
                flushHoldTimer = 0f;
                flushHoldWarned = false;
            }

            // Station Quick-Discard (1/2/3), Kopdes explicit upgrade selection (1-4), & Safe Deposit / Boat Toggle (E)
            if (gm != null && !isFreeCam && !gm.IsDemoHotkeyBusy)
            {
                bool nearStation = TryFindNearestHub(out DiscardStationType station, out bool isKopdes);
                if (nearStation && !isKopdes)
                {
                    if (WasKeyPressed(KeyAction.Digit1)) gm.DiscardWasteAtStation(station, WasteClass.Normal);
                    else if (WasKeyPressed(KeyAction.Digit2)) gm.DiscardWasteAtStation(station, WasteClass.Medical);
                    else if (WasKeyPressed(KeyAction.Digit3)) gm.DiscardWasteAtStation(station, WasteClass.Biohazard);
                }
                else if (nearStation && isKopdes && OnShopRequested == null)
                {
                    HandleKopdesKeySelection(gm);
                }
            }

            if (WasKeyPressed(KeyAction.E) && !isFreeCam)
            {
                if (!TryInteractWithNearbyHub())
                {
                    TryToggleBoat(gm);
                }
            }

            bool pointerOverUi = EventSystem.current != null && EventSystem.current.IsPointerOverGameObject();
            if (WasLeftMousePressed() && !isFreeCam && !pointerOverUi)
            {
                TryScoopOrDredge();
            }
        }

        private static void HandleKopdesKeySelection(RiverGameManager gm)
        {
            if (WasKeyPressed(KeyAction.Digit1))
            {
                if (!gm.BuyKampungBins()) gm.NotifyInfo("Tong Sampah Kampung sudah terpasang atau Rupiah belum cukup (Rp 30.000).", true);
            }
            else if (WasKeyPressed(KeyAction.Digit2))
            {
                if (gm.BuyUpgrade(UpgradeTier.WoodenSampan)) gm.NotifyInfo("Perahu Sampan Kayu dibeli di Kopdes! (Kapasitas 22)");
                else gm.NotifyInfo("Perahu Sampan Kayu sudah dimiliki atau Rupiah belum cukup (Rp 40.000).", true);
            }
            else if (WasKeyPressed(KeyAction.Digit3))
            {
                if (gm.BuyUpgrade(UpgradeTier.TrashBoom)) gm.NotifyInfo("Trash Boom aktif! (+Rp 2.500/4s)");
                else gm.NotifyInfo("Trash Boom sudah aktif atau Rupiah belum cukup (Rp 75.000).", true);
            }
            else if (WasKeyPressed(KeyAction.Digit4))
            {
                if (gm.BuyUpgrade(UpgradeTier.AmphibiousExcavator)) gm.NotifyInfo("Pindad Amphibious Excavator terbuka! Keruk Gunung Sampah!");
                else gm.NotifyInfo("Excavator sudah terbuka atau Rupiah belum cukup (Rp 120.000).", true);
            }
        }

        /// <summary>
        /// Refreshes nearby hub and Dermaga port proximity state, emitting change events only on transitions.
        /// </summary>
        public void RefreshNearbyHub()
        {
            bool found = TryFindNearestHub(out DiscardStationType station, out bool isKopdes, out string hubName);
            string resolvedName = found ? (hubName ?? string.Empty) : string.Empty;
            if (found != HasNearbyHub ||
                (found && (station != NearbyStationType || isKopdes != NearbyIsKopdes || resolvedName != NearbyHubName)))
            {
                HasNearbyHub = found;
                NearbyStationType = station;
                NearbyIsKopdes = isKopdes;
                NearbyHubName = resolvedName;
                OnNearbyHubChanged?.Invoke(found, station, isKopdes, resolvedName);
            }

            bool foundDock = TryFindNearestDermaga(transform.position, dockInteractRange, out _, out Transform dockRoot);
            string resolvedDock = foundDock && dockRoot != null ? dockRoot.name : string.Empty;
            if (foundDock != HasNearbyDermaga ||
                (foundDock && (isInBoat != NearbyDermagaIsInBoat || resolvedDock != NearbyDermagaName)))
            {
                HasNearbyDermaga = foundDock;
                NearbyDermagaIsInBoat = foundDock && isInBoat;
                NearbyDermagaName = resolvedDock;
                OnNearbyDermagaChanged?.Invoke(foundDock, isInBoat, resolvedDock);
            }
        }

        private static readonly (string token, DiscardStationType station, bool isShop)[] HubRules =
        {
            ("Bank Sampah", DiscardStationType.BankSampah, false),
            ("Pos Medis", DiscardStationType.PosMedisB3, false),
            ("Karantina Biohazard", DiscardStationType.KarantinaBiohazard, false),
            ("Gudang Pengepul", DiscardStationType.GudangPengepul, false),
            ("Koperasi Desa", DiscardStationType.BankSampah, true),
            ("Kopdes", DiscardStationType.BankSampah, true)
        };

        private bool TryFindNearestHub(out DiscardStationType stationType, out bool isKopdes)
        {
            return TryFindNearestHub(out stationType, out isKopdes, out _);
        }

        private bool TryFindNearestHub(out DiscardStationType stationType, out bool isKopdes, out string hubName)
        {
            stationType = DiscardStationType.BankSampah;
            isKopdes = false;
            hubName = string.Empty;

            Collider[] hits = Physics.OverlapSphere(transform.position, interactRange);
            float bestDistSq = float.MaxValue;
            bool found = false;

            foreach (Collider col in hits)
            {
                if (col == null) continue;

                Transform match = null;
                DiscardStationType candidateType = DiscardStationType.BankSampah;
                bool candidateShop = false;

                for (int i = 0; i < HubRules.Length; i++)
                {
                    match = FindHierarchyMatch(col.transform, HubRules[i].token);
                    if (match != null)
                    {
                        candidateType = HubRules[i].station;
                        candidateShop = HubRules[i].isShop;
                        break;
                    }
                }

                if (match == null) continue;

                float dSq = (SafeClosestPoint(col, transform.position) - transform.position).sqrMagnitude;
                if (dSq < bestDistSq)
                {
                    bestDistSq = dSq;
                    stationType = candidateType;
                    isKopdes = candidateShop;
                    hubName = match.name;
                    found = true;
                }
            }

            return found;
        }

        private bool TryInteractWithNearbyHub()
        {
            RiverGameManager gm = RiverGameManager.Instance;
            if (gm == null) return false;

            if (!TryFindNearestHub(out DiscardStationType station, out bool isKopdes))
            {
                return false;
            }

            if (isKopdes)
            {
                if (OnShopRequested != null) { OnShopRequested.Invoke(); return true; }
                gm.NotifyInfo("Kopdes: [1] Tong Kampung (30rb) | [2] Sampan (40rb) | [3] Trash Boom (75rb) | [4] Excavator (120rb)");
                return true;
            }

            gm.DiscardLegalAtStation(station);
            return true;
        }

        private bool TryToggleBoat(RiverGameManager gm)
        {
            if (!TryFindNearestDermaga(transform.position, dockInteractRange, out Collider dockCol, out Transform dockRoot))
            {
                gm?.NotifyInfo(
                    isInBoat
                        ? "Hanya bisa naik ke darat di Dermaga! (Dekati Dermaga Awal / Dermaga Tengah)"
                        : "Hanya bisa turun ke sungai & naik perahu di Dermaga!",
                    true);
                return false;
            }

            float waterY = gm != null ? gm.currentWaterLevelY : 0f;
            Bounds dockBounds = dockCol.bounds;
            float dockMapX = dockBounds.center.x / RiverMath.MapScale + RiverMath.WorldW * 0.5f;
            float dockMapY = Mathf.Clamp(dockBounds.center.z / RiverMath.MapScale + RiverMath.WorldH * 0.5f, 110f, RiverMath.WorldH);
            float cx = RiverMath.RiverCenterMapX(dockMapY);
            float hw = RiverMath.RiverHalfWidthMap(dockMapY);
            float cxWorld = (cx - RiverMath.WorldW * 0.5f) * RiverMath.MapScale;
            float hwWorld = hw * RiverMath.MapScale;
            bool dockOnEastSide = dockMapX >= cx;

            if (!isInBoat)
            {
                float waterX = dockOnEastSide ? dockBounds.min.x - 1.6f : dockBounds.max.x + 1.6f;
                float minRiverX = cxWorld - Mathf.Max(0.5f, hwWorld - 1.0f);
                float maxRiverX = cxWorld + Mathf.Max(0.5f, hwWorld - 1.0f);
                waterX = Mathf.Clamp(waterX, minRiverX, maxRiverX);

                isInBoat = true;
                verticalVel = 0f;
                TeleportPlayer(new Vector3(waterX, waterY + boatRideHeight, dockBounds.center.z));
                OnBoatStateChanged?.Invoke(true);
                RefreshNearbyHub();
                gm?.NotifyInfo($"Naik perahu dari {dockRoot.name}.");
                return true;
            }

            float bankEdgeWorldX = dockOnEastSide ? (cxWorld + hwWorld + 1.2f) : (cxWorld - hwWorld - 1.2f);
            float landX = dockOnEastSide
                ? Mathf.Max(dockBounds.center.x + 1.5f, bankEdgeWorldX)
                : Mathf.Min(dockBounds.center.x - 1.5f, bankEdgeWorldX);
            float bankSurfaceY = Mathf.Max(dockBounds.max.y, 1.40f, waterY) + 1.0f;

            isInBoat = false;
            verticalVel = 0f;
            TeleportPlayer(new Vector3(landX, bankSurfaceY, dockBounds.center.z));
            OnBoatStateChanged?.Invoke(false);
            RefreshNearbyHub();
            gm?.NotifyInfo($"Naik ke darat lewat {dockRoot.name}.");
            return true;
        }

        private Vector3 ResolvePermittedMoveOnFoot(Vector3 curPos, Vector3 rawStep, RiverGameManager gm)
        {
            if (rawStep.sqrMagnitude < 0.000001f) return rawStep;

            bool currentlyAllowed = IsFootPositionPermitted(curPos);
            Vector3 nextPos = new Vector3(curPos.x + rawStep.x, curPos.y, curPos.z + rawStep.z);
            if (IsFootPositionPermitted(nextPos)) return rawStep;

            if (!currentlyAllowed)
            {
                // Already in river on foot (edge recovery): allow moves moving out toward bank or Dermaga
                float curMapX = curPos.x / RiverMath.MapScale + RiverMath.WorldW * 0.5f;
                float curMapY = curPos.z / RiverMath.MapScale + RiverMath.WorldH * 0.5f;
                float nextMapX = nextPos.x / RiverMath.MapScale + RiverMath.WorldW * 0.5f;
                float nextMapY = nextPos.z / RiverMath.MapScale + RiverMath.WorldH * 0.5f;
                if (Mathf.Abs(nextMapX - RiverMath.RiverCenterMapX(nextMapY)) >= Mathf.Abs(curMapX - RiverMath.RiverCenterMapX(curMapY)))
                {
                    return rawStep;
                }
            }

            // Slide smoothly along the riverbank without falling into the river channel
            Vector3 tryX = new Vector3(curPos.x + rawStep.x, curPos.y, curPos.z);
            Vector3 tryZ = new Vector3(curPos.x, curPos.y, curPos.z + rawStep.z);
            Vector3 resolved = Vector3.zero;
            if (IsFootPositionPermitted(tryX)) resolved.x = rawStep.x;
            if (IsFootPositionPermitted(tryZ)) resolved.z = rawStep.z;

            if (resolved.sqrMagnitude < rawStep.sqrMagnitude * 0.25f && Time.unscaledTime >= nextRiverGuardAlertTime)
            {
                nextRiverGuardAlertTime = Time.unscaledTime + 3.0f;
                gm?.NotifyInfo("Naik & turun sungai hanya melalui Dermaga (tekan [E] di Dermaga)!", true);
            }

            return resolved;
        }

        private static Vector3 ResolvePermittedMoveInBoat(Vector3 curPos, Vector3 rawStep, RiverGameManager gm)
        {
            if (rawStep.sqrMagnitude < 0.000001f || (gm != null && gm.IsBankOverflowing)) return rawStep;
            if (!RiverMath.IsInRiver(curPos)) return rawStep;

            Vector3 nextPos = new Vector3(curPos.x + rawStep.x, curPos.y, curPos.z + rawStep.z);
            if (RiverMath.IsInRiver(nextPos)) return rawStep;

            Vector3 resolved = Vector3.zero;
            if (RiverMath.IsInRiver(new Vector3(curPos.x + rawStep.x, curPos.y, curPos.z))) resolved.x = rawStep.x;
            if (RiverMath.IsInRiver(new Vector3(curPos.x, curPos.y, curPos.z + rawStep.z))) resolved.z = rawStep.z;
            return resolved;
        }

        private static bool IsFootPositionPermitted(Vector3 pos)
        {
            if (!RiverMath.IsInRiver(pos)) return true;
            return IsPointOnBridge(pos) || IsPointOnDermaga(pos);
        }

        private static bool IsPointOnBridge(Vector3 pos)
        {
            if (pos.y < 1.8f) return false;
            Collider[] hits = Physics.OverlapCapsule(
                new Vector3(pos.x, pos.y - 3.0f, pos.z),
                new Vector3(pos.x, pos.y + 1.5f, pos.z),
                0.6f);
            for (int i = 0; i < hits.Length; i++)
            {
                if (hits[i] != null && (HasHierarchyName(hits[i].transform, "Jembatan") || HasHierarchyName(hits[i].transform, "Bridge")))
                {
                    return true;
                }
            }
            return false;
        }

        private static bool IsPointOnDermaga(Vector3 pos)
        {
            Collider[] hits = Physics.OverlapCapsule(
                new Vector3(pos.x, -2.0f, pos.z),
                new Vector3(pos.x, 5.0f, pos.z),
                0.45f);
            for (int i = 0; i < hits.Length; i++)
            {
                if (hits[i] != null && HasHierarchyName(hits[i].transform, "Dermaga"))
                {
                    return true;
                }
            }
            return false;
        }

        private static bool TryFindNearestDermaga(Vector3 pos, float range, out Collider bestCol, out Transform bestRoot)
        {
            bestCol = null;
            bestRoot = null;

            Collider[] hits = Physics.OverlapCapsule(
                new Vector3(pos.x, -2.5f, pos.z),
                new Vector3(pos.x, 6.0f, pos.z),
                range);

            float bestDistSq = float.MaxValue;
            for (int i = 0; i < hits.Length; i++)
            {
                Collider col = hits[i];
                if (col == null) continue;
                Transform match = FindHierarchyMatch(col.transform, "Dermaga");
                if (match == null) continue;

                Vector3 cp = SafeClosestPoint(col, new Vector3(pos.x, col.bounds.center.y, pos.z));
                float dx = cp.x - pos.x;
                float dz = cp.z - pos.z;
                float dSq = dx * dx + dz * dz;
                if (dSq < bestDistSq)
                {
                    bestDistSq = dSq;
                    bestCol = col;
                    bestRoot = match;
                }
            }

            return bestCol != null;
        }

        private static Vector3 SafeClosestPoint(Collider col, Vector3 point)
        {
            if (col is BoxCollider || col is SphereCollider || col is CapsuleCollider || (col is MeshCollider mc && mc.convex))
            {
                return col.ClosestPoint(point);
            }
            return col.bounds.ClosestPoint(point);
        }

        private void TeleportPlayer(Vector3 worldPos)
        {
            if (controller != null) controller.enabled = false;
            transform.position = worldPos;
            if (controller != null) controller.enabled = true;
        }

        private void TryScoopOrDredge()
        {
            RiverGameManager gm = RiverGameManager.Instance;
            if (gm == null || Time.time < nextScoopTime) return;
            if (gm.cargoCount >= gm.cargoCapacity)
            {
                gm.NotifyInfo("Kargo penuh! Setor ke stasiun atau tahan [Q] di daratan tinggi.", true);
                return;
            }

            ToolDefinition tool = gm.EquippedTool;
            nextScoopTime = Time.time + tool.Cooldown;
            toolSwingTimer = 1f;

            float reach = tool.Reach + (gm.excavatorUnlocked && isInBoat ? 3.5f : 0f);
            Vector3 eyeOrigin = cam != null ? cam.transform.position : (transform.position + Vector3.up * 0.7f);
            Vector3 eyeForward = cam != null ? cam.transform.forward : transform.forward;

            // 1. Collect camera-aimed floating trash, barrier pile, and Gunung Sampah candidates
            Vector3 scanCenter = eyeOrigin + eyeForward * (reach * 0.55f);
            Collider[] hits = Physics.OverlapSphere(scanCenter, reach * 0.65f, ~0, QueryTriggerInteraction.Collide);

            List<(Collider col, RiverTrashItem item, float score, float dist)> trashCandidates = new List<(Collider, RiverTrashItem, float, float)>();
            Collider bestGunungCol = null;
            float bestGunungScore = float.MaxValue;
            float bestGunungDist = float.MaxValue;
            Collider bestPileCol = null;
            float bestPileScore = float.MaxValue;

            foreach (Collider col in hits)
            {
                if (col == null || col.gameObject == gameObject) continue;

                Vector3 toTarget = SafeClosestPoint(col, eyeOrigin) - eyeOrigin;
                float dist = toTarget.magnitude;
                if (dist > reach + 0.5f) continue;

                float dot = dist > 0.05f ? Vector3.Dot(eyeForward, toTarget / dist) : 1f;
                if (dot < 0.25f && dist > 2.2f) continue; // Ignore targets behind the camera

                // Lower score = higher priority (centered in crosshair + closer)
                float score = dist * (1.35f - dot);

                RiverTrashItem trashItem = col.GetComponentInParent<RiverTrashItem>();
                if (trashItem == null)
                {
                    RiverFlowBuoyancy buoyancy = col.GetComponentInParent<RiverFlowBuoyancy>();
                    if (buoyancy != null)
                    {
                        trashItem = buoyancy.gameObject.AddComponent<RiverTrashItem>();
                    }
                }

                if (trashItem != null && !trashItem.isCollected)
                {
                    trashCandidates.Add((col, trashItem, score, dist));
                }
                else if (HasHierarchyName(col.transform, "PintuAirPile"))
                {
                    if (score < bestPileScore) { bestPileScore = score; bestPileCol = col; }
                }
                else if (HasHierarchyName(col.transform, "Gunung Sampah") || col.GetComponentInParent<GunungNodeController>() != null)
                {
                    if (score < bestGunungScore) { bestGunungScore = score; bestGunungDist = dist; bestGunungCol = col; }
                }
            }

            // Direct crosshair ray check: only prioritize Gunung Sampah ahead of floating trash if directly aimed closer than any floating trash
            if (Physics.Raycast(eyeOrigin, eyeForward, out RaycastHit directHit, reach, ~0, QueryTriggerInteraction.Ignore))
            {
                Collider dCol = directHit.collider;
                if (dCol != null && (HasHierarchyName(dCol.transform, "Gunung Sampah") || dCol.GetComponentInParent<GunungNodeController>() != null))
                {
                    float closestTrashDist = float.MaxValue;
                    for (int i = 0; i < trashCandidates.Count; i++)
                    {
                        if (trashCandidates[i].dist < closestTrashDist) closestTrashDist = trashCandidates[i].dist;
                    }
                    if (directHit.distance <= closestTrashDist + 0.25f)
                    {
                        TryDamageGunungCollider(dCol, gm, tool);
                        return;
                    }
                }
            }

            // 2. Scoop aimed floating trash props FIRST (never hijacked by PintuAirPile trigger box)
            if (trashCandidates.Count > 0)
            {
                trashCandidates.Sort((a, b) => a.score.CompareTo(b.score));
                int batchLimit = Mathf.Max(1, tool.BatchCount);
                int scooped = 0;
                Vector3 lastScoopPos = transform.position;

                for (int i = 0; i < trashCandidates.Count && scooped < batchLimit; i++)
                {
                    RiverTrashItem item = trashCandidates[i].item;
                    if (gm.TryPickupWaste(item.wasteClass, item.trashUnits))
                    {
                        lastScoopPos = item.transform.position;
                        item.ConsumeOnScoop();
                        scooped++;
                    }
                    else
                    {
                        break; // Cargo full
                    }
                }
                if (scooped > 0)
                {
                    gm.NotifyWaterSplash(new Vector3(lastScoopPos.x, gm.currentWaterLevelY, lastScoopPos.z));
                    return;
                }
                // Nothing scooped (e.g. cargo full): fall through to pile / Gunung branches
            }

            // 3. Fallback: scoop piled barrier trash at downstream Pintu Air
            if (bestPileCol != null && gm.piledRiverTrashCount > 0)
            {
                int pileScooped = gm.TryScoopPiledBarrierTrash(tool.BatchCount);
                if (pileScooped > 0)
                {
                    gm.NotifyWaterSplash(new Vector3(bestPileCol.transform.position.x, gm.currentWaterLevelY, bestPileCol.transform.position.z));
                }
                return;
            }

            // 4. Dredge Gunung Sampah if aimed at a mountain node
            if (bestGunungCol != null && bestGunungDist <= reach + 0.5f)
            {
                TryDamageGunungCollider(bestGunungCol, gm, tool);
            }
        }

        private static bool TryDamageGunungCollider(Collider col, RiverGameManager gm, ToolDefinition tool)
        {
            bool canDredge = gm.excavatorUnlocked || tool.GunungDamagePerSwing > 0f;
            if (!canDredge)
            {
                gm.NotifyCannotDredgeGunung();
                return false;
            }

            float dmg = gm.excavatorUnlocked ? Mathf.Max(0.20f, tool.GunungDamagePerSwing) : tool.GunungDamagePerSwing;
            GunungNodeController nodeCtrl = col.GetComponentInParent<GunungNodeController>();
            if (nodeCtrl != null)
            {
                nodeCtrl.ApplyDamage(dmg * 1.5f);
            }
            else
            {
                // Bottom-anchored fallback scaling using ratio (avoids stale cached bounds)
                float prevBottomY = col.bounds.min.y;
                float prevHalfY = col.bounds.extents.y;
                Vector3 scale = col.transform.localScale;
                float oldScaleY = Mathf.Max(0.01f, scale.y);
                scale.y = Mathf.Max(0.25f, oldScaleY * 0.85f);
                col.transform.localScale = scale;
                Vector3 pos = col.transform.position;
                pos.y = prevBottomY + prevHalfY * (scale.y / oldScaleY);
                col.transform.position = pos;
                Physics.SyncTransforms();
            }

            gm.DamageGunungSampah(dmg * 0.5f, col.transform.position);
            return true;
        }

        private void OnEquippedToolChanged(ToolDefinition tool)
        {
            if (tool == null || tool.Index == lastEquippedVisualIndex) return;
            lastEquippedVisualIndex = tool.Index;

            if (activeToolVisual != null)
            {
                Destroy(activeToolVisual);
                activeToolVisual = null;
            }

            if (toolSocket == null) return;

            GameObject prefab = null;
            int arrIdx = tool.Index - 1;
            if (toolPrefabs != null && arrIdx >= 0 && arrIdx < toolPrefabs.Length)
            {
                prefab = toolPrefabs[arrIdx];
            }
#if UNITY_EDITOR
            if (prefab == null)
            {
                string prefabPath = $"Assets/_Project/Props/Tools/Prefabs/{tool.PrefabName}.prefab";
                prefab = UnityEditor.AssetDatabase.LoadAssetAtPath<GameObject>(prefabPath);
            }
#endif
            if (prefab != null)
            {
                activeToolVisual = Instantiate(prefab, toolSocket);
                activeToolVisual.transform.localPosition = Vector3.zero;
                activeToolVisual.transform.localRotation = Quaternion.Euler(tool.HeadDir == "-Z" ? -18f : 65f, -8f, 0f);

                // Ensure equipped PF_Tool_* BoxCollider never collides with player CharacterController or raycasts
                foreach (Collider col in activeToolVisual.GetComponentsInChildren<Collider>(true))
                {
                    col.isTrigger = true;
                    col.enabled = false;
                }
            }
        }

        private static bool HasHierarchyName(Transform t, string token) => FindHierarchyMatch(t, token) != null;

        private static Transform FindHierarchyMatch(Transform t, string token)
        {
            while (t != null)
            {
                if (t.name.Contains(token)) return t;
                t = t.parent;
            }
            return null;
        }

        private void RefreshAimTarget()
        {
            RiverGameManager gm = RiverGameManager.Instance;
            if (gm == null) return;

            float reach = gm.EquippedTool.Reach + (gm.excavatorUnlocked && isInBoat ? 3.5f : 0f);
            Vector3 eyeOrigin = cam != null ? cam.transform.position : (transform.position + Vector3.up * 0.7f);
            Vector3 eyeForward = cam != null ? cam.transform.forward : transform.forward;
            float prickPct = gm.GetEffectiveMedicalPrickChance();

            bool hasTarget = false;
            WasteClass targetClass = WasteClass.Normal;
            bool inReach = false;

            if (Physics.Raycast(eyeOrigin, eyeForward, out RaycastHit hit, reach + 4f, ~0, QueryTriggerInteraction.Collide))
            {
                RiverTrashItem item = hit.collider != null ? hit.collider.GetComponentInParent<RiverTrashItem>() : null;
                if (item != null && !item.isCollected)
                {
                    hasTarget = true;
                    targetClass = item.wasteClass;
                    inReach = hit.distance <= reach + 0.5f;
                }
            }

            if (hasTarget != lastAimHasTarget || targetClass != lastAimClass || inReach != lastAimInReach || !Mathf.Approximately(prickPct, lastAimPrick))
            {
                lastAimHasTarget = hasTarget;
                lastAimClass = targetClass;
                lastAimInReach = inReach;
                lastAimPrick = prickPct;
                OnAimTargetChanged?.Invoke(hasTarget, targetClass, inReach, prickPct);
            }
        }

        private enum KeyAction { E, Q, F, R, X, Space, Digit1, Digit2, Digit3, Digit4, BracketLeft, BracketRight }

        private static Vector2 GetMoveAxis()
        {
#if ENABLE_INPUT_SYSTEM
            if (Keyboard.current != null)
            {
                float x = (Keyboard.current.dKey.isPressed || Keyboard.current.rightArrowKey.isPressed ? 1f : 0f)
                        - (Keyboard.current.aKey.isPressed || Keyboard.current.leftArrowKey.isPressed ? 1f : 0f);
                float y = (Keyboard.current.wKey.isPressed || Keyboard.current.upArrowKey.isPressed ? 1f : 0f)
                        - (Keyboard.current.sKey.isPressed || Keyboard.current.downArrowKey.isPressed ? 1f : 0f);
                return new Vector2(x, y);
            }
#endif
#if ENABLE_LEGACY_INPUT_MANAGER
            return new Vector2(Input.GetAxisRaw("Horizontal"), Input.GetAxisRaw("Vertical"));
#else
            return Vector2.zero;
#endif
        }

        private static Vector2 GetLookDelta()
        {
#if ENABLE_INPUT_SYSTEM
            if (Mouse.current != null)
            {
                return Mouse.current.delta.ReadValue() * 0.08f;
            }
#endif
#if ENABLE_LEGACY_INPUT_MANAGER
            return new Vector2(Input.GetAxis("Mouse X"), Input.GetAxis("Mouse Y"));
#else
            return Vector2.zero;
#endif
        }

        private static float GetScrollDelta()
        {
#if ENABLE_INPUT_SYSTEM
            if (Mouse.current != null)
            {
                return Mouse.current.scroll.ReadValue().y;
            }
#endif
#if ENABLE_LEGACY_INPUT_MANAGER
            return Input.GetAxis("Mouse ScrollWheel");
#else
            return 0f;
#endif
        }

        private static bool WasLeftMousePressed()
        {
#if ENABLE_INPUT_SYSTEM
            if (Mouse.current != null && Mouse.current.leftButton.wasPressedThisFrame) return true;
#endif
#if ENABLE_LEGACY_INPUT_MANAGER
            if (Input.GetMouseButtonDown(0)) return true;
#endif
            return false;
        }

        private static bool WasRightMousePressed()
        {
#if ENABLE_INPUT_SYSTEM
            if (Mouse.current != null && Mouse.current.rightButton.wasPressedThisFrame) return true;
#endif
#if ENABLE_LEGACY_INPUT_MANAGER
            if (Input.GetMouseButtonDown(1)) return true;
#endif
            return false;
        }

        private static bool IsRightMouseHeld()
        {
#if ENABLE_INPUT_SYSTEM
            if (Mouse.current != null && Mouse.current.rightButton.isPressed) return true;
#endif
#if ENABLE_LEGACY_INPUT_MANAGER
            if (Input.GetMouseButton(1)) return true;
#endif
            return false;
        }

        private static bool IsShiftHeld()
        {
#if ENABLE_INPUT_SYSTEM
            if (Keyboard.current != null && (Keyboard.current.leftShiftKey.isPressed || Keyboard.current.rightShiftKey.isPressed)) return true;
#endif
#if ENABLE_LEGACY_INPUT_MANAGER
            if (Input.GetKey(KeyCode.LeftShift) || Input.GetKey(KeyCode.RightShift)) return true;
#endif
            return false;
        }

        private static bool IsKeyHeld(KeyAction action)
        {
#if ENABLE_INPUT_SYSTEM
            if (Keyboard.current != null)
            {
                bool held = action switch
                {
                    KeyAction.E => Keyboard.current.eKey.isPressed,
                    KeyAction.Q => Keyboard.current.qKey.isPressed,
                    _ => false
                };
                if (held) return true;
            }
#endif
#if ENABLE_LEGACY_INPUT_MANAGER
            KeyCode kc = action switch
            {
                KeyAction.E => KeyCode.E,
                KeyAction.Q => KeyCode.Q,
                _ => KeyCode.None
            };
            if (kc != KeyCode.None && Input.GetKey(kc)) return true;
#endif
            return false;
        }

        private static bool WasKeyPressed(KeyAction action)
        {
#if ENABLE_INPUT_SYSTEM
            if (Keyboard.current != null)
            {
                bool hit = action switch
                {
                    KeyAction.E => Keyboard.current.eKey.wasPressedThisFrame,
                    KeyAction.Q => Keyboard.current.qKey.wasPressedThisFrame,
                    KeyAction.F => Keyboard.current.fKey.wasPressedThisFrame,
                    KeyAction.R => Keyboard.current.rKey.wasPressedThisFrame,
                    KeyAction.X => Keyboard.current.xKey.wasPressedThisFrame,
                    KeyAction.Space => Keyboard.current.spaceKey.wasPressedThisFrame,
                    KeyAction.Digit1 => Keyboard.current.digit1Key.wasPressedThisFrame,
                    KeyAction.Digit2 => Keyboard.current.digit2Key.wasPressedThisFrame,
                    KeyAction.Digit3 => Keyboard.current.digit3Key.wasPressedThisFrame,
                    KeyAction.Digit4 => Keyboard.current.digit4Key.wasPressedThisFrame,
                    KeyAction.BracketLeft => Keyboard.current.leftBracketKey.wasPressedThisFrame,
                    KeyAction.BracketRight => Keyboard.current.rightBracketKey.wasPressedThisFrame,
                    _ => false
                };
                if (hit) return true;
            }
#endif
#if ENABLE_LEGACY_INPUT_MANAGER
            KeyCode kc = action switch
            {
                KeyAction.E => KeyCode.E,
                KeyAction.Q => KeyCode.Q,
                KeyAction.F => KeyCode.F,
                KeyAction.R => KeyCode.R,
                KeyAction.X => KeyCode.X,
                KeyAction.Space => KeyCode.Space,
                KeyAction.Digit1 => KeyCode.Alpha1,
                KeyAction.Digit2 => KeyCode.Alpha2,
                KeyAction.Digit3 => KeyCode.Alpha3,
                KeyAction.Digit4 => KeyCode.Alpha4,
                KeyAction.BracketLeft => KeyCode.LeftBracket,
                KeyAction.BracketRight => KeyCode.RightBracket,
                _ => KeyCode.None
            };
            if (kc != KeyCode.None && Input.GetKeyDown(kc)) return true;
#endif
            return false;
        }
    }
}
