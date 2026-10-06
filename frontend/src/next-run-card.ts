import { html, type TemplateResult } from "lit";
import { BaseVaultCard } from "./dashboard-cards-base";
import { VaultCardEditor } from "./dashboard-cards-editor";
import { NEXT_RUN_CARD_TAG, NEXT_RUN_EDITOR_TAG } from "./config";
import {
  iconTemplate,
  mdiClockOutline,
} from "./icons";
import { registerDashboardCard } from "./register-dashboard-card";

export class VaultNextRunCard extends BaseVaultCard {
  static override editorTag = NEXT_RUN_EDITOR_TAG;

  protected override render(): TemplateResult {
    const totalJobsEnt = this.getEntity("total_jobs") || this.getEntity("jobs_total");
    const enabledJobsEnt = this.getEntity("enabled_jobs") || this.getEntity("jobs_enabled");
    const runnerJobEnt = this.getEntity("runner_active_job") || this.getEntity("runner_current_job_id");

    const statusEntities = this.getEntities("status").filter(
      (e) => !e.entity_id.includes("vault_status") && !e.entity_id.includes("storage_")
    );
    const totalJobs = Number(totalJobsEnt?.state ?? (statusEntities.length || 0));
    const enabledJobs = Number(enabledJobsEnt?.state ?? totalJobs);

    const activeJob = runnerJobEnt?.state && runnerJobEnt.state !== "idle" ? runnerJobEnt.state : null;

    // Find upcoming job from next_run entities or fallback to existing jobs
    const nextRunSensors = this.getEntities("next_run");
    const lastRunSensors = this.getEntities("last_run");
    let nextJobName = "";
    let nextRunTime: number | null = null;

    for (const n of nextRunSensors) {
      if (!n.state || n.state === "unavailable" || n.state === "unknown") continue;
      const t = new Date(n.state).getTime();
      const now = Date.now();
      if (!isNaN(t) && t > now && (nextRunTime === null || t < nextRunTime)) {
        nextRunTime = t;
        const match = n.attributes?.friendly_name as string | undefined;
        const objectId = n.entity_id.split(".")[1] || "";
        const jobToken = objectId.replace(/^vault_backup_/, "").replace(/_next_run$/, "");
        nextJobName = match?.replace(/next run/i, "").replace(/vault backup/i, "").trim() || jobToken || "Backup Job";
      }
    }

    if (!nextJobName && lastRunSensors.length > 0 && lastRunSensors[0]) {
      const match = lastRunSensors[0].attributes?.friendly_name as string | undefined;
      if (match) {
        nextJobName = match.replace(/last run/i, "").replace(/vault backup/i, "").trim() || "";
      }
    }

    if (!nextJobName && statusEntities.length > 0 && statusEntities[0]) {
      const match = statusEntities[0].attributes?.friendly_name as string | undefined;
      nextJobName = match?.replace(/status/i, "").replace(/vault backup/i, "").trim() || "";
    }

    if (!nextJobName) {
      nextJobName = enabledJobs > 0 ? "Scheduled Jobs" : "No active jobs";
    }

    const displayTime = activeJob
      ? "Running now"
      : nextRunTime
      ? this.formatTimeAgo(nextRunTime)
      : enabledJobs > 0
      ? "Scheduled"
      : "Idle";
    const subText = activeJob ? `Active: ${activeJob}` : nextJobName;
    const footerText = `${totalJobs} jobs · ${enabledJobs} enabled`;

    return html`
      <ha-card>
        <div class="header">
          <div class="header-main">
            <div class="header-icon">
              ${iconTemplate(mdiClockOutline, 18)}
            </div>
            <div class="header-titles">
              <span class="header-tag">Next Run</span>
              ${this.config.title ? html`<span class="header-title">${this.config.title}</span>` : ""}
            </div>
          </div>
        </div>

        <div class="kpi-main" style="padding-top: 4px;">
          <div class="kpi-value-row">
            <span class="kpi-value" style="font-size: ${activeJob ? "1.4rem" : "1.7rem"};">
              ${displayTime}
            </span>
          </div>

          <span class="kpi-label" style="margin-top: 4px;">${subText}</span>
          <span class="kpi-sub" style="margin-top: 2px;">${footerText}</span>
        </div>
      </ha-card>
    `;
  }
}

export class VaultNextRunCardEditor extends VaultCardEditor {}

registerDashboardCard({
  tag: NEXT_RUN_CARD_TAG,
  editorTag: NEXT_RUN_EDITOR_TAG,
  card: VaultNextRunCard,
  editor: VaultNextRunCardEditor,
  name: "Vault Next Run",
  description: "Display next scheduled backup run and job status",
});
