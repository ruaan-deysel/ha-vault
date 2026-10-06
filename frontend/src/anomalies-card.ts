import { html, type TemplateResult } from "lit";
import { BaseVaultCard } from "./dashboard-cards-base";
import { VaultCardEditor } from "./dashboard-cards-editor";
import { ANOMALIES_CARD_TAG, ANOMALIES_EDITOR_TAG } from "./config";
import {
  iconTemplate,
  mdiAlertOutline,
  mdiShieldCheck,
} from "./icons";
import { registerDashboardCard } from "./register-dashboard-card";

export class VaultAnomaliesCard extends BaseVaultCard {
  static override editorTag = ANOMALIES_EDITOR_TAG;

  override getGridOptions() {
    return { columns: 6, rows: 3, min_columns: 3, min_rows: 2 };
  }

  protected override render(): TemplateResult {
    const anomaliesEnt = this.getEntity("open_anomalies");
    const count = Number(anomaliesEnt?.state ?? 0);
    const anomaliesList = (anomaliesEnt?.attributes?.anomalies as Array<{
      detector?: string;
      severity?: string;
      summary?: string;
      job?: string;
    }>) || [];

    return html`
      <ha-card>
        <div class="header">
          <div class="header-main">
            <div class="header-icon ${count > 0 ? "error" : "success"}">
              ${iconTemplate(count > 0 ? mdiAlertOutline : mdiShieldCheck, 18)}
            </div>
            <div class="header-titles">
              <span class="header-tag">Anomalies & Attention</span>
              ${this.config.title ? html`<span class="header-title">${this.config.title}</span>` : ""}
            </div>
          </div>
          <div class="badge ${count > 0 ? "warning" : "success"}">
            ${count === 0 ? "Clear" : `${count} Issue${count === 1 ? "" : "s"}`}
          </div>
        </div>

        ${count === 0
          ? html`
              <div style="display: flex; align-items: center; gap: 12px; padding: 12px 4px;">
                <div style="color: var(--vault-success);">
                  ${iconTemplate(mdiShieldCheck, 24)}
                </div>
                <div style="display: flex; flex-direction: column;">
                  <span style="font-size: 0.95rem; font-weight: 600; color: var(--vault-text);">
                    No open anomalies
                  </span>
                  <span style="font-size: 0.78rem; color: var(--vault-subtext);">
                    All backup monitors and detectors report normal operation
                  </span>
                </div>
              </div>
            `
          : html`
              <div class="item-list">
                ${anomaliesList.map(
                  (a) => html`
                    <div class="card-row">
                      <div class="card-row-main">
                        <div class="card-row-title-bar">
                          <span class="card-row-title">${a.summary || a.detector || "Anomaly"}</span>
                          <span class="badge ${a.severity === "critical" ? "error" : "warning"}">
                            ${a.severity || "warning"}
                          </span>
                        </div>
                        <div class="card-row-meta">
                          <span>${a.job ? `Scope: ${a.job}` : "System detector"}</span>
                        </div>
                      </div>
                    </div>
                  `
                )}
              </div>
            `}
      </ha-card>
    `;
  }
}

export class VaultAnomaliesCardEditor extends VaultCardEditor {}

registerDashboardCard({
  tag: ANOMALIES_CARD_TAG,
  editorTag: ANOMALIES_EDITOR_TAG,
  card: VaultAnomaliesCard,
  editor: VaultAnomaliesCardEditor,
  name: "Vault Anomalies",
  description: "Display backup anomalies and attention alerts",
});
