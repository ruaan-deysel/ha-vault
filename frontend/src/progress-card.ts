import { html, type TemplateResult } from "lit";
import { BaseVaultCard } from "./dashboard-cards-base";
import { VaultCardEditor } from "./dashboard-cards-editor";
import { PROGRESS_CARD_TAG, PROGRESS_EDITOR_TAG } from "./config";
import {
  iconTemplate,
  mdiShieldCheck,
  mdiSync,
} from "./icons";
import { registerDashboardCard } from "./register-dashboard-card";

export class VaultProgressCard extends BaseVaultCard {
  static override editorTag = PROGRESS_EDITOR_TAG;

  override getGridOptions() {
    return { columns: 6, rows: 3, min_columns: 3, min_rows: 2 };
  }

  protected override render(): TemplateResult {
    const runningSensors = this.getEntities("running", "binary_sensor");
    const activeRunnerEnt = this.getEntity("runner_active_job") || this.getEntity("runner_current_job_id");

    const isRunning =
      runningSensors.some((s) => s.state === "on") ||
      (activeRunnerEnt?.state && activeRunnerEnt.state !== "idle");

    const runningSensor = runningSensors.find((s) => s.state === "on");
    const activeFriendlyName = runningSensor?.attributes?.friendly_name as string | undefined;
    const activeJobName =
      activeRunnerEnt?.state && activeRunnerEnt.state !== "idle"
        ? activeRunnerEnt.state
        : activeFriendlyName?.replace(/running/i, "").trim() || "Backup job";

    // Progress percentage
    const progressSensors = this.getEntities("progress");
    let progressVal = 0;
    for (const p of progressSensors) {
      const v = Number(p.state);
      if (!isNaN(v) && v > 0) {
        progressVal = v;
        break;
      }
    }

    return html`
      <ha-card>
        <div class="header">
          <div class="header-main">
            <div class="header-icon ${isRunning ? "running" : ""}">
              ${iconTemplate(mdiSync, 18)}
            </div>
            <div class="header-titles">
              <span class="header-tag">Backup In Progress</span>
              ${this.config.title ? html`<span class="header-title">${this.config.title}</span>` : ""}
            </div>
          </div>
          ${isRunning
            ? html`
                <div class="badge running">
                  <span class="badge-dot"></span>
                  Active
                </div>
              `
            : ""}
        </div>

        ${isRunning
          ? html`
              <div class="card-row" style="margin-top: 4px;">
                <div class="card-row-main">
                  <div class="card-row-title-bar">
                    <span class="card-row-title">${activeJobName}</span>
                    <span class="badge running">${progressVal}%</span>
                  </div>
                  <div class="progress-bar" style="margin: 6px 0;">
                    <div
                      class="progress-fill running"
                      style="width: ${Math.max(5, progressVal)}%;"
                    ></div>
                  </div>
                  <div class="card-row-meta">
                    <span>Backing up items...</span>
                  </div>
                </div>
              </div>
            `
          : html`
              <div style="display: flex; align-items: center; gap: 12px; padding: 12px 4px;">
                <div style="color: var(--vault-standby);">
                  ${iconTemplate(mdiShieldCheck, 24)}
                </div>
                <div style="display: flex; flex-direction: column;">
                  <span style="font-size: 0.95rem; font-weight: 600; color: var(--vault-text);">
                    No backup running
                  </span>
                  <span style="font-size: 0.78rem; color: var(--vault-subtext);">
                    Next scheduled run will start automatically
                  </span>
                </div>
              </div>
            `}
      </ha-card>
    `;
  }
}

export class VaultProgressCardEditor extends VaultCardEditor {}

registerDashboardCard({
  tag: PROGRESS_CARD_TAG,
  editorTag: PROGRESS_EDITOR_TAG,
  card: VaultProgressCard,
  editor: VaultProgressCardEditor,
  name: "Vault Backup In Progress",
  description: "Display active backup job progress or idle state",
});
