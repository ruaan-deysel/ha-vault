import { html, type TemplateResult } from "lit";
import { BaseVaultCard } from "./dashboard-cards-base";
import { VaultCardEditor } from "./dashboard-cards-editor";
import { LAST_BACKUP_CARD_TAG, LAST_BACKUP_EDITOR_TAG } from "./config";
import {
  iconTemplate,
  mdiCheckCircle,
} from "./icons";
import { registerDashboardCard } from "./register-dashboard-card";

export class VaultLastBackupCard extends BaseVaultCard {
  static override editorTag = LAST_BACKUP_EDITOR_TAG;

  protected override render(): TemplateResult {
    // Find last run job from state
    const lastRunSensors = this.getEntities("last_run");
    const lastSizeSensors = this.getEntities("last_size");
    const lastDurSensors = this.getEntities("last_duration");
    const statusSensors = this.getEntities("status");

    let latestTime = 0;
    let matchingJobToken = "";
    let jobTitle = "No backups recorded";
    let formattedSize = "--";
    let formattedDuration = "--";
    let isSuccess = true;
    let hasRuns = false;

    for (const s of lastRunSensors) {
      if (!s.state || s.state === "unavailable" || s.state === "unknown") continue;
      const t = new Date(s.state).getTime();
      if (!isNaN(t) && t > latestTime) {
        latestTime = t;
        hasRuns = true;
        const objectId = s.entity_id.split(".")[1] || "";
        matchingJobToken = objectId.replace(/^vault_backup_/, "").replace(/_last_run$/, "");
        const name = s.attributes?.friendly_name as string | undefined;
        if (name) {
          jobTitle = name.replace(/last run/i, "").replace(/vault backup/i, "").trim() || jobTitle;
        } else {
          jobTitle = matchingJobToken || "Backup Job";
        }
      }
    }

    if (hasRuns && matchingJobToken) {
      const sizeEnt = lastSizeSensors.find(
        (s) =>
          s.entity_id.endsWith(`_${matchingJobToken}_last_size`) ||
          s.entity_id.endsWith(`_${matchingJobToken}_size`) ||
          s.entity_id.includes(`_${matchingJobToken}_last_size`)
      );
      const eventEnt = this.getEntities("last_event", "event").find((e) =>
        e.entity_id.includes(matchingJobToken)
      );

      let sizeBytes = this.parseDataSizeBytes(
        sizeEnt?.state,
        sizeEnt?.attributes?.unit_of_measurement as string | undefined
      );
      if (!sizeBytes && eventEnt?.attributes?.size_bytes) {
        sizeBytes = Number(eventEnt.attributes.size_bytes);
      }
      if (sizeBytes > 0) {
        formattedSize = this.formatBytes(sizeBytes);
      }

      const durEnt = lastDurSensors.find(
        (d) =>
          d.entity_id.endsWith(`_${matchingJobToken}_last_duration`) ||
          d.entity_id.endsWith(`_${matchingJobToken}_duration`) ||
          d.entity_id.includes(`_${matchingJobToken}_last_duration`)
      );
      if (durEnt?.state && durEnt.state !== "unavailable" && durEnt.state !== "unknown") {
        formattedDuration = this.formatDuration(durEnt.state);
      }

      const statusEnt = statusSensors.find(
        (st) =>
          st.entity_id.endsWith(`_${matchingJobToken}_status`) ||
          st.entity_id.includes(`_${matchingJobToken}_status`)
      );
      if (statusEnt?.state) {
        const st = statusEnt.state.toLowerCase();
        isSuccess = !["failed", "error", "aborted"].includes(st);
      }
    }

    const timeAgoStr = latestTime > 0 ? this.formatTimeAgo(latestTime) : "--";

    return html`
      <ha-card>
        <div class="header">
          <div class="header-main">
            <div class="header-icon ${hasRuns ? (isSuccess ? "success" : "error") : ""}">
              ${iconTemplate(mdiCheckCircle, 18)}
            </div>
            <div class="header-titles">
              <span class="header-tag">Last Backup</span>
              ${this.config.title ? html`<span class="header-title">${this.config.title}</span>` : ""}
            </div>
          </div>
        </div>

        <div class="kpi-main" style="padding-top: 4px;">
          <div style="display: flex; align-items: center; gap: 6px;">
            ${hasRuns
              ? html`
                  <div class="badge ${isSuccess ? "success" : "error"}">
                    <span class="badge-dot"></span>
                    ${isSuccess ? "Success" : "Failed"}
                  </div>
                `
              : html`
                  <div class="badge neutral">
                    <span class="badge-dot"></span>
                    No Backups
                  </div>
                `}
          </div>

          <span class="kpi-label" style="margin-top: 6px;">
            ${jobTitle}${latestTime > 0 ? ` · ${timeAgoStr}` : ""}
          </span>
          <span class="kpi-sub" style="margin-top: 2px;">
            ${formattedSize} · ${formattedDuration}
          </span>
        </div>
      </ha-card>
    `;
  }
}

export class VaultLastBackupCardEditor extends VaultCardEditor {}

registerDashboardCard({
  tag: LAST_BACKUP_CARD_TAG,
  editorTag: LAST_BACKUP_EDITOR_TAG,
  card: VaultLastBackupCard,
  editor: VaultLastBackupCardEditor,
  name: "Vault Last Backup",
  description: "Display latest backup completion status, size, and duration",
});
