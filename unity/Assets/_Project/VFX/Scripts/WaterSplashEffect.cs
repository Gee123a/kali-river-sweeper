using KaliRiverSweeper.Core;
using UnityEngine;

namespace KaliRiverSweeper.VFX
{
    /// <summary>
    /// One-shot muddy water splash. Subscribes to RiverGameManager.OnWaterSplash, which fires
    /// on scoop and paddle. Play(position) stays public for direct calls.
    /// </summary>
    [RequireComponent(typeof(ParticleSystem))]
    public sealed class WaterSplashEffect : MonoBehaviour
    {
        private ParticleSystem splash;
        private RiverGameManager subscribedManager;

        private void Awake()
        {
            splash = GetComponent<ParticleSystem>();
            splash.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
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
                subscribedManager.OnWaterSplash -= HandleWaterSplash;
                subscribedManager = null;
            }
        }

        public void Play(Vector3 worldPosition)
        {
            transform.position = worldPosition;
            splash.Play(true);
        }

        private void TrySubscribe()
        {
            if (RiverGameManager.Instance == null) return;

            subscribedManager = RiverGameManager.Instance;
            subscribedManager.OnWaterSplash += HandleWaterSplash;
        }

        private void HandleWaterSplash(Vector3 worldPosition)
        {
            Play(worldPosition);
        }
    }
}
