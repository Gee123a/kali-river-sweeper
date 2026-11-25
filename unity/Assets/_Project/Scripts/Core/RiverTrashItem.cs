using UnityEngine;

namespace KaliRiverSweeper.Core
{
    /// <summary>
    /// Tracks waste classification (Normal / Medical / Biohazard) and live river registration
    /// so RiverGameManager.TotalTrashInRiver drives linear water rise in real time.
    /// </summary>
    public class RiverTrashItem : MonoBehaviour
    {
        public WasteClass wasteClass = WasteClass.Normal;
        public int trashUnits = 1;
        public bool isPiledAtBarrier;
        public bool isCollected;

        private bool isRegistered;

        private void Awake()
        {
            if (wasteClass == WasteClass.Normal)
            {
                wasteClass = InferWasteClassFromName(gameObject.name);
            }
        }

        private void Start()
        {
            TryRegister();
        }

        private void OnEnable()
        {
            TryRegister();
        }

        private void OnDisable()
        {
            TryUnregister();
        }

        public void TryRegister()
        {
            if (isRegistered || isCollected || RiverGameManager.Instance == null) return;
            isRegistered = true;
            if (isPiledAtBarrier)
            {
                RiverGameManager.Instance.AddPiledTrash(trashUnits);
            }
            else
            {
                RiverGameManager.Instance.RegisterActiveTrash(trashUnits);
            }
        }

        public void TryUnregister()
        {
            if (!isRegistered || RiverGameManager.Instance == null) return;
            isRegistered = false;
            if (isPiledAtBarrier)
            {
                RiverGameManager.Instance.RemovePiledTrash(trashUnits);
            }
            else
            {
                RiverGameManager.Instance.UnregisterActiveTrash(trashUnits);
            }
        }

        public void MarkPiledAtBarrier()
        {
            if (isPiledAtBarrier || isCollected) return;
            if (isRegistered && RiverGameManager.Instance != null)
            {
                RiverGameManager.Instance.ConvertActiveToPiled(trashUnits);
            }
            isPiledAtBarrier = true;
        }

        /// <summary>
        /// Frees the GameObject once piled visual cap is reached while keeping its trashUnits
        /// counted inside RiverGameManager.piledRiverTrashCount.
        /// </summary>
        public void AbsorbIntoNumericPile()
        {
            if (isCollected) return;
            MarkPiledAtBarrier();
            isCollected = true;
            isRegistered = false; // Prevent OnDisable from unregistering the numeric pile count
            Destroy(gameObject);
        }

        public void ConsumeOnScoop()
        {
            if (isCollected) return;
            isCollected = true;
            TryUnregister();
            Destroy(gameObject);
        }

        public static WasteClass InferWasteClassFromName(string objName)
        {
            if (string.IsNullOrEmpty(objName)) return WasteClass.Normal;
            string lower = objName.ToLowerInvariant();
            if (lower.Contains("biohazard") || lower.Contains("radioactive") || lower.Contains("toxic") || lower.Contains("drum"))
            {
                return WasteClass.Biohazard;
            }
            if (lower.Contains("medical") || lower.Contains("syringe") || lower.Contains("medis") || lower.Contains("jarum"))
            {
                return WasteClass.Medical;
            }
            return WasteClass.Normal;
        }
    }
}
