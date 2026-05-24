import "./poolman-pool-overview-card.js";
import "./poolman-problem-card.js";

const OVERVIEW_TAG = "poolman-pool-overview-card";
const PROBLEM_TAG = "poolman-problem-card";
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

// eslint-disable-next-line no-console
console.info(
  `%c POOLMAN-CARDS %c v${VERSION} `,
  "color: white; background: #03a9f4; font-weight: 700;",
  "color: #03a9f4; background: transparent; font-weight: 700;",
);
