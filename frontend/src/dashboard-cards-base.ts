import { LitElement, type PropertyValues } from "lit";
import { type CardConfig } from "./config";
import { dashboardCardStyles } from "./dashboard-cards-styles";
import {
  type DeviceRegistryEntry,
  type HassEntity,
  type HomeAssistant,
} from "./ha-types";

export abstract class BaseVaultCard extends LitElement {
  static override styles = dashboardCardStyles;
  static editorTag = "";

  static async getConfigElement(this: {
    editorTag: string;
  }): Promise<HTMLElement> {
    return document.createElement(this.editorTag);
  }

  static override properties = {
    hass: { attribute: false },
    config: { attribute: false },
  };

  declare hass?: HomeAssistant;
  declare config: CardConfig;

  constructor() {
    super();
    this.config = { type: "" };
  }

  override willUpdate(changedProperties: PropertyValues<this>): void {
    super.willUpdate(changedProperties);
    if (changedProperties.has("config")) {
      if (this.config.embedded) {
        this.setAttribute("embedded", "");
      } else {
        this.removeAttribute("embedded");
      }
    }
  }

  setConfig(config: CardConfig): void {
    if (!config || typeof config.type !== "string") {
      throw new Error("Invalid card configuration");
    }
    this.config = { ...config };
    if (this.config.embedded) {
      this.setAttribute("embedded", "");
    } else {
      this.removeAttribute("embedded");
    }
  }

  getCardSize(): number {
    return 3;
  }

  getGridOptions(): { columns: number; rows: number; min_columns?: number; min_rows?: number } {
    return { columns: 3, rows: 2, min_columns: 2, min_rows: 2 };
  }

  /** Get all Vault devices registered in Home Assistant */
  protected getVaultDevices(): DeviceRegistryEntry[] {
    if (!this.hass?.devices) return [];
    return Object.values(this.hass.devices).filter((device) =>
      device.identifiers?.some(([domain]) => domain === "vault")
    );
  }

  /** Resolve active Vault device based on card config or default */
  protected getActiveDevice(): DeviceRegistryEntry | undefined {
    const devices = this.getVaultDevices();
    if (devices.length === 0) return undefined;

    if (this.config.server) {
      const match = devices.find(
        (d) =>
          d.id === this.config.server ||
          d.name?.toLowerCase() === this.config.server?.toLowerCase() ||
          d.name_by_user?.toLowerCase() === this.config.server?.toLowerCase()
      );
      if (match) return match;
    }
    return devices[0];
  }

  /** Find an entity by translation key or entity_id suffix */
  protected getEntity(
    keyOrSuffix: string,
    domain = "sensor"
  ): HassEntity | undefined {
    if (!this.hass?.states) return undefined;
    const device = this.getActiveDevice();
    const deviceId = device?.id;

    // Search registry first if device is resolved
    if (deviceId && this.hass.entities) {
      const regMatches = Object.values(this.hass.entities).filter(
        (entry) =>
          entry.device_id === deviceId &&
          entry.entity_id.startsWith(`${domain}.`) &&
          (entry.translation_key === keyOrSuffix ||
            entry.entity_id.endsWith(`_${keyOrSuffix}`) ||
            entry.entity_id === `${domain}.${keyOrSuffix}`)
      );
      if (regMatches.length > 0 && regMatches[0]?.entity_id) {
        const entity = this.hass.states[regMatches[0].entity_id];
        if (entity) return entity;
      }
    }

    // First pass: exact entity ID matches
    for (const [entityId, entity] of Object.entries(this.hass.states)) {
      if (!entityId.startsWith(`${domain}.`)) continue;
      if (this.hass.entities) {
        const reg = this.hass.entities[entityId];
        if (reg) {
          if (deviceId && reg.device_id && reg.device_id !== deviceId) continue;
          if (reg.platform && reg.platform !== "vault") continue;
        }
      }
      if (
        entityId === `${domain}.vault_${keyOrSuffix}` ||
        entityId === `${domain}.${keyOrSuffix}` ||
        entityId === `${domain}.vault_backup_${keyOrSuffix}`
      ) {
        return entity;
      }
    }

    // Second pass: exact suffix matches
    for (const [entityId, entity] of Object.entries(this.hass.states)) {
      if (!entityId.startsWith(`${domain}.`)) continue;
      if (this.hass.entities) {
        const reg = this.hass.entities[entityId];
        if (reg) {
          if (deviceId && reg.device_id && reg.device_id !== deviceId) continue;
          if (reg.platform && reg.platform !== "vault") continue;
        }
      }
      if (entityId.endsWith(`_${keyOrSuffix}`)) {
        return entity;
      }
    }
    return undefined;
  }

