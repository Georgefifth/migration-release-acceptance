'use strict';
// Same visuals, timings and narration copy. No substitute or fabricated audio.
// The installed edge-tts service returned HTTP 403 in the capability probe.
module.exports=require('./scenes.cjs').map(({vo,...scene})=>({...scene,caption:scene.caption||vo}));
