using UnityEngine;
using KaliRiverSweeper.Core;

namespace KaliRiverSweeper.Player
{
    [RequireComponent(typeof(CharacterController))]
    public class KaliPlayerController : MonoBehaviour
    {
        [Header("Movement")]
        public float walkSpeed = 6.5f;
        public float sprintSpeed = 10.5f;
        public float boatSpeed = 9.5f;
        public float freeCamSpeed = 18f;
        public float mouseSensitivity = 2.2f;
        public float scoopRange = 5.5f;

        [Header("State")]
        public bool isInBoat;
        public bool isFreeCam;

        private CharacterController controller;
        private Camera cam;
        private float yaw;
        private float pitch;
        private float verticalVel;

        private void Awake()
        {
            controller = GetComponent<CharacterController>();
            cam = GetComponentInChildren<Camera>();
            yaw = transform.eulerAngles.y;
        }

        private void Update()
        {
#if ENABLE_LEGACY_INPUT_MANAGER || !ENABLE_INPUT_SYSTEM
            HandleLook();
            HandleActions();
            HandleMove();
#endif
        }

        private void HandleLook()
        {
            if (Input.GetMouseButtonDown(1))
            {
                Cursor.lockState = Cursor.lockState == CursorLockMode.Locked ? CursorLockMode.None : CursorLockMode.Locked;
            }
            if (Cursor.lockState == CursorLockMode.Locked || Input.GetMouseButton(1))
            {
                yaw += Input.GetAxis("Mouse X") * mouseSensitivity;
                pitch = Mathf.Clamp(pitch - Input.GetAxis("Mouse Y") * mouseSensitivity, -80f, 80f);
                transform.rotation = Quaternion.Euler(0f, yaw, 0f);
                if (cam != null) cam.transform.localRotation = Quaternion.Euler(pitch, 0f, 0f);
            }
        }

        private void HandleMove()
        {
            float h = Input.GetAxisRaw("Horizontal");
            float v = Input.GetAxisRaw("Vertical");
            Vector3 dir = (transform.right * h + transform.forward * v).normalized;

            if (isFreeCam)
            {
                float up = (Input.GetKey(KeyCode.E) ? 1f : 0f) - (Input.GetKey(KeyCode.Q) ? 1f : 0f);
                transform.position += (dir * freeCamSpeed + Vector3.up * (up * freeCamSpeed)) * Time.deltaTime;
                return;
            }

            float speed = isInBoat ? boatSpeed : (Input.GetKey(KeyCode.LeftShift) ? sprintSpeed : walkSpeed);
            if (!isInBoat)
            {
                verticalVel = controller.isGrounded ? -1f : verticalVel - 18f * Time.deltaTime;
            }
            else
            {
                verticalVel = (0.8f - transform.position.y) * 4f;
            }

            Vector3 move = dir * speed + Vector3.up * verticalVel;
            controller.Move(move * Time.deltaTime);
        }

        private void HandleActions()
        {
            if (Input.GetKeyDown(KeyCode.F)) isFreeCam = !isFreeCam;

            if (Input.GetKeyDown(KeyCode.R) && RiverGameManager.Instance != null)
            {
                RiverGameManager.Instance.SetWeather(!RiverGameManager.Instance.isMonsoonStorm);
            }

            if (Input.GetKeyDown(KeyCode.E))
            {
                if (!TryInteractWithNearbyHub())
                {
                    isInBoat = !isInBoat;
                }
            }

            if (Input.GetMouseButtonDown(0))
            {
                TryScoopOrDredge();
            }
        }

        private bool TryInteractWithNearbyHub()
        {
            if (RiverGameManager.Instance == null) return false;
            Collider[] hits = Physics.OverlapSphere(transform.position, 6f);
            foreach (Collider col in hits)
            {
                string n = col.gameObject.name;
                if (n.Contains("Bank Sampah")) { RiverGameManager.Instance.SellAtBankSampah(false); return true; }
                if (n.Contains("Pos Sortir")) { RiverGameManager.Instance.SellAtBankSampah(true); return true; }
            }
            return false;
        }

        private void TryScoopOrDredge()
        {
            if (RiverGameManager.Instance == null) return;
            float range = RiverGameManager.Instance.galahUnlocked ? scoopRange * 2f : scoopRange;
            Collider[] hits = Physics.OverlapSphere(transform.position + transform.forward * (range * 0.5f), range);
            foreach (Collider col in hits)
            {
                if (col.GetComponent<RiverFlowBuoyancy>() != null)
                {
                    if (RiverGameManager.Instance.TryAddCargo(1))
                    {
                        Destroy(col.gameObject);
                    }
                    return;
                }
                if (col.gameObject.name.Contains("Gunung Sampah") && RiverGameManager.Instance.excavatorUnlocked)
                {
                    RiverGameManager.Instance.DamageGunungSampah(0.20f);
                    col.transform.localScale = Vector3.Max(Vector3.one * 0.25f, col.transform.localScale * 0.85f);
                    return;
                }
            }
        }
    }
}
