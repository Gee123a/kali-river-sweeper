---
version: 1
slug: "canvas-hud"
primary_target: "canvas-hud"
related_targets: []
---

THESIS: KALI: Indonesian River Sweeper desktop HUD built as backlit translucent vellum exposure sheets ("Lembar Kalkir Zona Cahaya") over a sunlit golden-morning tropical river, replacing generic dark-navy SaaS cards with crisp 11-step tonal paper neutrals, diagonal load hatching, and a single glowing dichroic magenta (#E11D8F) reserved strictly for live hazard filtration and conflict states.

OWN-WORLD: Indonesian hydrographic field notes merged with a darkroom printer's backlit exposure record. Translucent vellum sheets (#F4F2EC) sit lightly along the top edges with masking-tape pins, keeping the center 68% river playfield and the entire bottom-left and bottom-center edge completely open for first-person sampan visibility and future tool/inventory slots. In the bottom-right corner, a slightly tilted (-2.5deg) backlit tracing-paper topographic contour river chart anchors navigation with exactly four stamped stations (B, M, K, P) and a magenta cross-hatch debris choke marker.

STORY: During calm Golden Morning gameplay (Act 1-2), the player reads survival (top-left HP 72, SIAGA 3 +0.84m), ecological mission progress (top-center GUNUNG SAMPAH 64%, KEJERNIHAN 61%, MONSUN 04:37), and economy/cargo (top-right Rp 1.250.000, MUATAN 14/22 across Normal/Medis/Biohazard, Warga 68) at a glance with zero screen clutter. When docking at a pier or facing Act 3 Monsoon overflow (>= +1.85m Sell-Lock) and Biohazard 10s exposure, contextual vellum strips slide cleanly into reserved rails using 90-degree magenta cross-hatching to signal illegal deposits (DENDA) or active crisis without ever covering the crosshair.

FIRST VIEWPORT: Full-bleed 1920x1080 (safe down to 1280x720) first-person desktop game HUD. Top-left: layered backlit vellum sheet for HP (11-step segmented zone ramp) and SIAGA flood elevation scale. Top-center: slim vellum ecological rail combining hatched GUNUNG SAMPAH %, solid teal KEJERNIHAN %, and tabular MONSUN countdown. Top-right: backlit vellum ledger with bold Rupiah headline, 3-class cargo capacity (14/22), and Warga trust. Center: unobtrusive 1px precision reticle. Bottom-left & bottom-center: completely clear during open navigation (contextual station sheet slides in only on dock trigger). Bottom-right: tilted translucent tracing-paper hydrographic contour map (+Z flow, B/M/K/P stamps, magenta choke hatch).

FORM: seed:05ebcbb5e3a3848a | catalogId: operate-b-exposure-record-zone-sheets | approvedComp: .impeccable/mocks/decision/r2-exposure.png | tokens: Zone X #F4F2EC, Zone VIII #DCDAD2, Zone IV #7A7974, Zone I #1E1F1D, Zone 0 #111211, Dichroic Magenta #E11D8F, River Teal #1B8A7A, Siaga Amber #D97706 | type: Condensed Tracked Display Caps (Barlow Condensed) + Tabular Mono (JetBrains Mono) | signature: 45-degree hatch for load, 90-degree magenta cross-hatch for conflict (DENDA / Sell-Lock / Biohazard), cleared light paper zones under all text.

FINISH: Pixel-verified at both 1920x1080 and 1280x720 across Normal Morning and Monsoon Crisis/Dock states; zero overlapping labels, WCAG AA contrast on cleared light zones (>= 7:1 ink on Zone X paper), 100% alignment with RiverGameManager.cs and ToolCatalog.cs values, zero em dashes, and ready-to-build Unity uGUI + TextMeshPro spec in docs/HUD_SPEC_NIKI.md.
