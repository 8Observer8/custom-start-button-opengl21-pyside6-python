#ifdef GL_ES
precision mediump float;
#endif

uniform bool uClick;
uniform vec3 uPickColor;
uniform sampler2D uSampler;

varying vec2 vTexCoord;

void main()
{
    if (!uClick)
    {
        gl_FragColor = texture2D(uSampler, vTexCoord);
    }
    else
    {
        gl_FragColor = vec4(uPickColor, 1.0);
    }
}
