import { html, type TemplateResult } from "lit";
import { BaseVaultCard } from "./dashboard-cards-base";
import { VaultCardEditor } from "./dashboard-cards-editor";
import { RULES_CARD_TAG, RULES_EDITOR_TAG } from "./config";
import {
  iconTemplate,
  mdiCheckCircle,
  mdiFileDocumentOutline,
} from "./icons";
import { registerDashboardCard } from "./register-dashboard-card";

export class VaultRulesCard extends BaseVaultCard {
  static override editorTag = RULES_EDITOR_TAG;

  override getGridOptions() {
    return { columns: 6, rows: 2, min_columns: 3, min_rows: 2 };
  }

  protected override render(): TemplateResult {
    // Inspect real storage destinations and their types
    const storageEntities = this.getEntities("storage");
    const storageTypeSensors = storageEntities.filter((s) => s.entity_id.endsWith("_type"));

    // Extract unique storage destination tokens, excluding metric sensors
    const destTokens = new Set<string>();
    for (const s of storageEntities) {
      const id = s.entity_id;
      if (
        id.endsWith("_total_space") ||
        id.endsWith("_used_space") ||
        id.endsWith("_free_space") ||
        id.endsWith("_health") ||
        id.endsWith("_status")
      ) {
        continue;
      }
      const match = id.match(/storage_([a-z0-9_]+?)(?:_type|_path|$)/);
      if (match?.[1]) {
        destTokens.add(match[1]);
      } else {
        destTokens.add(id);
      }
    }

    const storageTypes = storageTypeSensors
      .map((s) => String(s.state || "").toLowerCase())
      .filter((t) => t && t !== "unavailable" && t !== "unknown");

    const hasOffsite = storageTypes.some((t) => ["s3", "sftp", "webdav", "smb", "nfs"].includes(t));
    const uniqueTypesCount = new Set(storageTypes).size;
    const hasMultipleMedia = uniqueTypesCount >= 2;
    const destCount = destTokens.size || storageTypeSensors.length;
    const hasThreeCopies = destCount >= 3;

    const isCompliant = hasThreeCopies && hasMultipleMedia && hasOffsite;

    return html`
      <ha-card>
        <div class="header">
          <div class="header-main">
            <div class="header-icon">
              ${iconTemplate(mdiFileDocumentOutline, 18)}
            </div>
            <div class="header-titles">
              <span class="header-tag">3-2-1 Backup Rule</span>
              ${this.config.title ? html`<span class="header-title">${this.config.title}</span>` : ""}
            </div>
          </div>
          <div class="badge ${isCompliant ? "success" : "neutral"}">
            ${isCompliant ? "Compliant" : "3-2-1 Status"}
          </div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-top: 6px;">
          <div style="background: var(--vault-surface); padding: 8px 10px; border-radius: 6px; border: 1px solid var(--vault-border); display: flex; align-items: center; gap: 8px;">
            <div style="color: ${hasThreeCopies ? "var(--vault-success)" : "var(--vault-standby)"};">
              ${iconTemplate(mdiCheckCircle, 16)}
            </div>
            <div style="display: flex; flex-direction: column;">
              <span style="font-size: 0.75rem; font-weight: 700; color: var(--vault-text);">3 Copies</span>
              <span style="font-size: 0.7rem; color: var(--vault-subtext);">${hasThreeCopies ? "Target Verified" : `${destCount} Configured`}</span>
            </div>
          </div>

          <div style="background: var(--vault-surface); padding: 8px 10px; border-radius: 6px; border: 1px solid var(--vault-border); display: flex; align-items: center; gap: 8px;">
            <div style="color: ${hasMultipleMedia ? "var(--vault-success)" : "var(--vault-standby)"};">
              ${iconTemplate(mdiCheckCircle, 16)}
            </div>
            <div style="display: flex; flex-direction: column;">
              <span style="font-size: 0.75rem; font-weight: 700; color: var(--vault-text);">2 Media</span>
              <span style="font-size: 0.7rem; color: var(--vault-subtext);">${hasMultipleMedia ? `${uniqueTypesCount} Media Types` : "Single Media"}</span>
            </div>
          </div>

          <div style="background: var(--vault-surface); padding: 8px 10px; border-radius: 6px; border: 1px solid var(--vault-border); display: flex; align-items: center; gap: 8px;">
            <div style="color: ${hasOffsite ? "var(--vault-success)" : "var(--vault-standby)"};">
              ${iconTemplate(mdiCheckCircle, 16)}
            </div>
            <div style="display: flex; flex-direction: column;">
              <span style="font-size: 0.75rem; font-weight: 700; color: var(--vault-text);">1 Offsite</span>
              <span style="font-size: 0.7rem; color: var(--vault-subtext);">${hasOffsite ? "Remote Target" : "Local Only"}</span>
            </div>
          </div>
        </div>
      </ha-card>
    `;
  }
}

export class VaultRulesCardEditor extends VaultCardEditor {}

registerDashboardCard({
  tag: RULES_CARD_TAG,
  editorTag: RULES_EDITOR_TAG,
  card: VaultRulesCard,
  editor: VaultRulesCardEditor,
  name: "Vault 3-2-1 Rule",
  description: "Display 3-2-1 backup compliance checklist",
});
