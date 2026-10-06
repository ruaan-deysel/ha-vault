export const HEALTH_CARD_TAG = "vault-health-card";
export const HEALTH_EDITOR_TAG = "vault-health-card-editor";

export const PROTECTED_CARD_TAG = "vault-protected-card";
export const PROTECTED_EDITOR_TAG = "vault-protected-card-editor";

export const NEXT_RUN_CARD_TAG = "vault-next-run-card";
export const NEXT_RUN_EDITOR_TAG = "vault-next-run-card-editor";

export const LAST_BACKUP_CARD_TAG = "vault-last-backup-card";
export const LAST_BACKUP_EDITOR_TAG = "vault-last-backup-card-editor";

export const PROGRESS_CARD_TAG = "vault-progress-card";
export const PROGRESS_EDITOR_TAG = "vault-progress-card-editor";

export const JOBS_CARD_TAG = "vault-jobs-card";
export const JOBS_EDITOR_TAG = "vault-jobs-card-editor";

export const ACTIVITY_CARD_TAG = "vault-activity-card";
export const ACTIVITY_EDITOR_TAG = "vault-activity-card-editor";

export const STORAGE_CARD_TAG = "vault-storage-card";
export const STORAGE_EDITOR_TAG = "vault-storage-card-editor";

export const ANOMALIES_CARD_TAG = "vault-anomalies-card";
export const ANOMALIES_EDITOR_TAG = "vault-anomalies-card-editor";

export const RULES_CARD_TAG = "vault-rules-card";
export const RULES_EDITOR_TAG = "vault-rules-card-editor";

export const DASHBOARD_CARD_TAG = "vault-dashboard-card";
export const DASHBOARD_EDITOR_TAG = "vault-dashboard-card-editor";

export interface CardConfig {
  type: string;
  server?: string;
  name?: string;
  title?: string;
  embedded?: boolean;
  hide_header?: boolean;
  show_tiles?: string[];
  [key: string]: unknown;
}
