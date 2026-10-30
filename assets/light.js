/* Procedural light sprite for the noncommercial trial edition. No image asset. */
function glowSprite(rgb, power) {
    const channels = rgb.split(',').map(Number);
    const surface = document.createElement('canvas');
    surface.width = surface.height = 96;
    const painter = surface.getContext('2d');
    const pixels = painter.createImageData(96, 96);
    for (let row = 0; row < 96; row++) {
        for (let col = 0; col < 96; col++) {
            const dx = (col - 47.5) / 48, dy = (row - 47.5) / 48;
            const distance = dx * dx + dy * dy;
            const centre = Math.exp(-distance * 150);
            const spread = Math.exp(-distance * 21) * .58 + Math.exp(-distance * 6) * .10;
            const offset = (row * 96 + col) * 4;
            for (let channel = 0; channel < 3; channel++) {
                pixels.data[offset + channel] = channels[channel] + (255 - channels[channel]) * centre;
            }
            pixels.data[offset + 3] = Math.min(1, (centre + spread) * power) * 255;
        }
    }
    painter.putImageData(pixels, 0, 0);
    return surface;
}
