import "./poolman-pool-overview-card.js";
import "./poolman-problem-card.js";
import "./poolman-recommendations-card.js";
import "./poolman-action-history-card.js";
import "./poolman-quick-actions-card.js";

// Visual editors — registered eagerly so getConfigElement() resolves
// immediately and Lovelace surfaces the "edit" affordance for each card.
import "./editor/poolman-pool-overview-card-editor.js";
import "./editor/poolman-problem-card-editor.js";
import "./editor/poolman-recommendations-card-editor.js";
import "./editor/poolman-action-history-card-editor.js";
import "./editor/poolman-quick-actions-card-editor.js";

const OVERVIEW_TAG = "poolman-pool-overview-card";
const PROBLEM_TAG = "poolman-problem-card";
const RECOMMENDATIONS_TAG = "poolman-recommendations-card";
const ACTION_HISTORY_TAG = "poolman-action-history-card";
const QUICK_ACTIONS_TAG = "poolman-quick-actions-card";
const VERSION = "0.1.0";

window.customCards = window.customCards ?? [];
if (!window.customCards.some((c) => c.type === OVERVIEW_TAG)) {
  window.customCards.push({
    type: OVERVIEW_TAG,
    name: "Pool Overview",
    description:
      "Glanceable summary card for a Pool Manager pool: status badge, key chemistry metrics, water quality score and recommendation count.",
    preview: true,
    documentationURL: "https://noirbizarre.github.io/hass-poolman/pool-overview-card/",
  });
}
if (!window.customCards.some((c) => c.type === PROBLEM_TAG)) {
  window.customCards.push({
    type: PROBLEM_TAG,
    name: "Pool Problems",
    description:
      "Diagnostic card listing the current pool problems by severity, with measured value and expected range.",
    preview: true,
    documentationURL: "https://noirbizarre.github.io/hass-poolman/problem-card/",
  });
}
if (!window.customCards.some((c) => c.type === RECOMMENDATIONS_TAG)) {
  window.customCards.push({
    type: RECOMMENDATIONS_TAG,
    name: "Pool Recommendations",
    description:
      "Actionable pool recommendation list: severity badges, expandable details, and one-tap Apply / Ignore buttons backed by the poolman.apply_recommendation service.",
    preview: true,
    documentationURL:
      "https://noirbizarre.github.io/hass-poolman/recommendations-card/",
  });
}
if (!window.customCards.some((c) => c.type === ACTION_HISTORY_TAG)) {
  window.customCards.push({
    type: ACTION_HISTORY_TAG,
    name: "Pool Action History",
    description:
      "Chronological timeline of recorded pool actions (chemical treatments, cleaning, maintenance) with source badges.",
    preview: true,
    documentationURL: "https://noirbizarre.github.io/hass-poolman/action-history-card/",
  });
}
if (!window.customCards.some((c) => c.type === QUICK_ACTIONS_TAG)) {
  window.customCards.push({
    type: QUICK_ACTIONS_TAG,
    name: "Pool Quick Actions",
    description:
      "One-tap access to common pool operations: trigger analysis, boost filtration and record a treatment.",
    preview: true,
    documentationURL: "https://noirbizarre.github.io/hass-poolman/quick-actions-card/",
  });
}

// eslint-disable-next-line no-console
console.info(
  `%c POOLMAN-CARDS %c v${VERSION} `,
  "color: white; background: #03a9f4; font-weight: 700;",
  "color: #03a9f4; background: transparent; font-weight: 700;",
);
