using KaliRiverSweeper.Core;
using UnityEngine;

namespace KaliRiverSweeper.VFX
{
    /// <summary>
    /// One-shot debris cascade. Subscribes to RiverGameManager.OnGunungTierBreached, which
    /// fires on each Gunung Sampah dam tier break. Play(position) stays public for direct calls.
    /// </summary>
    [RequireComponent(typeof(ParticleSystem))]
    public sealed class TrashAvalancheEffect : MonoBehaviour
    {
        private ParticleSystem avalanche;
        private RiverGameManager subscribedManager;

        private void Awake()
        {
            avalanche = GetComponent<ParticleSystem>();
            avalanche.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
        }

        // Start runs after every Awake, so RiverGameManager.Instance is set by now.
        private void Start()
        {
            TrySubscribe();
        }

        private void Update()
        {
            // Subscription retry: covers a manager spawned after this effect.
            if (subscribedManager == null)
            {
                TrySubscribe();
            }
        }

        private void OnDisable()
        {
            if (subscribedManager != null)
            {
                subscribedManager.OnGunungTierBreached -= HandleTierBreached;
                subscribedManager = null;
            }
        }

        public void Play(Vector3 worldPosition)
        {
            transform.position = worldPosition;
            avalanche.Play(true);
        }

        private void TrySubscribe()
        {
            if (RiverGameManager.Instance == null) return;

            subscribedManager = RiverGameManager.Instance;
            subscribedManager.OnGunungTierBreached += HandleTierBreached;
        }

        private void HandleTierBreached(Vector3 worldPosition)
        {
            Play(worldPosition);
        }
    }
}
