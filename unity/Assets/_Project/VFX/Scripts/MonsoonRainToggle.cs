using UnityEngine;
using KaliRiverSweeper.Core;

namespace KaliRiverSweeper.VFX
{
    /// <summary>
    /// Toggles the monsoon rain particle system when RiverGameManager broadcasts a weather change.
    /// Subscribes only to the public OnWeatherChanged event; no polling.
    /// </summary>
    [RequireComponent(typeof(ParticleSystem))]
    public sealed class MonsoonRainToggle : MonoBehaviour
    {
        [SerializeField] private Vector3 followOffset = new Vector3(0f, 12f, 0f);

        private ParticleSystem rain;
        private ParticleSystem ripples;
        private RiverGameManager subscribedManager;
        private Transform cam;

        private void Awake()
        {
            rain = GetComponent<ParticleSystem>();
            Transform ripplesTransform = transform.Find("VFX_MonsoonRain_Ripples");
            ripples = ripplesTransform != null ? ripplesTransform.GetComponent<ParticleSystem>() : null;

            rain.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
            if (ripples != null)
            {
                ripples.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
            }
        }

        // Start runs after every Awake, so RiverGameManager.Instance is set by now.
        private void Start()
        {
            TrySubscribe();
        }

        private void Update()
        {
            // Subscription retry: covers a manager that is spawned later in the scene.
            if (subscribedManager == null)
            {
                TrySubscribe();
            }
        }

        private void LateUpdate()
        {
            if (cam == null && Camera.main != null)
            {
                cam = Camera.main.transform;
            }

            if (cam != null)
            {
                // Follow the camera horizontally; keep the emitter above the view.
                Vector3 target = cam.position + followOffset;
                transform.position = new Vector3(target.x, followOffset.y, target.z);
            }
        }

        private void OnDisable()
        {
            if (subscribedManager != null)
            {
                subscribedManager.OnWeatherChanged -= HandleWeatherChanged;
                subscribedManager = null;
            }
        }

        private void TrySubscribe()
        {
            if (RiverGameManager.Instance == null)
            {
                return;
            }

            subscribedManager = RiverGameManager.Instance;
            subscribedManager.OnWeatherChanged += HandleWeatherChanged;
        }

        private void HandleWeatherChanged(bool isMonsoonStorm)
        {
            if (isMonsoonStorm)
            {
                rain.Play(true);
                if (ripples != null)
                {
                    ripples.Play(true);
                }
            }
            else
            {
                rain.Stop(true, ParticleSystemStopBehavior.StopEmitting);
                if (ripples != null)
                {
                    ripples.Stop(true, ParticleSystemStopBehavior.StopEmitting);
                }
            }
        }
    }
}
