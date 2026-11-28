// Wesley (Shaders): soft additive pool of lamp light on the ground under a street / wall lamp.
// URP Forward is limited to 4 additional lights per object, and the river terrain is one big
// mesh, so real point lights alone would pop on the ground. This decal-like quad paints the
// pool instead; EnvNightLamp fades it with _Glow (MaterialPropertyBlock) as the lamp warms up.
Shader "KALI/Env/LightPool"
{
    Properties
    {
        _Color ("Light Colour", Color) = (1, 0.8, 0.28, 1)
        _Intensity ("Intensity", Range(0, 4)) = 1.1
        _Falloff ("Falloff", Range(0.5, 6)) = 2.2
        _Glow ("Glow (set by EnvNightLamp)", Range(0, 1)) = 1
    }
    SubShader
    {
        Tags { "RenderType" = "Transparent" "Queue" = "Transparent-10" "RenderPipeline" = "UniversalPipeline" "IgnoreProjector" = "True" }
        Pass
        {
            Name "LightPool"
            Tags { "LightMode" = "UniversalForward" }
            Blend One One
            ZWrite Off
            Cull Off
            Offset -2, -2

            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_fog
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            CBUFFER_START(UnityPerMaterial)
                half4 _Color;
                half _Intensity;
                half _Falloff;
                half _Glow;
            CBUFFER_END

            struct Attributes { float4 positionOS : POSITION; float2 uv : TEXCOORD0; };
            struct Varyings { float4 positionCS : SV_POSITION; float2 uv : TEXCOORD0; half fog : TEXCOORD1; };

            Varyings vert(Attributes v)
            {
                Varyings o;
                o.positionCS = TransformObjectToHClip(v.positionOS.xyz);
                o.uv = v.uv;
                o.fog = ComputeFogFactor(o.positionCS.z);
                return o;
            }

            half4 frag(Varyings i) : SV_Target
            {
                half r = saturate(length(i.uv * 2.0 - 1.0));
                half pool = pow(1.0 - r, _Falloff);                 // bright centre, soft edge, 0 at the rim
                half3 col = _Color.rgb * (pool * _Intensity * _Glow);
                col = MixFogColor(col, half3(0, 0, 0), i.fog);    // additive: fade to black in fog
                return half4(col, 1);
            }
            ENDHLSL
        }
    }
    FallBack Off
}
