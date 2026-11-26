using UnityEngine;

namespace KaliRiverSweeper.VFX
{
    /// <summary>
    /// One-shot muddy water splash. Gameplay code (scoop, paddle) calls Play(position).
    /// This script does not subscribe to events; the caller owns the trigger.
    /// </summary>
    [RequireComponent(typeof(ParticleSystem))]
    public sealed class WaterSplashEffect : MonoBehaviour
    {
        private ParticleSystem splash;

        private void Awake()
        {
            splash = GetComponent<ParticleSystem>();
            splash.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
        }

        public void Play(Vector3 worldPosition)
        {
            transform.position = worldPosition;
            splash.Play(true);
        }
    }
}
