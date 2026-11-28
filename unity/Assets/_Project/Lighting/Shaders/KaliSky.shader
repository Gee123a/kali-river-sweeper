// KALI/Sky - procedural URP skybox for KALI: Indonesian River Sweeper.
//
// Assign a material using this shader to RenderSettings.skybox. The material has NO properties:
// everything is read from global shader properties set every frame by KaliDayNightCycle
// (Shader.SetGlobalColor / SetGlobalVector / SetGlobalFloat). Unset globals read as 0 (black sky),
// so something must push them at least once (edit-mode preview included).
//
// Colour space: the project runs in GAMMA colour space, so SetGlobalColor passes values unconverted
// and the reference palette hex values can be used as-is. All colours below are "shader space".
//
// Globals (all optional, defaults = 0):
//   _KaliSkyZenith   Color   Sky colour high up (reached by ~25 deg elevation). Golden hour: #F9CEA4.
//   _KaliSkyHorizon  Color   Sky colour just above the horizon. Golden hour: #FEE5C5. Its luminance also
//                            sets the brightness of the storm cloud deck (dark at night automatically).
//   _KaliSkyHaze     Color   Horizon haze band (~3 deg tall, widens with smog), the fill below the horizon
//                            and the colour distant hills fade into. Golden hour: #E1C9B4.
//   _KaliSunDir      Vector  xyz = world direction TOWARD the sun (normalised in shader). Must always be
//                            the real sun, also at night (it is then below the horizon and hidden); it is
//                            shared with SG_KaliWater's glint, so never repoint it at the moon.
//   _KaliSunColor    Color   HDR sun disc radiance (rgb; ~2-8 so bloom catches it). Its hue squared tints
//                            the halo; the halo also fades out as max(rgb) drops below 1. Black = no sun.
//                            Golden hour: #FFFDDE * ~3. Shared with SG_KaliWater.
//   _KaliSunSize     Float   Angular RADIUS of the sun disc in radians (0.04 ~ 2.3 deg, stylised large).
//                            A tight corona glare scales with it.
//   _KaliSunGlow     Float   Strength of the very wide warm halo around the sun, 0..~1.5. Golden hour ~1
//                            (halo dominates the sky), noon ~0.2, night 0.
//   _KaliMoonDir     Vector  xyz = world direction toward the moon (fixed disc radius ~1.5 deg).
//   _KaliMoonColor   Color   HDR moon disc colour; also drives a faint moon glow. Black = no moon.
//   _KaliStars       Float   0..1 star visibility (hashed twinkling stars, faded near the horizon).
//   _KaliHillColor   Color   Painted hill silhouette colour (nearest layer). Golden hour: #8D7059.
//                            Three layers, 0.5-5 deg tall, taller toward -Z (upstream), notched by the river
//                            valley along the Z axis; farther layers fade toward _KaliSkyHaze.
//   _KaliStorm       Float   0..1 monsoon overcast: value-noise cloud deck rolls in, hides sun/moon/stars,
//                            greys the haze and hills. Brightness follows _KaliSkyHorizon luminance.
//   _KaliSmog        Float   0..1 pollution smog: wider/denser haze, softer dimmer sun, browner and
//                            desaturated sky, hazier hills, fewer stars.
// Engine globals used: _Time (star twinkle, cloud drift).

