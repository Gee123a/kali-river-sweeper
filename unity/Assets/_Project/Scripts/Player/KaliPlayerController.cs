using System;
using System.Collections.Generic;
using UnityEngine;
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

        [Header("Tool Socket (Optional)")]
        public Transform toolSocket;
        public GameObject[] toolPrefabs;

        [Header("State")]
        public bool isInBoat;
        public bool isFreeCam;

        public event Action<bool, DiscardStationType, bool, bool, string> OnNearbyHubChanged;
        public bool HasNearbyHub { get; private set; }
        public DiscardStationType NearbyStationType { get; private set; }
        public bool NearbyIsPosSortir { get; private set; }
        public bool NearbyIsTokoAlat { get; private set; }
        public string NearbyHubName { get; private set; } = string.Empty;

        private const float HubPollInterval = 0.1f;

        private CharacterController controller;
        private Camera cam;
        private float yaw;
        private float pitch;
        private float verticalVel;
        private float nextScoopTime;
        private float nextPaddleSplashTime;
        private float nextHubPollTime;
        private int lastEquippedVisualIndex = -1;
        private GameObject activeToolVisual;
        private Quaternion toolSocketBaseRot = Quaternion.identity;
        private float toolSwingTimer;

        private void Awake()
        {
            controller = GetComponent<CharacterController>();
            cam = GetComponentInChildren<Camera>();
            yaw = transform.eulerAngles.y;

#if !ENABLE_INPUT_SYSTEM && !ENABLE_LEGACY_INPUT_MANAGER
            Debug.LogWarning("[KALI] Neither Unity Input System nor Legacy Input Manager is active in Player Settings. Player controls will be disabled.");
#endif
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
            if (RiverGameManager.Instance != null && RiverGameManager.Instance.activeEnding != GameEnding.None)
            {
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
                transform.position += (dir * freeCamSpeed + Vector3.up * (up * freeCamSpeed)) * Time.deltaTime;
                return;
            }

            RiverGameManager gm = RiverGameManager.Instance;
            float waterY = gm != null ? gm.currentWaterLevelY : 0f;
            float speed = isInBoat ? boatSpeed : (IsShiftHeld() ? sprintSpeed : walkSpeed);

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
            }
            else
            {
                float targetBoatY = waterY + boatRideHeight;
                verticalVel = (targetBoatY - transform.position.y) * 5.0f;
            }

            Vector3 move = dir * speed + Vector3.up * verticalVel;
            if (isInBoat)
            {
                float stormMult = gm != null && gm.isMonsoonStorm ? 2.2f : 1f;
                move += Vector3.forward * (0.45f * stormMult); // Gentle +Z downstream current
            }

            controller.Move(move * Time.deltaTime);

            if (isInBoat && gm != null && dir.sqrMagnitude > 0.05f && Time.time >= nextPaddleSplashTime)
            {
                nextPaddleSplashTime = Time.time + 0.45f;
                gm.NotifyWaterSplash(new Vector3(transform.position.x, waterY, transform.position.z));
            }
        }

        private void HandleActions()
        {
            RiverGameManager gm = RiverGameManager.Instance;

            if (WasKeyPressed(KeyAction.F)) isFreeCam = !isFreeCam;

            if (WasKeyPressed(KeyAction.R) && gm != null)
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

            // High-ground cargo dump (anti-deadlock during Sell-Lock) when not in Free-Cam
            if (!isFreeCam && WasKeyPressed(KeyAction.Q) && gm != null)
            {
                gm.DumpCargoOnHighGround();
            }

            // Emergency Flush hotkey (Shift + X) during flood crisis
            if (IsShiftHeld() && WasKeyPressed(KeyAction.X) && gm != null)
            {
                gm.TriggerEmergencyFlush();
            }

            // Station Quick-Discard (1/2/3) & All-Discard / Boat Toggle (E)
            if (gm != null && !gm.IsDemoHotkeyBusy)
            {
                bool nearStation = TryFindNearestHub(out DiscardStationType station, out bool isPosSortir, out bool isTokoAlat);
                if (nearStation && !isTokoAlat)
                {
                    if (WasKeyPressed(KeyAction.Digit1)) gm.DiscardWasteAtStation(station, WasteClass.Normal, isPosSortir);
                    else if (WasKeyPressed(KeyAction.Digit2)) gm.DiscardWasteAtStation(station, WasteClass.Medical, isPosSortir);
                    else if (WasKeyPressed(KeyAction.Digit3)) gm.DiscardWasteAtStation(station, WasteClass.Biohazard, isPosSortir);
                }
            }

            if (WasKeyPressed(KeyAction.E) && !isFreeCam)
            {
                if (!TryInteractWithNearbyHub())
                {
                    TryToggleBoat(gm);
                }
            }

            if (WasLeftMousePressed() && !isFreeCam)
            {
                TryScoopOrDredge();
            }
        }

        /// <summary>
        /// Refreshes nearby hub proximity state and emits OnNearbyHubChanged when the active hub changes.
        /// </summary>
        public void RefreshNearbyHub()
        {
            bool found = TryFindNearestHub(out DiscardStationType station, out bool isPosSortir, out bool isTokoAlat, out string hubName);
            string resolvedName = found ? (hubName ?? string.Empty) : string.Empty;
            if (found == HasNearbyHub &&
                (!found || (station == NearbyStationType && isPosSortir == NearbyIsPosSortir && isTokoAlat == NearbyIsTokoAlat && resolvedName == NearbyHubName)))
            {
                return;
            }

            HasNearbyHub = found;
            NearbyStationType = station;
            NearbyIsPosSortir = isPosSortir;
            NearbyIsTokoAlat = isTokoAlat;
            NearbyHubName = resolvedName;
            OnNearbyHubChanged?.Invoke(found, station, isPosSortir, isTokoAlat, resolvedName);
        }

        private static readonly (string token, DiscardStationType station, bool isSortir, bool isToko)[] HubRules =
        {
            ("Bank Sampah", DiscardStationType.BankSampah, false, false),
            ("Pos Sortir", DiscardStationType.BankSampah, true, false),
            ("Pos Medis", DiscardStationType.PosMedisB3, false, false),
            ("Karantina Biohazard", DiscardStationType.KarantinaBiohazard, false, false),
            ("Gudang Pengepul", DiscardStationType.GudangPengepul, false, false),
            ("Toko Alat", DiscardStationType.BankSampah, false, true)
        };

        private bool TryFindNearestHub(out DiscardStationType stationType, out bool isPosSortir, out bool isTokoAlat)
        {
            return TryFindNearestHub(out stationType, out isPosSortir, out isTokoAlat, out _);
        }

        private bool TryFindNearestHub(out DiscardStationType stationType, out bool isPosSortir, out bool isTokoAlat, out string hubName)
        {
            stationType = DiscardStationType.BankSampah;
            isPosSortir = false;
            isTokoAlat = false;
            hubName = string.Empty;

            Collider[] hits = Physics.OverlapSphere(transform.position, interactRange);
            float bestDistSq = float.MaxValue;
            bool found = false;

            foreach (Collider col in hits)
            {
                if (col == null) continue;

                Transform match = null;
                DiscardStationType candidateType = DiscardStationType.BankSampah;
                bool candidateSortir = false;
                bool candidateToko = false;

                for (int i = 0; i < HubRules.Length; i++)
                {
                    match = FindHierarchyMatch(col.transform, HubRules[i].token);
                    if (match != null)
                    {
                        candidateType = HubRules[i].station;
                        candidateSortir = HubRules[i].isSortir;
                        candidateToko = HubRules[i].isToko;
                        break;
                    }
                }

                if (match == null) continue;

                float dSq = (col.ClosestPoint(transform.position) - transform.position).sqrMagnitude;
                if (dSq < bestDistSq)
                {
                    bestDistSq = dSq;
                    stationType = candidateType;
                    isPosSortir = candidateSortir;
                    isTokoAlat = candidateToko;
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

            if (!TryFindNearestHub(out DiscardStationType station, out bool isPosSortir, out bool isTokoAlat))
            {
                return false;
            }

            if (isTokoAlat)
            {
                // Fallback quick-upgrade progression if Niki's shop modal is not open
                if (!gm.kampungBinsInstalled && gm.BuyKampungBins()) return true;
                if (!gm.sampanUnlocked && gm.BuyUpgrade(UpgradeTier.WoodenSampan))
                {
                    gm.NotifyInfo("Perahu Sampan Kayu dibeli! (Kapasitas 22)");
                    return true;
                }
                if (!gm.trashBoomActive && gm.BuyUpgrade(UpgradeTier.TrashBoomAndPosSortir))
                {
                    gm.NotifyInfo("Trash Boom & Pos Sortir aktif! (+Rp 2.500/4s)");
                    return true;
                }
                if (!gm.excavatorUnlocked && gm.BuyUpgrade(UpgradeTier.AmphibiousExcavator))
                {
                    gm.NotifyInfo("Pindad Amphibious Excavator terbuka! Keruk Gunung Sampah!");
                    return true;
                }
                gm.NotifyInfo("Toko Alat: Kumpulkan lebih banyak Rupiah (Bins 30k / Sampan 40k / Boom 75k / Excavator 120k).", true);
                return true;
            }

            gm.DiscardAllAtStation(station, isPosSortir);
            return true;
        }

        private void TryToggleBoat(RiverGameManager gm)
        {
            float mapX = transform.position.x / RiverMath.MapScale + RiverMath.WorldW * 0.5f;
            float mapY = Mathf.Clamp(transform.position.z / RiverMath.MapScale + RiverMath.WorldH * 0.5f, 110f, RiverMath.WorldH);
            float cx = RiverMath.RiverCenterMapX(mapY);
            float hw = RiverMath.RiverHalfWidthMap(mapY);
            float waterY = gm != null ? gm.currentWaterLevelY : 0f;
            bool flooded = gm != null && gm.IsBankOverflowing;

            if (!isInBoat)
            {
                // Allow boarding when near river channel / dock (within ~8m of bank edge) or when banks are flooded
                if (!flooded && Mathf.Abs(mapX - cx) > hw + 64f)
                {
                    gm?.NotifyInfo("Dekati tepi sungai atau dermaga untuk naik perahu.", true);
                    return;
                }
                isInBoat = true;
                verticalVel = 0f;
                if (!RiverMath.IsInRiver(transform.position))
                {
                    float insideMapX = cx + Mathf.Sign(mapX - cx) * Mathf.Max(0f, hw - 18f);
                    Vector3 waterPos = RiverMath.ToWorld3D(insideMapX, mapY, waterY + boatRideHeight);
                    TeleportPlayer(waterPos);
                }
                return;
            }

            // Disembarking: lift cleanly onto nearest bank above BankTopY (+1.40m) so player is never trapped in -2.0m trench
            isInBoat = false;
            verticalVel = 0f;
            if (RiverMath.IsInRiver(transform.position))
            {
                float bankMapX = cx + (mapX >= cx ? 1f : -1f) * (hw + 22f);
                float bankSurfaceY = Mathf.Max(1.40f, waterY) + 1.1f;
                Vector3 bankPos = RiverMath.ToWorld3D(bankMapX, mapY, bankSurfaceY);
                TeleportPlayer(bankPos);
            }
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

                Vector3 toTarget = col.ClosestPoint(eyeOrigin) - eyeOrigin;
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
                }
                return;
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

        private enum KeyAction { E, Q, F, R, X, Space, Digit1, Digit2, Digit3, BracketLeft, BracketRight }

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
