# TomatoDoc theme

One visual language for every module (Nutrient, Fruit, Disease, Monitoring, Price), taken from the
project's portfolio site: a warm cream page, deep forest-green hero areas, a lime accent and
soft, rounded white cards.

| File | What it holds |
|---|---|
| `index.js` | Colour tokens (`palette`), gradients, radii, shadows and text styles. Import with `import { palette as P, radius, shadow } from '../theme'`. |
| `navigation.js` | The floating tab bar (`tabOptions`) and stack header options used by `AppNavigator`. |
| `../components/ScreenHeader.js` | The green page header (back button, title, optional right element) used by every module screen. |

Rules when adding or changing a screen:

* Use the tokens, not new hex values. Page background `P.bg`, cards `P.surface` with `P.border`,
  primary actions `P.forestMid` with white text, highlights on green `P.lime`.
* Status colours: `P.good`, `P.warn`, `P.danger` (each has a `...Dim` background and `...Border`).
* Cards use `radius.lg` and `shadow.card`; hero blocks use `radius.xl`.
* Leave room above the floating tab bar on tab screens (about 110 to 130 px of bottom padding).
* This folder only changes how things look. Navigation, API calls and state live elsewhere.
