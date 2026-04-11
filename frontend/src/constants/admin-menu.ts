/**
 * French UI labels for the admin menu section.
 */

export const ADMIN_MENU_LABELS = {
  // Section titles
  manualReplacement: "Remplacement manuel",
  forceDishPlaceholder: "Forcer un plat spécifique…",

  // Table headers
  day: "Jour",
  meal: "Repas",
  manualDish: "Plat manuel",

  // Actions
  useVotes: "Utiliser les votes",
  saveReplacement: "Enregistrer le remplacement",
  validateMenu: "Valider le menu",
  unvalidateMenu: "Dévalider le menu",

  // Status
  finalizedState: "État finalisé",
  yes: "oui",
  no: "non",

  // Vote counts
  votesForSlot: "Votes pour ce créneau",
} as const;

/** Unicode indicator for finalized periods */
export const FINALIZED_INDICATOR = " ✓";
