import { html, type TemplateResult } from "lit";
import { BaseVaultCard } from "./dashboard-cards-base";
import { VaultCardEditor } from "./dashboard-cards-editor";
import { STORAGE_CARD_TAG, STORAGE_EDITOR_TAG } from "./config";
import {
  iconTemplate,
  mdiHarddisk,
} from "./icons";
import { registerDashboardCard } from "./register-dashboard-card";
import type { HassEntity } from "./ha-types";

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
    if (!this.hass?.states) return [];

    const storageMap = new Map<string, StorageItem>();
    const storageEntities: HassEntity[] = [];

    for (const [entityId, entity] of Object.entries(this.hass.states)) {
      if (entityId.startsWith("sensor.") && entityId.includes("storage_")) {
        storageEntities.push(entity);
      }
    }

    const tokens = new Set<string>();
    for (const ent of storageEntities) {
      const match = ent.entity_id.match(/storage_([a-z0-9_]+?)_(?:name|type|health|free_space|used_space|total_space)$/);
      if (match && match[1]) {
        tokens.add(match[1]);
      }
    }

    for (const token of tokens) {
      const nameEnt = storageEntities.find((e) => e.entity_id.endsWith(`storage_${token}_name`));
      const typeEnt = storageEntities.find((e) => e.entity_id.endsWith(`storage_${token}_type`));
      const healthEnt = storageEntities.find((e) => e.entity_id.endsWith(`storage_${token}_health`));
      const freeEnt = storageEntities.find((e) => e.entity_id.endsWith(`storage_${token}_free_space`));
      const usedEnt = storageEntities.find((e) => e.entity_id.endsWith(`storage_${token}_used_space`));
      const totalEnt = storageEntities.find((e) => e.entity_id.endsWith(`storage_${token}_total_space`));

      const freeBytes = this.parseDataSizeBytes(freeEnt?.state, freeEnt?.attributes?.unit_of_measurement as string | undefined);
      const usedBytes =
        this.parseDataSizeBytes(usedEnt?.state, usedEnt?.attributes?.unit_of_measurement as string | undefined) ||
        Number(freeEnt?.attributes?.used_bytes || 0);
      const totalBytes =
        this.parseDataSizeBytes(totalEnt?.state, totalEnt?.attributes?.unit_of_measurement as string | undefined) ||
        Number(freeEnt?.attributes?.total_bytes || 0);

      let cleanName = nameEnt?.state;
      if (!cleanName || cleanName === "unavailable" || cleanName === "unknown") {
        const rawName = (freeEnt?.attributes?.friendly_name || token) as string;
        cleanName = rawName
          .replace(/free space/i, "")
          .replace(/total space/i, "")
          .replace(/used space/i, "")
          .replace(/storage/i, "")
          .replace(/vault backup/i, "")
          .trim() || token;
      }

      let pct = 0;
      if (totalBytes > 0 && usedBytes > 0) {
        pct = Math.min(100, Math.round((usedBytes / totalBytes) * 100));
      } else if (totalBytes > 0 && freeBytes > 0) {
        const calcUsed = Math.max(0, totalBytes - freeBytes);
        pct = Math.min(100, Math.round((calcUsed / totalBytes) * 100));
      }

      storageMap.set(token, {
        id: token,
        name: cleanName,
        type: (typeEnt?.state && typeEnt.state !== "unavailable" ? typeEnt.state : "local").toUpperCase(),
        health: (healthEnt?.state && healthEnt.state !== "unavailable" ? healthEnt.state : "ok"),
        usedBytes,
        freeBytes,
        totalBytes,
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

                      ${s.totalBytes > 0
                        ? html`
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
                          `
                        : html`
                            <div class="progress-bar" style="margin: 6px 0;">
                              <div
                                class="progress-fill"
                                style="width: 100%;"
                              ></div>
                            </div>

                            <div class="card-row-meta">
                              <span>${this.formatBytes(s.freeBytes)} free</span>
                              <span>·</span>
                              <span>Destination active</span>
                            </div>
                          `}
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
