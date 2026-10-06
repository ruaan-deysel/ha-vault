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
    const statusEntities = this.getEntities("status").filter(
      (e) => !e.entity_id.includes("vault_status") && !e.entity_id.includes("storage_")
    );

    const rawTotal = Number(totalJobsEnt?.state ?? 0);
    const rawEnabled = Number(enabledJobsEnt?.state ?? 0);

    const itemsBackedUpEntities = this.getEntities("items_backed_up");
    const itemsFailedEntities = this.getEntities("items_failed");
    let itemsProtected = 0;
    let itemsFailed = 0;
    for (const ent of itemsBackedUpEntities) {
      const val = Number(ent.state);
      if (!isNaN(val) && val > 0) itemsProtected += val;
    }
    for (const ent of itemsFailedEntities) {
      const val = Number(ent.state);
      if (!isNaN(val) && val > 0) itemsFailed += val;
    }

    let coveredCount = 0;
    let totalCount = 0;

    if (rawTotal > 0) {
      totalCount = rawTotal;
      coveredCount = rawEnabled > 0 ? rawEnabled : rawTotal;
    } else if (itemsProtected > 0 || itemsFailed > 0) {
      coveredCount = itemsProtected;
      totalCount = itemsProtected + itemsFailed;
    } else if (statusEntities.length > 0) {
      totalCount = statusEntities.length;
      coveredCount = statusEntities.filter((s) => s.state !== "disabled").length || totalCount;
    }

    const pct = totalCount > 0 ? Math.min(100, Math.round((coveredCount / totalCount) * 100)) : 100;
    const isAllCovered = totalCount > 0 && coveredCount >= totalCount && itemsFailed === 0;

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
            <span class="kpi-value">${coveredCount}</span>
            <span class="kpi-unit">/${totalCount || coveredCount}</span>
          </div>

          <div class="progress-bar" style="margin: 8px 0 6px 0;">
            <div
              class="progress-fill ${isAllCovered ? "" : "warning"}"
              style="width: ${pct}%;"
            ></div>
          </div>

          <span class="kpi-sub">
            ${isAllCovered
              ? "All items covered"
              : itemsFailed > 0
              ? `${itemsFailed} failed item${itemsFailed === 1 ? "" : "s"}`
              : `${coveredCount} of ${totalCount} jobs active`}
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
