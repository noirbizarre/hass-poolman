import "./poolman-pool-overview-card.js";

const CARD_TAG = "poolman-pool-overview-card";
const VERSION = "0.1.0";

window.customCards = window.customCards ?? [];
if (!window.customCards.some((c) => c.type === CARD_TAG)) {
  window.customCards.push({
    type: CARD_TAG,
    name: "Pool Overview",
    description:
      "Glanceable summary card for a Pool Manager pool: status badge, key chemistry metrics, water quality score and recommendation count.",
    preview: true,
    documentationURL: "https://noirbizarre.github.io/hass-poolman/pool-overview-card/",
  });
}

// eslint-disable-next-line no-console
console.info(
  `%c POOLMAN-POOL-OVERVIEW-CARD %c v${VERSION} `,
  "color: white; background: #03a9f4; font-weight: 700;",
  "color: #03a9f4; background: transparent; font-weight: 700;",
);
