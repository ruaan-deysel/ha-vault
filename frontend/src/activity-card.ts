import { html, type TemplateResult } from "lit";
import { BaseVaultCard } from "./dashboard-cards-base";
import { VaultCardEditor } from "./dashboard-cards-editor";
import { ACTIVITY_CARD_TAG, ACTIVITY_EDITOR_TAG } from "./config";
import {
  iconTemplate,
  mdiCheck,
  mdiFormatListBulleted,
} from "./icons";
import { registerDashboardCard } from "./register-dashboard-card";

interface ActivityItem {
  id: string;
  jobName: string;
  status: string;
  timeStr: string;
  durationStr: string;
  sizeStr: string;
  itemsStr: string;
  itemsList: string[];
}

export class VaultActivityCard extends BaseVaultCard {
  static override editorTag = ACTIVITY_EDITOR_TAG;

  override getCardSize(): number {
    return 5;
  }

  override getGridOptions() {
    return { columns: 6, rows: 5, min_columns: 4, min_rows: 3 };
  }

  private getActivity(): ActivityItem[] {
    const lastRunSensors = this.getEntities("last_run");
    const lastSizeSensors = this.getEntities("last_size");
    const lastDurSensors = this.getEntities("last_duration");
    const lastItemsSensors = this.getEntities("items_backed_up");

    const activities: ActivityItem[] = [];

    for (const runEnt of lastRunSensors) {
      if (!runEnt.state || runEnt.state === "unavailable" || runEnt.state === "unknown") continue;
      const objectId = runEnt.entity_id.split(".")[1] || "";
      const jobToken = objectId.replace(/^vault_backup_/, "").replace(/_last_run$/, "");
      const cleanName = (runEnt.attributes?.friendly_name as string || jobToken)
        .replace(/last run/i, "")
        .replace(/vault backup/i, "")
        .trim();

      const sizeEnt = lastSizeSensors.find(
        (s) =>
          s.entity_id.endsWith(`_${jobToken}_last_size`) ||
          s.entity_id.endsWith(`_${jobToken}_size`) ||
          s.entity_id.includes(`_${jobToken}_last_size`)
      );
      const durEnt = lastDurSensors.find(
        (d) =>
          d.entity_id.endsWith(`_${jobToken}_last_duration`) ||
          d.entity_id.endsWith(`_${jobToken}_duration`) ||
          d.entity_id.includes(`_${jobToken}_last_duration`)
      );
      const itemsEnt = lastItemsSensors.find(
        (i) =>
          i.entity_id.endsWith(`_${jobToken}_items_backed_up`) ||
          i.entity_id.includes(`_${jobToken}_items_backed_up`)
      );

      const eventEnt = this.getEntities("last_event", "event").find((e) =>
        e.entity_id.includes(jobToken)
      );

      let sizeBytes = this.parseDataSizeBytes(
        sizeEnt?.state,
        sizeEnt?.attributes?.unit_of_measurement as string | undefined
      );
      if (!sizeBytes && eventEnt?.attributes?.size_bytes) {
        sizeBytes = Number(eventEnt.attributes.size_bytes);
      }

      const durStr = this.formatDuration(durEnt?.state);
      const itemsVal = Number(itemsEnt?.state || eventEnt?.attributes?.items_done || 0);

      // Date formatting
      let timeFormatted = runEnt.state;
      try {
        const d = new Date(runEnt.state);
        if (!isNaN(d.getTime())) {
          timeFormatted = d.toLocaleDateString("en-US", {
            day: "numeric",
            month: "short",
            hour: "2-digit",
            minute: "2-digit",
          });
        }
      } catch {
        // keep fallback
      }

      // Item tags extracted from real entity attributes
      let realItems: string[] = [];
      const rawItems =
        runEnt.attributes?.items ||
        runEnt.attributes?.item_names ||
        itemsEnt?.attributes?.items ||
        itemsEnt?.attributes?.item_names;
      if (Array.isArray(rawItems)) {
        realItems = rawItems.map((item) => String(item).trim()).filter(Boolean);
      }

      // Status extracted from real entity attributes or state
      const runStatus = String(
        runEnt.attributes?.status ||
        runEnt.attributes?.last_status ||
        itemsEnt?.attributes?.status ||
        eventEnt?.attributes?.status ||
        "completed"
      ).toLowerCase();

      activities.push({
        id: jobToken,
        jobName: cleanName,
        status: runStatus,
        timeStr: timeFormatted,
        durationStr: durStr,
        sizeStr: this.formatBytes(sizeBytes),
        itemsStr: itemsVal > 0 ? `${itemsVal} items` : "--",
        itemsList: realItems,
      });
    }

    return activities;
  }

  protected override render(): TemplateResult {
    const activities = this.getActivity();

    return html`
      <ha-card>
        <div class="header">
          <div class="header-main">
            <div class="header-icon">
              ${iconTemplate(mdiFormatListBulleted, 18)}
            </div>
            <div class="header-titles">
              <span class="header-tag">Recent Activity</span>
              ${this.config.title ? html`<span class="header-title">${this.config.title}</span>` : ""}
            </div>
          </div>
        </div>

        <div class="item-list" style="margin-top: 4px;">
          ${activities.length === 0
            ? html`
                <div class="empty-state">
                  <span>No recent backup activity recorded</span>
                </div>
              `
            : activities.map(
                (act) => html`
                  <div class="card-row" style="flex-direction: column; align-items: stretch; gap: 8px;">
                    <div style="display: flex; align-items: center; justify-content: space-between; gap: 8px;">
                      <div style="display: flex; align-items: center; gap: 8px;">
                        <span
                          style="width: 8px; height: 8px; border-radius: 50%; background: ${act.status === "failed" || act.status === "error" ? "var(--vault-error)" : "var(--vault-success)"}; display: inline-block;"
                        ></span>
                        <span style="font-size: 0.88rem; font-weight: 600; color: var(--vault-text);">
                          ${act.jobName}
                        </span>
                        <span class="badge ${act.status === "failed" || act.status === "error" ? "error" : "success"}" style="font-size: 0.68rem; padding: 1px 6px;">
                          ${act.status}
                        </span>
                      </div>
                      <span style="font-size: 0.72rem; color: var(--vault-subtext);">
                        ${act.timeStr}
                      </span>
                    </div>

                    ${act.itemsList.length > 0
                      ? html`
                          <div class="chip-container">
                            ${act.itemsList.map(
                              (item) => html`
                                <span class="chip success">
                                  ${iconTemplate(mdiCheck, 12)}
                                  ${item}
                                </span>
                              `
                            )}
                          </div>
                        `
                      : ""}

                    <div style="font-size: 0.72rem; color: var(--vault-subtext); border-top: 1px solid var(--vault-border); padding-top: 6px; display: flex; gap: 8px;">
                      <span>${act.durationStr}</span>
                      <span>·</span>
                      <span>${act.sizeStr}</span>
                      <span>·</span>
                      <span>${act.itemsStr}</span>
                    </div>
                  </div>
                `
              )}
        </div>
      </ha-card>
    `;
  }
}

export class VaultActivityCardEditor extends VaultCardEditor {}

registerDashboardCard({
  tag: ACTIVITY_CARD_TAG,
  editorTag: ACTIVITY_EDITOR_TAG,
  card: VaultActivityCard,
  editor: VaultActivityCardEditor,
  name: "Vault Recent Activity",
  description: "Display backup history timeline with backed up items tags",
});
