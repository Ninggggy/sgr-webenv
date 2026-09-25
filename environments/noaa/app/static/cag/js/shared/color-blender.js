// Linear interpolation helper
export const lerp = (a, b, t) => Math.round(a + (b - a) * t);

// Convert a hex color to an RGB array
export const hexToRgb = (hex) => {
    // Remove the '#' if present and normalize shorthand (e.g., '#abc' -> '#aabbcc')
    hex = hex.replace(/^#/, '');
    if (hex.length === 3) {
        hex = hex.split('').map(ch => ch + ch).join('');
    }
    // Convert each pair of hex digits to a number
    return hex.match(/.{2}/g).map(val => parseInt(val, 16));
};

// Convert an RGB to a hex
export const rgbToHex = (r, g, b) => {
  // Support being called as rgbToHex([r,g,b]) or rgbToHex(r,g,b)
  const values = Array.isArray(r) ? r : [r, g, b];

  const toHex = c => c.toString(16).padStart(2, '0');
  return "#" + values.map(toHex).join('');
}

// Blend two hex colors. `t` should be between 0 and 1:
// t = 0 returns colorA; t = 1 returns colorB.
export const hexBlender = (colorA, colorB, t) => {
    const rgbA = hexToRgb(colorA);
    const rgbB = hexToRgb(colorB);
    const blendedRgb = rgbA.map((channel, i) => lerp(channel, rgbB[i], t));
    return rgbToHex(blendedRgb);
};

// Blend two RGB colors given as [r, g, b] arrays.
// Returns a string like "rgb(r, g, b)".
export const rgbBlender = (rgbA, rgbB, t) => {
    const blended = rgbA.map((channel, i) => lerp(channel, rgbB[i], t));
    return `rgb(${blended.join(', ')})`;
};
