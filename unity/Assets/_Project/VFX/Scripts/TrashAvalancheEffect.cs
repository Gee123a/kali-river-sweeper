using UnityEngine;

namespace KaliRiverSweeper.VFX
{
    /// <summary>
    /// One-shot debris cascade, played when a Gunung Sampah dam tier breaks.
    /// The caller (gameplay code) invokes Play(position). No event subscription here.
    /// </summary>
    [RequireComponent(typeof(ParticleSystem))]
    public sealed class TrashAvalancheEffect : MonoBehaviour
    {
        private ParticleSystem avalanche;

        private void Awake()
        {
            avalanche = GetComponent<ParticleSystem>();
            avalanche.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
        }

        public void Play(Vector3 worldPosition)
        {
            transform.position = worldPosition;
            avalanche.Play(true);
        }
    }
}
