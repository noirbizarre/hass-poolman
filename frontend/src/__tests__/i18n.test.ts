import { describe, expect, it } from "vitest";

import { normalizeLang, t } from "../i18n.js";

describe("normalizeLang", () => {
  it("returns 'en' by default", () => {
    expect(normalizeLang(undefined)).toBe("en");
    expect(normalizeLang("")).toBe("en");
  });

  it("recognizes French variants", () => {
    expect(normalizeLang("fr")).toBe("fr");
    expect(normalizeLang("fr-FR")).toBe("fr");
    expect(normalizeLang("FR_CA")).toBe("fr");
  });

  it("falls back to English for unknown languages", () => {
    expect(normalizeLang("de")).toBe("en");
    expect(normalizeLang("es-ES")).toBe("en");
  });
});

describe("t", () => {
  it("translates known keys to English by default", () => {
    expect(t(undefined, "analyze")).toBe("Analyze now");
    expect(t("en", "boost_2h")).toBe("+2 h");
  });

  it("translates known keys to French when requested", () => {
    expect(t("fr", "analyze")).toBe("Analyser");
    expect(t("fr-FR", "record")).toBe("Enregistrer un traitement");
  });

  it("falls back to English when a language is unsupported", () => {
    expect(t("de", "analyze")).toBe("Analyze now");
  });
});
