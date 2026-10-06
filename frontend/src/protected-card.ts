import { html, type TemplateResult } from "lit";
import { BaseVaultCard } from "./dashboard-cards-base";
import { VaultCardEditor } from "./dashboard-cards-editor";
import { PROTECTED_CARD_TAG, PROTECTED_EDITOR_TAG } from "./config";
import {
  iconTemplate,
  mdiShieldOutline,
} from "./icons";
import { registerDashboardCard } from "./register-dashboard-card";

export class VaultProtectedCard extends BaseVaultCard {
  static override editorTag = PROTECTED_EDITOR_TAG;

  protected override render(): TemplateResult {
    const totalJobsEnt = this.getEntity("total_jobs") || this.getEntity("jobs_total");
    const enabledJobsEnt = this.getEntity("enabled_jobs") || this.getEntity("jobs_enabled");

    const totalJobs = Number(totalJobsEnt?.state ?? 0);
    const enabledJobs = Number(enabledJobsEnt?.state ?? totalJobs);

    const pct = totalJobs > 0 ? Math.round((enabledJobs / totalJobs) * 100) : 100;
    const isAllCovered = enabledJobs >= totalJobs && totalJobs > 0;

    return html`
      <ha-card>
        <div class="header">
          <div class="header-main">
            <div class="header-icon ${isAllCovered ? "success" : ""}">
              ${iconTemplate(mdiShieldOutline, 18)}
            </div>
            <div class="header-titles">
              <span class="header-tag">Protected</span>
              ${this.config.title ? html`<span class="header-title">${this.config.title}</span>` : ""}
            </div>
          </div>
        </div>

        <div class="kpi-main" style="padding-top: 4px;">
          <div class="kpi-value-row">
            <span class="kpi-value">${enabledJobs}</span>
            <span class="kpi-unit">/${totalJobs || enabledJobs}</span>
          </div>

          <div class="progress-bar" style="margin: 8px 0 6px 0;">
            <div
              class="progress-fill ${isAllCovered ? "" : "warning"}"
              style="width: ${pct}%;"
            ></div>
          </div>

          <span class="kpi-sub">
            ${isAllCovered ? "All items covered" : `${enabledJobs} of ${totalJobs} jobs active`}
          </span>
        </div>
      </ha-card>
    `;
  }
}

export class VaultProtectedCardEditor extends VaultCardEditor {}

registerDashboardCard({
  tag: PROTECTED_CARD_TAG,
  editorTag: PROTECTED_EDITOR_TAG,
  card: VaultProtectedCard,
  editor: VaultProtectedCardEditor,
  name: "Vault Protected Items",
  description: "Display protected items and enabled jobs coverage",
});
