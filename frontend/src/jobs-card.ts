import { html, type TemplateResult } from "lit";
import { BaseVaultCard } from "./dashboard-cards-base";
import { VaultCardEditor } from "./dashboard-cards-editor";
import { JOBS_CARD_TAG, JOBS_EDITOR_TAG } from "./config";
import {
  iconTemplate,
  mdiBriefcaseOutline,
  mdiPlay,
  mdiRestart,
} from "./icons";
import { registerDashboardCard } from "./register-dashboard-card";

interface JobItem {
  id: string;
  jobId?: number;
  name: string;
  status: string;
  isRunning: boolean;
  enabled: boolean;
  compression?: string;
  lastRun?: string;
  duration?: string;
  size?: string;
  restorePoints?: number;
  progress?: number;
  buttonEntityId?: string;
}

export class VaultJobsCard extends BaseVaultCard {
  static override editorTag = JOBS_EDITOR_TAG;

  override getCardSize(): number {
    return 4;
  }

  override getGridOptions() {
    return { columns: 6, rows: 4, min_columns: 3, min_rows: 3 };
  }

  private _runningJobs = new Set<string>();

  private getJobs(): JobItem[] {
    const statusEntities = this.getEntities("status");
    const runningSensors = this.getEntities("running", "binary_sensor");
    const runButtons = this.getEntities("run_now", "button");

    const jobsMap = new Map<string, JobItem>();

    for (const ent of statusEntities) {
      if (
        ent.entity_id === "sensor.vault_status" ||
        ent.entity_id === "sensor.vault_backup_status" ||
        ent.entity_id.includes("storage_")
      ) {
        continue;
      }
      const objectId = ent.entity_id.split(".")[1] || "";
      // Extract job key token
      const jobToken = objectId
        .replace(/^vault_backup_job_/, "")
        .replace(/^vault_backup_/, "")
        .replace(/^vault_job_/, "")
        .replace(/^vault_/, "")
        .replace(/_status$/, "");

      if (!jobToken || jobToken === "backup" || jobToken === "status") {
        continue;
      }

      const cleanName =
        (ent.attributes?.friendly_name as string || jobToken)
          .replace(/status/i, "")
          .replace(/^vault backup/i, "")
          .trim() || jobToken;

      const isRunning =
        runningSensors.some((r) => r.entity_id.includes(jobToken) && r.state === "on") ||
        ent.state.toLowerCase() === "running";

      const btn = runButtons.find(
        (b) =>
          b.entity_id.endsWith(`_${jobToken}_run_backup`) ||
          b.entity_id.endsWith(`_${jobToken}_run_now`) ||
          b.entity_id.endsWith(`_${jobToken}`) ||
          b.entity_id.includes(`_${jobToken}_run_backup`) ||
          b.entity_id.includes(`_${jobToken}_run_now`)
      );

      const compAttr = ent.attributes?.compression as string | undefined;
      const rawJobId = ent.attributes?.job_id;
      const parsedJobId =
        typeof rawJobId === "number"
          ? rawJobId
          : typeof rawJobId === "string" && !isNaN(Number(rawJobId))
          ? Number(rawJobId)
          : undefined;

      jobsMap.set(jobToken, {
        id: jobToken,
        jobId: parsedJobId,
        name: cleanName,
        status: ent.state || "idle",
        isRunning,
        enabled: ent.state !== "disabled",
        compression: compAttr || undefined,
        buttonEntityId: btn?.entity_id,
      });
    }

    return Array.from(jobsMap.values());
  }

  private async _handleRunNow(job: JobItem): Promise<void> {
    if (this._runningJobs.has(job.id)) return;
    this._runningJobs.add(job.id);
    this.requestUpdate();

    try {
      if (job.buttonEntityId) {
        await this.callAction("button", "press", { entity_id: job.buttonEntityId });
      } else if (job.jobId !== undefined) {
        await this.callAction("vault", "run_backup", { job_id: job.jobId });
      } else {
        await this.callAction("vault", "run_backup", { job_name: job.name });
      }
    } catch (err) {
      console.error(`Failed to trigger job ${job.name}:`, err);
    } finally {
      setTimeout(() => {
        this._runningJobs.delete(job.id);
        this.requestUpdate();
      }, 3000);
    }
  }

  protected override render(): TemplateResult {
    const jobs = this.getJobs();

    return html`
      <ha-card>
        <div class="header">
          <div class="header-main">
            <div class="header-icon">
              ${iconTemplate(mdiBriefcaseOutline, 18)}
            </div>
            <div class="header-titles">
              <span class="header-tag">Backup Jobs</span>
              ${this.config.title ? html`<span class="header-title">${this.config.title}</span>` : ""}
            </div>
          </div>
          <span style="font-size: 0.78rem; font-weight: 600; color: var(--vault-accent);">
            ${jobs.length} jobs
          </span>
        </div>

        <div class="item-list">
          ${jobs.length === 0
            ? html`
                <div class="empty-state">
                  <span>No backup jobs found on this Vault instance</span>
                </div>
              `
            : jobs.map((job) => {
                const inProgress = job.isRunning || this._runningJobs.has(job.id);
                return html`
                  <div class="card-row">
                    <div class="card-row-main">
                      <div class="card-row-title-bar">
                        <span class="card-row-title">${job.name}</span>
                        ${job.isRunning
                          ? html`
                              <span class="badge running">
                                <span class="badge-dot"></span>
                                Running
                              </span>
                            `
                          : job.status.toLowerCase() === "completed"
                          ? html`
                              <span class="badge success">
                                <span class="badge-dot"></span>
                                Completed
                              </span>
                            `
                          : html`
                              <span class="badge neutral">
                                ${job.enabled ? "Enabled" : "Disabled"}
                              </span>
                            `}
                      </div>
                      <div class="card-row-meta">
                        <span>${job.enabled ? "Enabled" : "Disabled"}${job.compression ? ` · ${job.compression}` : ""}</span>
                      </div>
                    </div>

                    <div class="card-row-actions">
                      ${this.getActiveDevice()?.configuration_url
                        ? html`
                            <button
                              class="btn"
                              title="Restore"
                              @click="${() => {
                                const url = this.getActiveDevice()?.configuration_url;
                                if (url) window.open(url, "_blank");
                              }}"
                            >
                              ${iconTemplate(mdiRestart, 14)}
                              Restore
                            </button>
                          `
                        : ""}

                      <button
                        class="btn amber"
                        ?disabled="${inProgress}"
                        @click="${() => this._handleRunNow(job)}"
                      >
                        ${iconTemplate(mdiPlay, 14)}
                        ${inProgress ? "Starting..." : "Run Now"}
                      </button>
                    </div>
                  </div>
                `;
              })}
        </div>
      </ha-card>
    `;
  }
}

export class VaultJobsCardEditor extends VaultCardEditor {}

registerDashboardCard({
  tag: JOBS_CARD_TAG,
  editorTag: JOBS_EDITOR_TAG,
  card: VaultJobsCard,
  editor: VaultJobsCardEditor,
  name: "Vault Backup Jobs",
  description: "Display backup jobs with quick Run Now and Restore controls",
});
