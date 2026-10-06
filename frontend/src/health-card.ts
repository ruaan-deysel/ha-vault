import { html, type TemplateResult } from "lit";
import { BaseVaultCard } from "./dashboard-cards-base";
import { VaultCardEditor } from "./dashboard-cards-editor";
import { HEALTH_CARD_TAG, HEALTH_EDITOR_TAG } from "./config";
import {
  iconTemplate,
  mdiHeart,
} from "./icons";
import { registerDashboardCard } from "./register-dashboard-card";

export class VaultHealthCard extends BaseVaultCard {
  static override editorTag = HEALTH_EDITOR_TAG;

  protected override render(): TemplateResult {
    const statusEnt = this.getEntity("vault_status") || this.getEntity("status");
    const rawStatus = statusEnt?.state?.toLowerCase();
    const isUnknownOrUnavailable = !statusEnt || rawStatus === "unavailable" || rawStatus === "unknown";
    const isHealthy = !isUnknownOrUnavailable && (rawStatus === "ok" || rawStatus === "healthy" || rawStatus === "running");

    const anomaliesEnt = this.getEntity("open_anomalies");
    const openAnomalies = Number(anomaliesEnt?.state ?? 0);

    // Calculate health score: 100 if healthy & 0 anomalies, 70 if warnings/anomalies, 25 if unhealthy, null if unavailable
    let score: number | null = 100;
    if (isUnknownOrUnavailable) {
      score = null;
    } else if (!isHealthy) {
      score = 25;
    } else if (openAnomalies > 0) {
      score = Math.max(40, 100 - openAnomalies * 20);
    }

    const circumference = 2 * Math.PI * 22; // r=22
    const strokeDashoffset = score !== null ? circumference - (score / 100) * circumference : circumference;
    const strokeColor = score === null
      ? "var(--vault-standby)"
      : score >= 90
      ? "var(--vault-success)"
      : score >= 60
      ? "var(--vault-warning)"
      : "var(--vault-error)";

    const statusTitle = isUnknownOrUnavailable
      ? "Status unknown"
      : isHealthy && openAnomalies === 0
      ? "All backups healthy"
      : openAnomalies > 0
      ? `${openAnomalies} ${openAnomalies === 1 ? "anomaly" : "anomalies"} detected`
      : "Issues detected";

    const versionEnt = this.getEntity("vault_version");
    const modeEnt = this.getEntity("vault_mode");
    const subText = modeEnt?.state ? `Mode: ${modeEnt.state}` : versionEnt?.state ? `v${versionEnt.state}` : "Vault Backup";

    const iconClass = isUnknownOrUnavailable ? "" : isHealthy ? "success" : "error";

    return html`
      <ha-card>
        <div class="header">
          <div class="header-main">
            <div class="header-icon ${iconClass}">
              ${iconTemplate(mdiHeart, 18)}
            </div>
            <div class="header-titles">
              <span class="header-tag">Health Score</span>
              ${this.config.title ? html`<span class="header-title">${this.config.title}</span>` : ""}
            </div>
          </div>
        </div>

        <div class="kpi-container">
          <div class="score-circle">
            <svg viewBox="0 0 52 52">
              <circle class="score-circle-bg" cx="26" cy="26" r="22"></circle>
              <circle
                class="score-circle-fill"
                style="stroke: ${strokeColor}; stroke-dasharray: ${circumference}; stroke-dashoffset: ${strokeDashoffset};"
                cx="26"
                cy="26"
                r="22"
              ></circle>
            </svg>
            <span class="score-text">${score !== null ? score : "--"}</span>
          </div>

          <div class="kpi-main">
            <span class="kpi-label">${statusTitle}</span>
            <span class="kpi-sub">${subText}</span>
          </div>
        </div>
      </ha-card>
    `;
  }
}

export class VaultHealthCardEditor extends VaultCardEditor {}

registerDashboardCard({
  tag: HEALTH_CARD_TAG,
  editorTag: HEALTH_EDITOR_TAG,
  card: VaultHealthCard,
  editor: VaultHealthCardEditor,
  name: "Vault Health Score",
  description: "Display Vault overall health score gauge and system status",
});
