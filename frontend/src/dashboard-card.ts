import { css, html, type TemplateResult } from "lit";
import { BaseVaultCard } from "./dashboard-cards-base";
import { VaultCardEditor } from "./dashboard-cards-editor";
import { DASHBOARD_CARD_TAG, DASHBOARD_EDITOR_TAG } from "./config";
import {
  iconTemplate,
  mdiShieldCheck,
} from "./icons";
import { registerDashboardCard } from "./register-dashboard-card";

// Ensure sub-cards are registered
import "./health-card";
import "./protected-card";
import "./next-run-card";
import "./last-backup-card";
import "./progress-card";
import "./rules-card";
import "./jobs-card";
import "./activity-card";
import "./storage-card";
import "./anomalies-card";

export class VaultDashboardCard extends BaseVaultCard {
  static override editorTag = DASHBOARD_EDITOR_TAG;

  static override styles = [
    ...BaseVaultCard.styles,
    css`
      .dash-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin-top: 4px;
      }

      .dash-sections {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 12px;
        margin-top: 8px;
      }

      @media (max-width: 768px) {
        .dash-grid {
          grid-template-columns: repeat(2, 1fr);
        }
        .dash-sections {
          grid-template-columns: 1fr;
        }
      }

      @media (max-width: 480px) {
        .dash-grid {
          grid-template-columns: 1fr;
        }
      }
    `,
  ];

  override getCardSize(): number {
    return 8;
  }

  override getGridOptions() {
    return { columns: 12, rows: 8, min_columns: 6, min_rows: 4 };
  }

  protected override render(): TemplateResult {
    const onlineEnt = this.getEntity("online", "binary_sensor") || this.getEntity("vault_online", "binary_sensor");
    const isOnline = onlineEnt ? onlineEnt.state === "on" : true;
    const versionEnt = this.getEntity("vault_version") || this.getEntity("version");

    const device = this.getActiveDevice();
    const serverName = device?.name_by_user || device?.name || "Vault Backup";
    const versionStr = versionEnt?.state ? `v${versionEnt.state}` : "";

    return html`
      <ha-card>
        <div class="header" style="border-bottom: 1px solid var(--vault-border); padding-bottom: 10px;">
          <div class="header-main">
            <div class="header-icon ${isOnline ? "success" : "error"}">
              ${iconTemplate(mdiShieldCheck, 20)}
            </div>
            <div class="header-titles">
              <span class="header-title">${this.config.title || serverName}</span>
              <span class="header-subtitle">Vault Unraid Backup Daemon ${versionStr}</span>
            </div>
          </div>
          <div class="header-actions">
            <div class="badge ${isOnline ? "success" : "error"}">
              <span class="badge-dot"></span>
              ${isOnline ? "Online" : "Offline"}
            </div>
          </div>
        </div>

        <!-- KPI Row: 4 At-a-Glance Tiles -->
        <div class="dash-grid">
          <vault-health-card
            embedded
            .hass="${this.hass}"
            .config="${{ type: "custom:vault-health-card", embedded: true, server: this.config.server }}"
          ></vault-health-card>

          <vault-protected-card
            embedded
            .hass="${this.hass}"
            .config="${{ type: "custom:vault-protected-card", embedded: true, server: this.config.server }}"
          ></vault-protected-card>

          <vault-next-run-card
            embedded
            .hass="${this.hass}"
            .config="${{ type: "custom:vault-next-run-card", embedded: true, server: this.config.server }}"
          ></vault-next-run-card>

          <vault-last-backup-card
            embedded
            .hass="${this.hass}"
            .config="${{ type: "custom:vault-last-backup-card", embedded: true, server: this.config.server }}"
          ></vault-last-backup-card>
        </div>

        <!-- Backup in progress banner -->
        <vault-progress-card
          embedded
          .hass="${this.hass}"
          .config="${{ type: "custom:vault-progress-card", embedded: true, server: this.config.server }}"
        ></vault-progress-card>

        <!-- Main Sections: Jobs & Activity -->
        <div class="dash-sections">
          <vault-jobs-card
            embedded
            .hass="${this.hass}"
            .config="${{ type: "custom:vault-jobs-card", embedded: true, server: this.config.server }}"
          ></vault-jobs-card>

          <vault-activity-card
            embedded
            .hass="${this.hass}"
            .config="${{ type: "custom:vault-activity-card", embedded: true, server: this.config.server }}"
          ></vault-activity-card>
        </div>

        <!-- Storage & 3-2-1 Row -->
        <div class="dash-sections">
          <vault-storage-card
            embedded
            .hass="${this.hass}"
            .config="${{ type: "custom:vault-storage-card", embedded: true, server: this.config.server }}"
          ></vault-storage-card>

          <vault-rules-card
            embedded
            .hass="${this.hass}"
            .config="${{ type: "custom:vault-rules-card", embedded: true, server: this.config.server }}"
          ></vault-rules-card>
        </div>
      </ha-card>
    `;
  }
}

export class VaultDashboardCardEditor extends VaultCardEditor {}

registerDashboardCard({
  tag: DASHBOARD_CARD_TAG,
  editorTag: DASHBOARD_EDITOR_TAG,
  card: VaultDashboardCard,
  editor: VaultDashboardCardEditor,
  name: "Vault Dashboard",
  description: "Complete unified dashboard replicating the Vault backup interface",
});
