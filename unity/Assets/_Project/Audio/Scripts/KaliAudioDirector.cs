using KaliRiverSweeper.Core;
using UnityEngine;

namespace KaliRiverSweeper.Audio
{
    /// <summary>
    /// Event-driven audio director for KALI: Indonesian River Sweeper.
    /// Subscribes to RiverGameManager.Instance events (no per-frame gameplay polling) and drives:
    /// - BGM loop (BGM_KalimasTheme)
    /// - Calm river vs monsoon storm ambience crossfade (OnWeatherChanged)
    /// - Siaga 2/1 flood warning siren (OnStateChanged)
    /// - Accelerating Biohazard Geiger ticks while carrying biohazard cargo
    /// - Water splash, Gunung avalanche, tool unlock/equip, station pass/fine, hazard sting, ending & NPC/quest cues.
    /// </summary>
    public sealed class KaliAudioDirector : MonoBehaviour
    {
        public static KaliAudioDirector Instance { get; private set; }

        [Header("Ambience & BGM Clips")]
        public AudioClip bgmKalimasTheme;
        public AudioClip ambRiverCalm;
        public AudioClip ambMonsoonStorm;

        [Header("Gameplay & Alert SFX")]
        public AudioClip sfxWaterSplash;
        public AudioClip sfxGunungAvalanche;
        public AudioClip sfxSirenSiaga;
        public AudioClip sfxBiohazardGeiger;
        public AudioClip sfxMedicalPrickAlert;
        public AudioClip sfxStationPass;
        public AudioClip sfxStationFineBuzzer;
        public AudioClip sfxToolUnlockFanfare;
        public AudioClip sfxEquipClick;
        public AudioClip sfxVictorySdg;
        public AudioClip sfxEndingFail;

        [Header("Village & Quest SFX")]
        public AudioClip sfxNpcTalkBlip;
        public AudioClip sfxQuestComplete;

        [Header("Mix Levels")]
        [Range(0f, 1f)] public float bgmVolume = 0.28f;
        [Range(0f, 1f)] public float ambienceVolume = 0.45f;
        [Range(0f, 1f)] public float sfxVolume = 0.75f;
        [Range(0f, 1f)] public float sirenVolume = 0.42f;

        private AudioSource bgmSource;
        private AudioSource calmSource;
        private AudioSource stormSource;
        private AudioSource sirenSource;
        private AudioSource sfxSource;

        private RiverGameManager manager;
        private float subscribeRetryTimer;
        private float stormBlend;
        private float targetStormBlend;
        private bool sirenActive;
        private float sirenTargetVolume;
        private bool geigerActive;
        private float geigerInterval = 0.8f;
        private float geigerTimer;

        private void Awake()
        {
            if (Instance != null && Instance != this)
            {
                Destroy(gameObject);
                return;
            }
            Instance = this;

            bgmSource = CreateSource("BGM_Source", loop: true, volume: bgmVolume);
            calmSource = CreateSource("AMB_CalmSource", loop: true, volume: ambienceVolume);
            stormSource = CreateSource("AMB_StormSource", loop: true, volume: 0f);
            sirenSource = CreateSource("SFX_SirenSource", loop: true, volume: 0f);
            sfxSource = CreateSource("SFX_OneShotSource", loop: false, volume: 1f);

            StartLoop(bgmSource, bgmKalimasTheme);
            StartLoop(calmSource, ambRiverCalm);
            StartLoop(stormSource, ambMonsoonStorm);
            if (sfxSirenSiaga != null) sirenSource.clip = sfxSirenSiaga;
        }

        private void OnEnable()
        {
            TrySubscribeManager();
        }

        private void Start()
        {
            TrySubscribeManager();
        }

        private void OnDisable()
        {
            if (manager != null)
            {
                manager.OnStateChanged -= HandleStateChanged;
                manager.OnWeatherChanged -= HandleWeatherChanged;
                manager.OnWaterSplash -= HandleWaterSplash;
                manager.OnGunungTierBreached -= HandleGunungTierBreached;
                manager.OnToolUnlocked -= HandleToolUnlocked;
                manager.OnEquippedToolChanged -= HandleEquippedToolChanged;
                manager.OnHazardOrAlert -= HandleHazardOrAlert;
                manager.OnStationAuditReceipt -= HandleStationAuditReceipt;
                manager.OnEndingTriggered -= HandleEndingTriggered;
                manager = null;
            }
        }

        private void Update()
        {
            if (manager == null)
            {
                subscribeRetryTimer -= Time.unscaledDeltaTime;
                if (subscribeRetryTimer <= 0f)
                {
                    subscribeRetryTimer = 0.5f;
                    TrySubscribeManager();
                }
            }

            float dt = Time.unscaledDeltaTime;

            // Smooth calm <-> monsoon storm ambience crossfade
            if (!Mathf.Approximately(stormBlend, targetStormBlend))
            {
                stormBlend = Mathf.MoveTowards(stormBlend, targetStormBlend, dt * 0.7f);
                if (calmSource != null) calmSource.volume = ambienceVolume * (1f - stormBlend * 0.65f);
                if (stormSource != null) stormSource.volume = ambienceVolume * stormBlend;
            }

            // Smooth Siaga 2/1 siren fade
            if (sirenSource != null)
            {
                float target = sirenActive ? sirenTargetVolume : 0f;
                sirenSource.volume = Mathf.MoveTowards(sirenSource.volume, target, dt * 1.5f);
                if (sirenSource.volume > 0.01f && !sirenSource.isPlaying && sirenSource.clip != null)
                {
                    sirenSource.Play();
                }
                else if (sirenSource.volume <= 0.005f && sirenSource.isPlaying)
                {
                    sirenSource.Stop();
                }
            }

            // Accelerating Biohazard Geiger clicks while carrying biohazard cargo
            if (geigerActive && sfxBiohazardGeiger != null && sfxSource != null)
            {
                geigerTimer -= Time.deltaTime;
                if (geigerTimer <= 0f)
                {
                    geigerTimer = geigerInterval;
                    sfxSource.pitch = Random.Range(0.95f, 1.08f);
                    sfxSource.PlayOneShot(sfxBiohazardGeiger, sfxVolume * 0.65f);
                }
            }
        }

