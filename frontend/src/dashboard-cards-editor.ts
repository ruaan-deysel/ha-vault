import { LitElement, css, html, type TemplateResult } from "lit";
import { type CardConfig } from "./config";
import { fireEvent, type HomeAssistant } from "./ha-types";

export class VaultCardEditor extends LitElement {
  static override properties = {
    hass: { attribute: false },
    _config: { state: true },
  };

  declare hass?: HomeAssistant;
  declare _config?: CardConfig;

  static override styles = css`
    .card-config {
      display: flex;
      flex-direction: column;
      gap: 14px;
      padding: 8px 0;
      color: var(--primary-text-color, #fff);
      font-size: 0.9rem;
    }
    .form-row {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    label {
      font-size: 0.8rem;
      font-weight: 600;
      color: var(--secondary-text-color, #aaa);
    }
    input[type="text"],
    select {
      padding: 8px 12px;
      border-radius: 6px;
      border: 1px solid var(--divider-color, rgba(255, 255, 255, 0.15));
      background: var(--card-background-color, #18181b);
      color: var(--primary-text-color, #fff);
      font-size: 0.85rem;
    }
    .checkbox-row {
      display: flex;
      align-items: center;
      gap: 10px;
      cursor: pointer;
    }
    .checkbox-row input {
      width: 16px;
      height: 16px;
      accent-color: var(--primary-color, #f59e0b);
    }
  `;

  setConfig(config: CardConfig): void {
    this._config = { ...config };
  }

  private _valueChanged(key: string, value: unknown): void {
    if (!this._config) return;
    const newConfig = { ...this._config, [key]: value };
    this._config = newConfig;
    fireEvent(this, "config-changed", { config: newConfig });
  }

  protected override render(): TemplateResult {
    if (!this.hass || !this._config) return html``;

    const devices = Object.values(this.hass.devices || {}).filter((d) =>
      d.identifiers?.some(([domain]) => domain === "vault")
    );

    return html`
      <div class="card-config">
        <div class="form-row">
          <label>Title (Optional)</label>
          <input
            type="text"
            .value="${this._config.title || ""}"
            @input="${(e: Event) =>
              this._valueChanged(
                "title",
                (e.target as HTMLInputElement).value
              )}"
          />
        </div>

        ${devices.length > 1
          ? html`
              <div class="form-row">
                <label>Vault Server</label>
                <select
                  @change="${(e: Event) =>
                    this._valueChanged(
                      "server",
                      (e.target as HTMLSelectElement).value
                    )}"
                >
                  <option value="">Default (First detected)</option>
                  ${devices.map(
                    (d) => html`
                      <option
                        value="${d.id}"
                        ?selected="${this._config?.server === d.id}"
                      >
                        ${d.name_by_user || d.name || d.id}
                      </option>
                    `
                  )}
                </select>
              </div>
            `
          : ""}
      </div>
    `;
  }
}
