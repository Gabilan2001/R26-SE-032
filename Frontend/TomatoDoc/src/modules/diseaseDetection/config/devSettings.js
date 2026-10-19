// Local-only testing toggles for the Disease module. Deliberately NOT
// persisted (AsyncStorage etc.) -- these reset to their defaults every
// time the app is freshly launched, so there's no risk of a leftover
// testing setting silently carrying into a demo. Reachable only via the
// small settings icon on the scan screen, not a visible tab -- this is a
// dev/testing knob, not a user-facing feature.

// Background removal is OFF by default -- faster scans out of the box.
// Toggle it on from Scan Settings if you specifically want the rembg step.
let skipBgRemoval = true;

export const getSkipBgRemoval = () => skipBgRemoval;
export const setSkipBgRemoval = (value) => { skipBgRemoval = value; };
