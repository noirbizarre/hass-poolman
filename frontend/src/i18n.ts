// Minimal in-bundle i18n for Poolman Lovelace cards.
//
// We do not pull strings from the integration's translations file at runtime
// to keep the card self-contained and reactive without an extra websocket
// round-trip. The set of keys is small and stable, so duplicating them here
// is acceptable.

export type Lang = "en" | "fr";

export type TranslationKey =
  | "card_name"
  | "card_description"
  | "analyze"
  | "analyze_aria"
  | "boost_2h"
  | "boost_4h"
  | "boost_aria"
  | "record"
  | "record_aria"
  | "pending"
  | "success"
  | "error_generic"
  | "service_unavailable"
  | "dialog_title"
  | "dialog_type"
  | "dialog_type_chemical"
  | "dialog_type_cleaning"
  | "dialog_type_maintenance"
  | "dialog_product_id"
  | "dialog_quantity"
  | "dialog_unit"
  | "dialog_unit_none"
  | "dialog_note"
  | "dialog_submit"
  | "dialog_cancel"
  | "dialog_validation_quantity"
  // Card editor (visual Lovelace editor)
  | "editor_device"
  | "editor_entity"
  | "editor_name"
  | "editor_metrics"
  | "editor_metric_temperature"
  | "editor_metric_ph"
  | "editor_metric_free_chlorine"
  | "editor_metric_orp"
  | "editor_show_score"
  | "editor_recommendations_path"
  | "editor_max"
  | "editor_show_severity"
  | "editor_confirm_apply"
  | "editor_confirm_apply_never"
  | "editor_confirm_apply_always"
  | "editor_confirm_apply_critical_high"
  | "editor_limit"
  | "editor_show_source"
  | "editor_group_by_day"
  | "editor_analyze"
  | "editor_boost"
  | "editor_record"
  | "editor_device_required"
  | "editor_device_or_entity_required";

type StringTable = Record<TranslationKey, string>;

const EN: StringTable = {
  card_name: "Quick Actions",
  card_description:
    "One-tap buttons to trigger a pool analysis, boost filtration or record a treatment.",
  analyze: "Analyze now",
  analyze_aria: "Trigger an immediate pool analysis",
  boost_2h: "+2 h",
  boost_4h: "+4 h",
  boost_aria: "Boost filtration",
  record: "Record treatment",
  record_aria: "Record a manual pool action",
  pending: "Working…",
  success: "Done",
  error_generic: "Service call failed",
  service_unavailable: "Service calls unavailable",
  dialog_title: "Record treatment",
  dialog_type: "Type",
  dialog_type_chemical: "Chemical",
  dialog_type_cleaning: "Cleaning",
  dialog_type_maintenance: "Maintenance",
  dialog_product_id: "Product ID",
  dialog_quantity: "Quantity",
  dialog_unit: "Unit",
  dialog_unit_none: "—",
  dialog_note: "Note",
  dialog_submit: "Record",
  dialog_cancel: "Cancel",
  dialog_validation_quantity: "Quantity must be a positive number",
  editor_device: "Pool device",
  editor_entity: "Entity",
  editor_name: "Name",
  editor_metrics: "Metrics",
  editor_metric_temperature: "Temperature",
  editor_metric_ph: "pH",
  editor_metric_free_chlorine: "Free chlorine",
  editor_metric_orp: "ORP",
  editor_show_score: "Show water quality score",
  editor_recommendations_path: "Recommendations navigation path",
  editor_max: "Maximum rows",
  editor_show_severity: "Show severity label",
  editor_confirm_apply: "Confirm before applying",
  editor_confirm_apply_never: "Never",
  editor_confirm_apply_always: "Always",
  editor_confirm_apply_critical_high: "Critical and high priority",
  editor_limit: "Maximum actions",
  editor_show_source: "Show source badge",
  editor_group_by_day: "Group by day",
  editor_analyze: "Show Analyze button",
  editor_boost: "Show filtration boost buttons",
  editor_record: "Show Record treatment button",
  editor_device_required: "Pool device is required",
  editor_device_or_entity_required: "A pool device or an entity is required",
};

const FR: StringTable = {
  card_name: "Actions rapides",
  card_description:
    "Boutons en un tap pour déclencher une analyse, booster la filtration ou enregistrer un traitement.",
  analyze: "Analyser",
  analyze_aria: "Déclencher une analyse immédiate",
  boost_2h: "+2 h",
  boost_4h: "+4 h",
  boost_aria: "Booster la filtration",
  record: "Enregistrer un traitement",
  record_aria: "Enregistrer une action manuelle",
  pending: "En cours…",
  success: "Fait",
  error_generic: "Échec de l'appel du service",
  service_unavailable: "Appels de service indisponibles",
  dialog_title: "Enregistrer un traitement",
  dialog_type: "Type",
  dialog_type_chemical: "Produit chimique",
  dialog_type_cleaning: "Nettoyage",
  dialog_type_maintenance: "Maintenance",
  dialog_product_id: "Identifiant produit",
  dialog_quantity: "Quantité",
  dialog_unit: "Unité",
  dialog_unit_none: "—",
  dialog_note: "Note",
  dialog_submit: "Enregistrer",
  dialog_cancel: "Annuler",
  dialog_validation_quantity: "La quantité doit être un nombre positif",
  editor_device: "Bassin",
  editor_entity: "Entité",
  editor_name: "Nom",
  editor_metrics: "Mesures",
  editor_metric_temperature: "Température",
  editor_metric_ph: "pH",
  editor_metric_free_chlorine: "Chlore libre",
  editor_metric_orp: "ORP",
  editor_show_score: "Afficher le score de qualité",
  editor_recommendations_path: "Chemin de navigation des recommandations",
  editor_max: "Nombre maximum de lignes",
  editor_show_severity: "Afficher le libellé de sévérité",
  editor_confirm_apply: "Confirmer avant application",
  editor_confirm_apply_never: "Jamais",
  editor_confirm_apply_always: "Toujours",
  editor_confirm_apply_critical_high: "Priorité critique et haute",
  editor_limit: "Nombre maximum d'actions",
  editor_show_source: "Afficher la source",
  editor_group_by_day: "Grouper par jour",
  editor_analyze: "Afficher le bouton Analyser",
  editor_boost: "Afficher les boutons Booster",
  editor_record: "Afficher le bouton Enregistrer",
  editor_device_required: "Le bassin est requis",
  editor_device_or_entity_required: "Un bassin ou une entité est requis",
};

const STRINGS: Record<Lang, StringTable> = { en: EN, fr: FR };

/** Normalize an HA locale code (e.g. `fr-FR`, `EN_US`) to a supported Lang. */
export function normalizeLang(lang: string | undefined): Lang {
  if (!lang) return "en";
  const head = lang.toLowerCase().replace("_", "-").split("-")[0];
  return head === "fr" ? "fr" : "en";
}

/** Translate a key. Unknown keys fall back to their identifier. */
export function t(lang: string | undefined, key: TranslationKey): string {
  const norm = normalizeLang(lang);
  return STRINGS[norm][key] ?? STRINGS.en[key] ?? key;
}