Shader "KALI/Sky"
{
    SubShader
    {
        Tags { "Queue" = "Background" "RenderType" = "Background" "PreviewType" = "Skybox" "RenderPipeline" = "UniversalPipeline" }
        Cull Off
        ZWrite Off

        Pass
        {
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma target 3.0

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            float4 _KaliSkyZenith;
            float4 _KaliSkyHorizon;
            float4 _KaliSkyHaze;
            float4 _KaliSunDir;
            float4 _KaliSunColor;
            float _KaliSunSize;
            float _KaliSunGlow;
            float4 _KaliMoonDir;
            float4 _KaliMoonColor;
            float _KaliStars;
            float4 _KaliHillColor;
            float _KaliStorm;
            float _KaliSmog;

            struct Attributes
            {
                float4 positionOS : POSITION;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 dirOS : TEXCOORD0;
                UNITY_VERTEX_OUTPUT_STEREO
            };

            float Lum(float3 c) { return dot(c, float3(0.2126, 0.7152, 0.0722)); }
            float3 Norm(float3 v) { return v * rsqrt(max(dot(v, v), 1e-8)); }
            float MaxC(float3 c) { return max(c.r, max(c.g, c.b)); }

            // Sine-free hashes (Dave Hoskins), stable on mobile GPUs.
            float Hash12(float2 p)
            {
                float3 p3 = frac(p.xyx * 0.1031);
                p3 += dot(p3, p3.yzx + 33.33);
                return frac((p3.x + p3.y) * p3.z);
            }

            float3 Hash32(float2 p)
            {
                float3 p3 = frac(p.xyx * float3(0.1031, 0.1030, 0.0973));
                p3 += dot(p3, p3.yxz + 33.33);
                return frac((p3.xxy + p3.yzz) * p3.zyx);
            }

            float VNoise(float2 p)
            {
                float2 i = floor(p);
                float2 f = p - i;
                float2 u = f * f * (3.0 - 2.0 * f);
                return lerp(lerp(Hash12(i), Hash12(i + float2(1.0, 0.0)), u.x),
                            lerp(Hash12(i + float2(0.0, 1.0)), Hash12(i + 1.0), u.x), u.y);
            }

            // One star candidate per cell of a cube-face grid; centres kept inside the cell so no neighbour lookups.
            float3 Stars(float3 d, float pixAng)
            {
                float3 a = abs(d);
                float2 uv;
                float face;
                if (a.y >= a.x && a.y >= a.z) { uv = d.xz / a.y; face = d.y > 0.0 ? 0.0 : 1.0; }
                else if (a.x >= a.z)          { uv = d.zy / a.x; face = d.x > 0.0 ? 2.0 : 3.0; }
                else                          { uv = d.xy / a.z; face = d.z > 0.0 ? 4.0 : 5.0; }

                const float cells = 110.0;
                float2 g = uv * cells + face * 517.0;
                float2 cell = floor(g);
                float3 h = Hash32(cell);

                const float density = 0.035;
                float present = step(h.x, density);
                float bright = pow(saturate(1.0 - h.x / density), 3.0) * 3.0 + 0.3;

                float pxG = pixAng * cells * (1.0 + dot(uv, uv)); // pixel footprint in cell units (d tan = sec^2)
                float r = 0.10 + 0.08 * h.z;
                float rEff = min(max(r, pxG), 0.25);               // never narrower than a pixel (AA), partly energy-compensated
                float dist = length(g - cell - (0.25 + 0.5 * h.yz));
                float s = saturate(1.0 - dist / rEff);
                s *= s * r / rEff;

                float twinkle = 0.7 + 0.3 * sin(_Time.y * (1.3 + 3.0 * h.y) + h.z * 43.0);
                float3 tint = lerp(float3(0.75, 0.85, 1.0), float3(1.0, 0.9, 0.75), h.y);
                return tint * (s * bright * twinkle * present);
            }

            float3 HillLayer(float3 hill, float3 haze, float fade, float h, float y)
            {
                float3 c = lerp(hill, haze, fade);
                float mist = saturate(1.0 - y / max(h, 1e-3)); // lighter toward the base: valley mist
                return lerp(c, haze, mist * 0.35);
            }

            Varyings vert(Attributes v)
            {
                Varyings o;
                UNITY_SETUP_INSTANCE_ID(v);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);
                o.positionCS = TransformObjectToHClip(v.positionOS.xyz);
                o.dirOS = v.positionOS.xyz; // skybox object space = world orientation centred on the camera
                return o;
            }

            half4 frag(Varyings i) : SV_Target
            {
                float3 d = Norm(i.dirOS);
                float y = d.y;
                float pixAng = max(length(fwidth(d)) * 0.7, 1e-5); // angular pixel size; derivatives kept out of branches
                float storm = saturate(_KaliStorm);
                float smog = saturate(_KaliSmog);

                // 1. Zenith -> horizon gradient + wide horizon haze band.
                float yp = saturate(y);
                float q = 1.0 - yp;
                q *= q;
                float3 col = lerp(_KaliSkyHorizon.rgb, _KaliSkyZenith.rgb, 1.0 - q * q);
                float3 haze = _KaliSkyHaze.rgb;
                col = lerp(col, haze, exp(-yp * lerp(16.0, 5.0, smog)) * 0.85);

                // 2. Stars and moon (behind clouds and hills).
                UNITY_BRANCH
                if (_KaliStars > 0.001)
                    col += Stars(d, pixAng) * (_KaliStars * smoothstep(0.02, 0.3, y) * (1.0 - 0.8 * smog));

                float3 dm = d - Norm(_KaliMoonDir.xyz);
                float mAng = length(dm);
                const float moonR = 0.026;
                float mDisc = 1.0 - smoothstep(moonR - pixAng, moonR + pixAng, mAng);
                float2 mUV = float2(dm.x + dm.z, dm.y - dm.z) / moonR;
                float maria = VNoise(mUV * 2.2 + 3.1) * 0.6 + VNoise(mUV * 5.0) * 0.4;
                float limb = sqrt(saturate(1.0 - mAng * mAng / (moonR * moonR)));
                col += _KaliMoonColor.rgb * ((mDisc * lerp(0.7, 1.0, limb) * (1.0 - 0.3 * maria) + 0.06 * exp(-mAng * 9.0) + 0.25 * exp(-mAng * 45.0))
                                             * (1.0 - 0.5 * smog));

                // 3. Monsoon overcast deck.
                float level = sqrt(saturate(Lum(_KaliSkyHorizon.rgb) * 1.25));
                float3 ovTint = lerp(float3(1.0, 1.0, 1.0), _KaliSkyHorizon.rgb / max(MaxC(_KaliSkyHorizon.rgb), 1e-4), 0.2) * level;
                float3 ovLight = float3(0.36, 0.39, 0.44) * ovTint;
                float cov = 0.0;
                UNITY_BRANCH
                if (storm > 0.001)
                {
                    float2 cp = d.xz / (max(y, 0.0) + 0.1) * 0.8 + _Time.y * float2(0.035, 0.012);
                    float n = VNoise(cp) * 0.55 + VNoise(cp * 2.1 + 5.2) * 0.3 + VNoise(cp * 4.3 + 1.7) * 0.15;
                    n = lerp(0.5, n, saturate(y * 5.0)); // no detail aliasing near the horizon
                    cov = saturate((n - 1.0 + storm * 1.25) * 3.0);
                    float3 deck = lerp(float3(0.15, 0.17, 0.21) * ovTint, ovLight, saturate(n * 1.6 - 0.3));
                    deck = lerp(deck, ovLight * 1.1, (1.0 - saturate(y * 4.0)) * 0.6);
                    col = lerp(col, deck, cov);
                }
                float3 hazeS = lerp(haze, ovLight * 1.05, storm * 0.85);

                // 4. Painted hill silhouettes (far -> near) as a function of azimuth. Integer sine frequencies keep the
                //    atan2 seam (exactly -Z) continuous.
                float invXZ = rsqrt(max(dot(d.xz, d.xz), 1e-6));
                float az = atan2(d.x, abs(d.z) < 1e-5 ? 1e-5 : d.z);
                float sx = d.x * invXZ;                                 // sin(azimuth): 0 along the river (Z axis)
                float up = saturate(0.5 - 0.5 * d.z * invXZ);           // 1 toward -Z (upstream), 0 toward +Z
                up = up * up * (3.0 - 2.0 * up);
                float dxSun = sx - _KaliSunDir.x;
                float valley = 1.0 - 0.52 * exp(-dxSun * dxSun * 12.0); // valley notch aligned to setting sun
                float h0 = (0.075 + 0.065 * up + 0.022 * sin(2.0 * az + 1.3) + 0.014 * sin(5.0 * az + 0.4) + 0.008 * sin(11.0 * az + 2.1)) * valley;
                float h1 = (0.052 + 0.048 * up + 0.018 * sin(4.0 * az + 2.2) + 0.011 * sin(9.0 * az + 0.9) + 0.006 * sin(19.0 * az + 1.7)) * valley;
                float h2 = (0.030 + 0.035 * up + 0.014 * sin(6.0 * az + 0.3) + 0.008 * sin(13.0 * az + 2.6) + 0.004 * sin(29.0 * az + 1.1)) * valley;
                float m0 = saturate((h0 - y) / pixAng + 0.5);
                float m1 = saturate((h1 - y) / pixAng + 0.5);
                float m2 = saturate((h2 - y) / pixAng + 0.5);
                float hazeMore = saturate(storm * 0.7 + smog * 0.35);
                float3 hill = lerp(_KaliHillColor.rgb, Lum(_KaliHillColor.rgb).xxx, storm * 0.6);
                col = lerp(col, HillLayer(hill, hazeS, lerp(0.72, 1.0, hazeMore), h0, y), m0);
                col = lerp(col, HillLayer(hill, hazeS, lerp(0.48, 0.95, hazeMore), h1, y), m1);
                col = lerp(col, HillLayer(hill, hazeS, lerp(0.22, 0.9, hazeMore), h2, y), m2);
                float nearness = max(m2, max(m1 * 0.7, m0 * 0.4));
                float sunOcc = max(m2, max(m1 * 0.9, m0 * 0.6));     // far hazy ridges let the sun glow through

                // 5. Below the horizon: haze fill (hill bases dissolve into it).
                float ground = smoothstep(0.0, 0.02, -y);
                col = lerp(col, hazeS, ground);

                // 6. Sun: very wide warm halo (lerp, in-scatters over everything), tight corona and soft HDR disc.
                float sAng = length(d - Norm(_KaliSunDir.xyz));
                float sunMax = MaxC(_KaliSunColor.rgb);
                float3 sunHue = _KaliSunColor.rgb / max(sunMax, 1e-4);
                float spread = 1.0 - 0.4 * smog;
                float halo = 0.68 * exp(-sAng * 1.45 * spread) + 0.32 * exp(-sAng * 4.8 * spread);
                float haloAmt = saturate(_KaliSunGlow * halo) * saturate(sunMax) * (1.0 - 0.85 * storm) * (1.0 - 0.3 * smog) * (1.0 - 0.30 * nearness);
                float3 haloTarget = max(_KaliSkyHorizon.rgb, sunHue * 1.65);
                col = lerp(col, haloTarget, haloAmt);

                float sz = max(_KaliSunSize, 1e-4);
                float soft = sz * (0.14 + 0.6 * smog) + pixAng;
                float disc = 1.0 - smoothstep(sz - soft, sz + soft, sAng);
                float corona = sz * sz / (sAng * sAng + sz * sz);
                corona *= corona;                                    // tight glare, ~0.25 at the disc edge
                float sunVis = (1.0 - cov) * (1.0 - 0.7 * storm);
                col += _KaliSunColor.rgb * (sunVis * (1.0 - ground) * (1.0 - 0.75 * smog) * (disc * (1.0 - sunOcc) + corona * 0.75 * (1.0 - 0.40 * nearness)));

                // 7. Smog grade: desaturate, brown, dim.
                float l = Lum(col);
                col = lerp(col, l.xxx, 0.45 * smog);
                col = lerp(col, l * float3(1.15, 0.92, 0.66), 0.5 * smog);
                col *= 1.0 - 0.12 * smog;

                return half4(col, 1.0);
            }
            ENDHLSL
        }
    }
    Fallback Off
}