  /** Find all entities matching a pattern/prefix scoped to active Vault device */
  protected getEntities(
    keyPrefix: string,
    domain = "sensor"
  ): HassEntity[] {
    if (!this.hass?.states) return [];
    const results: HassEntity[] = [];
    const device = this.getActiveDevice();
    const deviceId = device?.id;

    for (const [entityId, entity] of Object.entries(this.hass.states)) {
      if (!entityId.startsWith(`${domain}.`)) continue;
      if (this.hass.entities) {
        const reg = this.hass.entities[entityId];
        if (!reg || reg.platform !== "vault") continue;
        if (deviceId && reg.device_id && reg.device_id !== deviceId) continue;
      } else if (!entityId.startsWith(`${domain}.vault_`) && !entityId.includes("vault")) {
        continue;
      }
      const objectId = entityId.slice(domain.length + 1);
      const matchesKey =
        objectId === keyPrefix ||
        objectId.startsWith(`${keyPrefix}_`) ||
        objectId.startsWith(`vault_${keyPrefix}_`) ||
        objectId.endsWith(`_${keyPrefix}`) ||
        objectId.includes(`_${keyPrefix}_`);
      if (matchesKey) {
        results.push(entity);
      }
    }
    return results;
  }

  /** Format bytes to human readable string (MB/GB/TB) */
  protected formatBytes(bytes: number | string | undefined | null): string {
    const n = Number(bytes);
    if (isNaN(n) || n <= 0) return "--";
    if (n >= 1e12) return `${(n / 1e12).toFixed(1)} TB`;
    if (n >= 1e9) return `${(n / 1e9).toFixed(1)} GB`;
    if (n >= 1e6) return `${(n / 1e6).toFixed(1)} MB`;
    if (n >= 1e3) return `${(n / 1e3).toFixed(1)} KB`;
    return `${n} B`;
  }

  /** Format duration in seconds to human readable string */
  protected formatDuration(seconds: number | string | undefined | null): string {
    const s = Number(seconds);
    if (isNaN(s) || s < 0) return "--";
    if (s < 60) return `${Math.round(s)}s`;
    const m = Math.floor(s / 60);
    const remS = Math.round(s % 60);
    if (m < 60) return remS ? `${m}m ${remS}s` : `${m}m`;
    const h = Math.floor(m / 60);
    const remM = m % 60;
    return remM ? `${h}h ${remM}m` : `${h}h`;
  }

  /** Format ISO date string or timestamp to relative or localized time */
  protected formatTimeAgo(isoOrTimestamp: string | number | undefined | null): string {
    if (!isoOrTimestamp) return "--";
    try {
      const date = new Date(isoOrTimestamp);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const isFuture = diffMs < 0;
      const absDiffSec = Math.floor(Math.abs(diffMs) / 1000);

      if (absDiffSec < 60) return isFuture ? "in < 1m" : "just now";
      if (absDiffSec < 3600) {
        const m = Math.floor(absDiffSec / 60);
        return isFuture ? `in ${m}m` : `${m}m ago`;
      }
      if (absDiffSec < 86400) {
        const h = Math.floor(absDiffSec / 3600);
        return isFuture ? `in ${h}h` : `${h}h ago`;
      }
      const d = Math.floor(absDiffSec / 86400);
      return isFuture ? `in ${d}d` : `${d}d ago`;
    } catch {
      return String(isoOrTimestamp);
    }
  }

  /** Call a Home Assistant service/action safely */
  protected async callAction(
    domain: string,
    action: string,
    data: Record<string, unknown> = {}
  ): Promise<void> {
    if (!this.hass) return;
    try {
      await this.hass.callService(domain, action, data);
    } catch (err) {
      console.error(`Failed to call ${domain}.${action}:`, err);
      throw err;
    }
  }
}