        public void PlayNpcTalkBlip()
        {
            PlayOneShot(sfxNpcTalkBlip, 0.7f, Random.Range(0.92f, 1.12f));
        }

        public void PlayQuestComplete()
        {
            PlayOneShot(sfxQuestComplete, 0.95f, 1f);
        }

        private void TrySubscribeManager()
        {
            if (manager != null || RiverGameManager.Instance == null) return;

            manager = RiverGameManager.Instance;
            manager.OnStateChanged += HandleStateChanged;
            manager.OnWeatherChanged += HandleWeatherChanged;
            manager.OnWaterSplash += HandleWaterSplash;
            manager.OnGunungTierBreached += HandleGunungTierBreached;
            manager.OnToolUnlocked += HandleToolUnlocked;
            manager.OnEquippedToolChanged += HandleEquippedToolChanged;
            manager.OnHazardOrAlert += HandleHazardOrAlert;
            manager.OnStationAuditReceipt += HandleStationAuditReceipt;
            manager.OnEndingTriggered += HandleEndingTriggered;

            HandleWeatherChanged(manager.isMonsoonStorm);
            HandleStateChanged();
        }

        private void HandleStateChanged()
        {
            if (manager == null) return;

            bool ended = manager.activeEnding != GameEnding.None;
            sirenActive = !ended && manager.SiagaLevel <= 2;
            sirenTargetVolume = manager.SiagaLevel == 1 ? sirenVolume : sirenVolume * 0.55f;

            geigerActive = !ended && manager.biohazardCargo > 0;
            if (geigerActive)
            {
                float graceRatio = manager.biohazardGraceSeconds > 0f
                    ? Mathf.Clamp01(manager.BiohazardGraceRemaining / manager.biohazardGraceSeconds)
                    : 0f;
                geigerInterval = Mathf.Lerp(0.18f, 0.90f, graceRatio);
            }
        }

        private void HandleWeatherChanged(bool isMonsoonStorm)
        {
            targetStormBlend = isMonsoonStorm ? 1f : 0f;
        }

        private void HandleWaterSplash(Vector3 worldPos)
        {
            PlayOneShot(sfxWaterSplash, 0.85f, Random.Range(0.90f, 1.10f));
        }

        private void HandleGunungTierBreached(Vector3 worldPos)
        {
            PlayOneShot(sfxGunungAvalanche, 1f, Random.Range(0.94f, 1.04f));
        }

        private void HandleToolUnlocked(ToolDefinition tool)
        {
            PlayOneShot(sfxToolUnlockFanfare, 0.9f, 1f);
        }

        private void HandleEquippedToolChanged(ToolDefinition tool)
        {
            PlayOneShot(sfxEquipClick, 0.7f, Random.Range(0.95f, 1.05f));
        }

        private void HandleHazardOrAlert(string msg, bool isDanger)
        {
            if (isDanger)
            {
                PlayOneShot(sfxMedicalPrickAlert, 0.8f, 1f);
            }
        }

        private void HandleStationAuditReceipt(StationAuditReceipt receipt)
        {
            if (receipt.IsPass)
            {
                PlayOneShot(sfxStationPass, 0.9f, 1f);
            }
            else
            {
                PlayOneShot(sfxStationFineBuzzer, 0.95f, 1f);
            }
        }

        private void HandleEndingTriggered(GameEnding ending)
        {
            sirenActive = false;
            geigerActive = false;

            bool goodEnding = ending == GameEnding.TrueSdgVictory || ending == GameEnding.PartialSurvival;
            PlayOneShot(goodEnding ? sfxVictorySdg : sfxEndingFail, 1f, 1f);
        }

        private void PlayOneShot(AudioClip clip, float scale, float pitch)
        {
            if (clip == null || sfxSource == null) return;
            sfxSource.pitch = pitch;
            sfxSource.PlayOneShot(clip, sfxVolume * scale);
        }

        private AudioSource CreateSource(string childName, bool loop, float volume)
        {
            GameObject go = new GameObject(childName);
            go.transform.SetParent(transform, false);
            AudioSource src = go.AddComponent<AudioSource>();
            src.playOnAwake = false;
            src.loop = loop;
            src.spatialBlend = 0f;
            src.volume = volume;
            return src;
        }

        private static void StartLoop(AudioSource src, AudioClip clip)
        {
            if (src == null || clip == null) return;
            src.clip = clip;
            src.Play();
        }
    }
}
