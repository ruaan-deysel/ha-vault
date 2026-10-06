import { html, type TemplateResult } from "lit";
import { BaseVaultCard } from "./dashboard-cards-base";
import { VaultCardEditor } from "./dashboard-cards-editor";
import { STORAGE_CARD_TAG, STORAGE_EDITOR_TAG } from "./config";
import {
  iconTemplate,
  mdiHarddisk,
} from "./icons";
import { registerDashboardCard } from "./register-dashboard-card";

interface StorageItem {
  id: string;
  name: string;
  type: string;
  health: string;
  usedBytes: number;
  freeBytes: number;
  totalBytes: number;
  usagePct: number;
}

export class VaultStorageCard extends BaseVaultCard {
  static override editorTag = STORAGE_EDITOR_TAG;

  override getCardSize(): number {
    return 4;
  }

  override getGridOptions() {
    return { columns: 6, rows: 4, min_columns: 3, min_rows: 3 };
  }

  private getStorage(): StorageItem[] {
    const totalEntities = this.getEntities("total_space");
    const usedEntities = this.getEntities("used_space");
    const freeEntities = this.getEntities("free_space");
    const typeEntities = this.getEntities("type");
    const healthEntities = this.getEntities("health");

    const storageMap = new Map<string, StorageItem>();

    for (const ent of totalEntities) {
      const match = ent.entity_id.match(/storage_(.*?)_total_space/);
      const token = match && match[1] ? match[1] : "default";

      const typeEnt = typeEntities.find((t) => t.entity_id.includes(`storage_${token}_type`));
      const healthEnt = healthEntities.find((h) => h.entity_id.includes(`storage_${token}_health`));
      const usedEnt = usedEntities.find((u) => u.entity_id.includes(`storage_${token}_used_space`));
      const freeEnt = freeEntities.find((f) => f.entity_id.includes(`storage_${token}_free_space`));

      const totalVal = Number(ent.state || 0);
      const usedVal = Number(usedEnt?.state || 0);
      const freeVal = Number(freeEnt?.state || 0);

      const rawName = (ent.attributes?.friendly_name as string | undefined) || token;
      const cleanName = rawName
        .replace(/total space/i, "")
        .replace(/storage/i, "")
        .replace(/vault backup/i, "")
        .trim();

      const pct = totalVal > 0 ? Math.min(100, Math.round((usedVal / totalVal) * 100)) : 0;

      storageMap.set(token, {
        id: token,
        name: cleanName || token,
        type: (typeEnt?.state || "local").toUpperCase(),
        health: healthEnt?.state || "ok",
        usedBytes: usedVal,
        freeBytes: freeVal,
        totalBytes: totalVal,
        usagePct: pct,
      });
    }

    return Array.from(storageMap.values());
  }

  protected override render(): TemplateResult {
    const storages = this.getStorage();

    return html`
      <ha-card>
        <div class="header">
          <div class="header-main">
            <div class="header-icon">
              ${iconTemplate(mdiHarddisk, 18)}
            </div>
            <div class="header-titles">
              <span class="header-tag">Storage Destinations</span>
              ${this.config.title ? html`<span class="header-title">${this.config.title}</span>` : ""}
            </div>
          </div>
          <span style="font-size: 0.78rem; font-weight: 600; color: var(--vault-accent);">
            ${storages.length} targets
          </span>
        </div>

        <div class="item-list">
          ${storages.length === 0
            ? html`
                <div class="empty-state">
                  <span>No storage destinations configured</span>
                </div>
              `
            : storages.map((s) => {
                const isHealthy = s.health.toLowerCase() === "ok" || s.health.toLowerCase() === "healthy";
                const isHighUsage = s.usagePct >= 90;
                return html`
                  <div class="card-row">
                    <div class="card-row-main">
                      <div class="card-row-title-bar">
                        <span class="card-row-title">${s.name}</span>
                        <span class="badge neutral">${s.type}</span>
                        <span class="badge ${isHealthy ? "success" : "warning"}">
                          <span class="badge-dot"></span>
                          ${isHealthy ? "Healthy" : s.health}
                        </span>
                      </div>

                      <div class="progress-bar" style="margin: 6px 0;">
                        <div
                          class="progress-fill ${isHighUsage ? "error" : s.usagePct > 80 ? "warning" : ""}"
                          style="width: ${s.usagePct}%;"
                        ></div>
                      </div>

                      <div class="card-row-meta">
                        <span>${this.formatBytes(s.freeBytes)} free</span>
                        <span>·</span>
                        <span>${this.formatBytes(s.usedBytes)} of ${this.formatBytes(s.totalBytes)} (${s.usagePct}%)</span>
                      </div>
                    </div>
                  </div>
                `;
              })}
        </div>
      </ha-card>
    `;
  }
}

export class VaultStorageCardEditor extends VaultCardEditor {}

registerDashboardCard({
  tag: STORAGE_CARD_TAG,
  editorTag: STORAGE_EDITOR_TAG,
  card: VaultStorageCard,
  editor: VaultStorageCardEditor,
  name: "Vault Storage",
  description: "Display backup storage destinations and capacity usage",
});
